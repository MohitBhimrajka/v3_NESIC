# pdf_generator.py

import os
from pathlib import Path
import markdown
from markdown.extensions import fenced_code, tables, toc, attr_list, def_list, footnotes
from markdown.extensions.codehilite import CodeHiliteExtension
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
import yaml
import html
# --- Corrected/Added BS4 Imports ---
from bs4 import BeautifulSoup, Comment
from bs4.element import Tag # <-- CORRECT IMPORT ADDED
# --- End BS4 Imports ---
import re
from typing import Optional, Dict, List, Tuple, Any, Union
from config import SECTION_ORDER, PDF_CONFIG # Assuming PDF_CONFIG is still used, though not shown in direct graph logic
from pydantic import BaseModel
import logging # Added for logging graph errors

# --- Added Imports for Graph Generation ---
import matplotlib # Must be imported before pyplot
matplotlib.use('Agg') # Use non-interactive backend suitable for servers
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import json
import numpy as np
import string
import colorsys # For generating distinct colors automatically
import hashlib # For creating unique filenames for graphs
from io import BytesIO # For potential in-memory handling if needed, though saving is preferred
# --- End Added Imports ---

# Setup logger for pdf_generator module
logger = logging.getLogger(__name__)
# Ensure logger propagates messages if root logger is configured elsewhere
logger.propagate = True
# Set a default level if no other configuration is found
if not logger.hasHandlers():
    logger.setLevel(logging.WARNING)
    # Add a basic handler if needed, though test_agent_prompt.py likely configures the root logger
    # handler = logging.StreamHandler()
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # handler.setFormatter(formatter)
    # logger.addHandler(handler)


class PDFSection(BaseModel):
    """Model for a section in the PDF."""
    id: str
    title: str
    content: str # Raw Markdown content
    html_content: str = "" # Processed HTML content
    intro: str = ""
    key_topics: List[str] = []
    metadata: Dict = {} # YAML frontmatter metadata
    reading_time: int = 0 # Estimated reading time in minutes
    subsections: List[Any] = [] # Subsections of this section


class EnhancedPDFGenerator:
    """Enhanced PDF Generator with better markdown support, styling, and graph rendering."""

    def __init__(self, template_path: Optional[str] = None):
        """Initialize the PDF generator with an optional custom template path."""
        if template_path:
            self.template_dir = str(Path(template_path).parent)
            self.template_name = Path(template_path).name
        else:
            self.template_dir = str(Path(__file__).parent / 'templates')
            self.template_name = 'enhanced_report_template.html'

        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        try:
            self.template = self.env.get_template(self.template_name)
        except Exception as e:
            logger.error(f"Failed to load template {self.template_name} from {self.template_dir}: {e}")
            raise # Re-raise the error as it's critical

        # Keep the original markdown instance for non-graph parts if needed
        self.md_basic = self._create_markdown_processor()

    def _create_markdown_processor(self):
        """Create a markdown processor with all necessary extensions."""
        # Standard markdown extensions used elsewhere
        extensions = [
            'extra', 'meta', 'codehilite', 'admonition', 'attr_list', 'toc',
            'def_list', 'footnotes', 'abbr', 'md_in_html', 'sane_lists', 'nl2br'
        ]
        extension_configs = {
            'codehilite': {'css_class': 'highlight', 'guess_lang': False},
            'toc': {'permalink': False},
            'footnotes': {'BACKLINK_TEXT': '↩'}
        }
        try:
            return markdown.Markdown(extensions=extensions, extension_configs=extension_configs)
        except Exception as e:
            logger.error(f"Failed to initialize Markdown processor: {e}")
            raise # Critical error

    # --- YAML and Content Processing Methods ---
    def _extract_section_metadata(self, content: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter and content from a markdown section."""
        metadata = {}
        content_no_leading_whitespace = content.lstrip()
        # Check if content starts with '---' followed by a newline character
        if content_no_leading_whitespace.startswith('---') and '\n' in content_no_leading_whitespace:
            try:
                # Split carefully, expecting '---', yaml block, '---', content
                parts = content_no_leading_whitespace.split('---', 2)
                if len(parts) >= 3 and parts[1].strip(): # Ensure the frontmatter part is not empty
                    frontmatter = parts[1]
                    markdown_content = parts[2] # The rest of the content after the second '---'
                    loaded_meta = yaml.safe_load(frontmatter)
                    # Ensure it's a dict, handle empty frontmatter gracefully
                    metadata = loaded_meta if isinstance(loaded_meta, dict) else {}
                    return metadata, markdown_content.strip()
                else:
                    # If split doesn't yield 3 parts or frontmatter is empty, treat as normal content
                    logger.debug("Could not find valid YAML frontmatter structure.")
                    return metadata, content.strip() # Return original content if parsing fails
            except (yaml.YAMLError, IndexError, ValueError) as e:
                logger.warning(f"Failed to parse YAML frontmatter: {e}. Treating as content.")
                # Fall through to return original content if YAML is invalid
                pass
        # If it doesn't start with '---' or parsing failed
        return metadata, content.strip()

    def _estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in minutes based on word count."""
        # Simple word count - consider removing HTML tags first for more accuracy if needed
        plain_text = re.sub('<[^<]+?>', '', content) # Basic tag removal
        words = len(plain_text.split())
        words_per_minute = 250 # Adjusted for potentially technical content
        estimated_time = max(1, round(words / words_per_minute)) # Ensure at least 1 minute
        # Capping at a reasonable max, e.g., 10 minutes per section
        return min(10, estimated_time)


    def _extract_key_topics(self, content: str, max_topics: int = 5) -> List[str]:
        """Extract key topics (H2, H3 headings) from the markdown content."""
        # Need to convert to HTML first to reliably find headings
        try:
            temp_html = self._create_markdown_processor().convert(content)
            soup = BeautifulSoup(temp_html, 'html.parser')
        except Exception as e:
            logger.error(f"Error converting markdown for key topic extraction: {e}")
            return ["Content Overview"] # Fallback

        headings = soup.find_all(['h2', 'h3'])
        topics = []
        # Try to skip the first H2 if it looks like the main section title
        starting_index = 0
        if headings and headings[0].name == 'h2':
            # A more robust check might compare against the expected section title if available
            starting_index = 1

        for heading in headings[starting_index:]:
            text = heading.get_text(strip=True) # Get text and strip whitespace
            # Remove potential numbering like "1. ", "1.1. "
            clean_text = re.sub(r'^\d+(\.\d+)*\.*\s+', '', text).strip()
            if clean_text: # Ensure we don't add empty topics
                topics.append(clean_text)
            if max_topics and len(topics) >= max_topics:
                break

        # If no topics found, provide a default
        if not topics:
            return ["Detailed Analysis"]
        return topics

    def _extract_intro(self, content: str) -> str:
        """Extract the introduction paragraph(s) from the markdown content."""
        lines = content.strip().split('\n')
        intro_lines = []
        i = 0

        # Skip potential frontmatter remnants, metadata lines, or initial blank lines more robustly
        while i < len(lines):
            line_strip = lines[i].strip()
            if not line_strip or line_strip == '---': # Skip blank lines and separators
                i += 1
                continue
            # Basic check for key: value structure, common in metadata
            if ':' in line_strip and len(line_strip.split(':')[0]) < 30: # Avoid removing lines with colons in sentences
                 i+= 1
                 continue
            break # Stop skipping once we hit potential content

        # Skip initial headers (H1-H6)
        while i < len(lines) and lines[i].strip().startswith('#'):
             i += 1

        # Collect contiguous non-empty, non-header lines until a significant break or header
        start_intro_index = i
        while i < len(lines):
            line_strip = lines[i].strip()
            if line_strip.startswith('#'): # Stop at any header
                 break
            # Stop if we hit more than one consecutive blank line (often indicates end of intro)
            if not line_strip and i > start_intro_index and i + 1 < len(lines) and not lines[i+1].strip():
                break
            # Include the line (even if blank, to preserve paragraph breaks within intro)
            intro_lines.append(lines[i])
            i += 1

        # Join collected lines and trim leading/trailing whitespace from the whole block
        intro_content = '\n'.join(intro_lines).strip()

        if not intro_content:
            # Fallback if no intro could be reliably extracted
            return "<p>This section contains detailed analysis and insights regarding the main topic.</p>"

        # Use the full markdown processor to render the intro correctly
        try:
            md_processor = self._create_markdown_processor()
            # Resetting the processor might be necessary if it maintains state across calls
            md_processor.reset()
            intro_html = md_processor.convert(intro_content)
            # Wrap in a div for potential styling
            return f'<div class="section-intro">{intro_html}</div>' if intro_html else "<p>Overview of the section's content.</p>"
        except Exception as e:
            logger.error(f"Error converting intro markdown to HTML: {e}")
            return "<p>Error displaying introduction.</p>"


    # --- Graph Generation Methods (Phase 2 - Complete) ---

    def _extract_graph_json(self, content: str) -> List[Tuple[Dict, str]]:
        """Extract valid graph JSON blocks and their original text from markdown."""
        graph_pattern = r'<GRAPH_JSON>(.*?)</GRAPH_JSON>'
        # Using re.DOTALL to match across newlines, re.IGNORECASE might be useful too
        matches = re.finditer(graph_pattern, content, re.DOTALL | re.IGNORECASE)
        valid_graphs = []

        for match in matches:
            json_string = match.group(1).strip()
            original_block = match.group(0) # Keep the full matched block <GRAPH_JSON>...</GRAPH_JSON>
            try:
                # Basic attempt to fix trailing commas before parsing
                json_string = re.sub(r',\s*([\}\]])', r'\1', json_string)

                graph_data = json.loads(json_string)
                if isinstance(graph_data, dict) and self._validate_graph_data(graph_data):
                    valid_graphs.append((graph_data, original_block))
                else:
                    logger.warning(f"Skipping graph: Validation failed for '{graph_data.get('title', 'Untitled')}'")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse graph JSON: {e}. Content snippet: {json_string[:200]}...")
            except Exception as e:
                logger.error(f"Unexpected error processing graph JSON: {e}")

        return valid_graphs

    def _validate_graph_data(self, graph_data: Dict) -> bool:
        """Validate that the graph JSON has minimally required and plausible data."""
        if not isinstance(graph_data, dict):
            logger.debug("Graph validation failed: Input is not a dictionary.")
            return False
        if 'type' not in graph_data or not isinstance(graph_data['type'], str) or not graph_data['type']:
            logger.debug("Graph validation failed: Missing or invalid 'type'.")
            return False
        if 'data' not in graph_data or not isinstance(graph_data['data'], dict):
            logger.debug("Graph validation failed: Missing or invalid 'data' object.")
            return False

        data = graph_data['data']
        # Labels are crucial for most chart types
        labels_present = 'labels' in data and isinstance(data['labels'], list) and data['labels']
        if not labels_present and graph_data['type'].lower() not in ['scatter', 'bubble']:
            logger.debug("Graph validation failed: Missing or empty 'labels' array required for this chart type.")
            return False

        if 'datasets' not in data or not isinstance(data['datasets'], list) or not data['datasets']:
            logger.debug("Graph validation failed: Missing or empty 'datasets' array.")
            return False

        num_labels = len(data['labels']) if labels_present else 0

        for i, dataset in enumerate(data['datasets']):
            if not isinstance(dataset, dict):
                logger.debug(f"Graph validation failed: Dataset {i} is not a dictionary.")
                return False
            if 'data' not in dataset or not isinstance(dataset['data'], list) or not dataset['data']:
                logger.debug(f"Graph validation failed: Dataset {i} has missing or empty 'data' array.")
                return False

            # Check for common LLM placeholder patterns in data
            values = dataset['data']
            if any(isinstance(v, str) and v.lower().startswith(('value', '[value', 'insert', 'replace', 'num_', 'placeholder')) for v in values):
                logger.debug(f"Graph validation failed: Dataset {i} contains placeholder string values.")
                return False

            # Check for length mismatch (important!) - except for pie/doughnut which use labels for slices
            if graph_data['type'].lower() not in ['pie', 'doughnut'] and labels_present and len(values) != num_labels:
                 # Allow if labels were initially empty and length is consistent across datasets (e.g. scatter)
                 is_first_dataset = (i == 0)
                 if not is_first_dataset:
                     prev_dataset_len = len(data['datasets'][0].get('data', []))
                     if len(values) != prev_dataset_len:
                         logger.debug(f"Graph validation failed: Dataset {i} data length ({len(values)}) mismatch with previous dataset ({prev_dataset_len}).")
                         return False
                 elif num_labels != 0: # If labels *are* present, length must match on first dataset too
                     logger.debug(f"Graph validation failed: Dataset {i} data length ({len(values)}) mismatch with labels length ({num_labels}).")
                     return False

            # Attempt numeric conversion and check if all are zero (warning, not failure)
            try:
                 # More robust check for numbers, including negative
                 numeric_values = [float(v) for v in values if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).replace('-', '', 1).isdigit())]
                 if numeric_values and all(abs(v) < 1e-9 for v in numeric_values): # Use tolerance for float comparison
                      logger.warning(f"Graph validation: Dataset {i} in '{graph_data.get('title', 'Untitled')}' contains only zero values. Proceeding, but may indicate missing data.")
            except (ValueError, TypeError) as e:
                 # If conversion fails for any item, it might be intentional (e.g., categorical data) or an error
                 logger.debug(f"Non-numeric data found in dataset {i} while checking for zeros: {e}. Proceeding.")
                 pass # Don't fail validation just because of non-numeric items here

        return True # Passed all checks

    def _generate_colors(self, num_colors: int) -> List[str]:
        """Generates a list of visually distinct hex colors using HSV space."""
        if num_colors <= 0: return []
        colors = []
        # Use golden ratio partitioning of hue space for better distinction
        golden_ratio_conjugate = 0.618033988749895
        hue = np.random.rand() # Random start hue
        saturation = 0.65 # Keep saturation reasonable
        value = 0.85 # Keep value reasonable

        for i in range(num_colors):
            hue = (hue + golden_ratio_conjugate) % 1.0
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            # Ensure conversion to int is safe and within 0-255 range
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(max(0, min(255, rgb[0]*255))),
                int(max(0, min(255, rgb[1]*255))),
                int(max(0, min(255, rgb[2]*255)))
            )
            colors.append(hex_color)
        return colors

    def _safely_convert_to_float(self, value: Any, default: float = 0.0) -> float:
        """Attempts to convert a value to float, returning default on failure."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                # Handle common currency/percentage symbols if needed
                cleaned_value = value.replace(',', '').replace('¥', '').replace('$', '').replace('%', '').strip()
                if cleaned_value: # Check if not empty after cleaning
                    # Handle potential negative numbers correctly
                    return float(cleaned_value)
            except (ValueError, TypeError):
                pass # Conversion failed
        # If it's None or conversion failed, return default
        return default

    def _render_graph(self, graph_data: Dict, output_path: Path) -> Optional[Path]:
        """Renders a graph using Matplotlib based on JSON data and saves it."""
        fig = None # Ensure fig is defined for finally block
        try:
            graph_type = graph_data.get('type', 'bar').lower()
            data = graph_data.get('data', {})
            options = graph_data.get('options', {})
            labels = data.get('labels', [])
            datasets = data.get('datasets', [])

            # Initial figure setup - potentially adjust size based on type/labels
            figsize = (8, 5) # Default
            if len(labels) > 10 and graph_type not in ['pie', 'doughnut', 'radar']: figsize = (10, 6) # Wider for many labels
            if graph_type == 'horizontalbar' and len(labels) > 8: figsize = (8, max(6, len(labels) * 0.6)) # Taller for horizontal bars

            fig, ax = plt.subplots(figsize=figsize, dpi=150)

            # Determine number of colors needed
            num_datasets = len(datasets)
            num_labels_or_points = len(labels) if labels else (len(datasets[0]['data']) if datasets and datasets[0].get('data') else 0)

            # Get default colors - generate enough for datasets or labels (for pie)
            default_colors = self._generate_colors(max(num_datasets, num_labels_or_points, 1))

            # --- Plotting Logic ---
            if graph_type in ['bar', 'horizontalbar']:
                # Ensure labels is a list of strings
                str_labels = [str(lbl) for lbl in labels]
                bar_width = 0.8 / num_datasets
                indices = np.arange(len(str_labels))

                for i, dataset in enumerate(datasets):
                    dataset_data = [self._safely_convert_to_float(d) for d in dataset.get('data', [])]
                    color = dataset.get('backgroundColor', default_colors[i % len(default_colors)])
                    border_color = dataset.get('borderColor', color) # Use background if no border specified
                    bar_positions = indices + (i - (num_datasets - 1) / 2) * bar_width

                    plot_args = {
                        "label": dataset.get('label'),
                        "color": color,
                        "edgecolor": border_color,
                        "linewidth": dataset.get('borderWidth', 0.5) # Thinner default border
                    }

                    if graph_type == 'bar':
                        ax.bar(bar_positions, dataset_data, bar_width, **plot_args)
                    else: # horizontalBar
                        ax.barh(bar_positions, dataset_data, bar_width, **plot_args)

                if graph_type == 'bar':
                    ax.set_xticks(indices)
                    ax.set_xticklabels(str_labels, rotation=30, ha='right', fontsize='small')
                else:
                    ax.set_yticks(indices)
                    ax.set_yticklabels(str_labels, fontsize='small')
                    ax.invert_yaxis()

            elif graph_type == 'line':
                str_labels = [str(lbl) for lbl in labels]
                for i, dataset in enumerate(datasets):
                    # Use NaN for gaps where conversion fails
                    dataset_data = [self._safely_convert_to_float(d, default=np.nan) for d in dataset.get('data', [])]
                    color = dataset.get('borderColor', default_colors[i % len(default_colors)])
                    bg_color = dataset.get('backgroundColor', 'none') # For fill
                    fill = dataset.get('fill', False)

                    ax.plot(str_labels, dataset_data, label=dataset.get('label'), color=color,
                            marker='o', markersize=4, linestyle='-', linewidth=dataset.get('borderWidth', 1.5))
                    if fill and bg_color != 'none':
                        # Ensure data doesn't contain NaNs before filling
                        valid_indices = ~np.isnan(dataset_data)
                        if np.any(valid_indices):
                             ax.fill_between(np.array(str_labels)[valid_indices], np.array(dataset_data)[valid_indices], color=bg_color, alpha=0.2)

                plt.xticks(rotation=30, ha='right', fontsize='small')

            elif graph_type in ['pie', 'doughnut']:
                if datasets and datasets[0].get('data'):
                    first_dataset = datasets[0]
                    # Safely convert data, filter out zeros/negatives/non-numeric for pie chart
                    raw_data = first_dataset.get('data', [])
                    numeric_data = [(str(labels[i]), self._safely_convert_to_float(raw_data[i], default=0.0)) for i in range(len(raw_data)) if i < len(labels)]
                    filtered_data = [(label, value) for label, value in numeric_data if value > 1e-9] # Use tolerance

                    if not filtered_data: # Handle case where all data is effectively zero or negative
                        logger.warning(f"No positive data found for pie/doughnut chart '{graph_data.get('title', 'Untitled')}'")
                        plt.close(fig)
                        return None

                    final_labels, final_values = zip(*filtered_data)

                    pie_colors = first_dataset.get('backgroundColor')
                    # Ensure colors match the length of the filtered data
                    if not isinstance(pie_colors, list) or len(pie_colors) < len(final_values):
                         pie_colors = self._generate_colors(len(final_values))
                    else:
                         pie_colors = pie_colors[:len(final_values)] # Truncate if too long

                    wedges, texts, autotexts = ax.pie(final_values, labels=final_labels, colors=pie_colors,
                                                      autopct='%1.1f%%', startangle=90, pctdistance=0.85,
                                                      textprops={'fontsize': 'x-small'})
                    plt.setp(autotexts, size='x-small', weight="bold", color="white") # Make percentages bold/white

                    if graph_type == 'doughnut':
                        centre_circle = plt.Circle((0,0),0.70,fc='white')
                        fig.gca().add_artist(centre_circle)
                    ax.axis('equal')
                else:
                    logger.warning(f"Pie/Doughnut chart '{graph_data.get('title', 'Untitled')}' has no valid data in the first dataset.")
                    plt.close(fig)
                    return None

            # --- Radar Chart Implementation ---
            elif graph_type == 'radar':
                if not labels or not datasets:
                    logger.warning(f"Radar chart '{graph_data.get('title', 'Untitled')}' missing labels or datasets.")
                    plt.close(fig)
                    return None

                str_labels = [str(lbl) for lbl in labels]
                num_vars = len(str_labels)
                if num_vars < 3: # Radar needs at least 3 variables
                     logger.warning(f"Radar chart '{graph_data.get('title', 'Untitled')}' needs at least 3 labels.")
                     plt.close(fig)
                     return None

                angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
                angles += angles[:1] # Close the plot

                # Switch to polar projection
                ax.remove() # Remove the default axes
                ax = fig.add_subplot(111, polar=True)

                for i, dataset in enumerate(datasets):
                    dataset_data_raw = [self._safely_convert_to_float(d) for d in dataset.get('data', [])]
                    if len(dataset_data_raw) != num_vars:
                        logger.warning(f"Dataset {i} length mismatch ({len(dataset_data_raw)} vs {num_vars}) for radar chart '{graph_data.get('title', 'Untitled')}'. Skipping dataset.")
                        continue
                    dataset_data = dataset_data_raw + dataset_data_raw[:1] # Close the plot data

                    color = dataset.get('borderColor', default_colors[i % len(default_colors)])
                    fill_color = dataset.get('backgroundColor', color)
                    fill = dataset.get('fill', True)

                    ax.plot(angles, dataset_data, color=color, linewidth=dataset.get('borderWidth', 1.5), linestyle='solid', label=dataset.get('label'))
                    if fill:
                        ax.fill(angles, dataset_data, color=fill_color, alpha=0.25)

                ax.set_xticks(angles[:-1]) # Set angle ticks
                ax.set_xticklabels(str_labels) # Set labels for angles
                # Adjust radial ticks (y-axis for polar)
                ax.set_yticks(np.linspace(ax.get_ylim()[0], ax.get_ylim()[1], 5)) # Example: 5 ticks
                ax.tick_params(axis='y', labelsize='x-small') # Smaller radial labels
                ax.tick_params(axis='x', labelsize='small') # Variable labels

            else:
                logger.warning(f"Unsupported graph type encountered: {graph_type}. Skipping graph.")
                plt.close(fig)
                return None

            # --- Common Styling ---
            fig.suptitle(graph_data.get('title', ''), fontsize=14, weight='bold', y=1.02)

            # Apply common options only if the plot type allows axes
            if graph_type not in ['pie', 'doughnut']:
                y_axis_options = options.get('scales', {}).get('yAxes', [{}])[0]
                if y_axis_options.get('ticks', {}).get('beginAtZero', True): # Default True for bar/line unless specified otherwise
                    current_ylim = ax.get_ylim()
                    ax.set_ylim(bottom=min(0, current_ylim[0]), top=current_ylim[1]) # Ensure 0 is included if requested

                # Add basic axis labels if provided
                y_scale_label = y_axis_options.get('scaleLabel', {})
                if y_scale_label.get('display', False) and y_scale_label.get('labelString'):
                    ax.set_ylabel(y_scale_label['labelString'], fontsize='small')
                x_axis_options = options.get('scales', {}).get('xAxes', [{}])[0]
                x_scale_label = x_axis_options.get('scaleLabel', {})
                if x_scale_label.get('display', False) and x_scale_label.get('labelString'):
                    ax.set_xlabel(x_scale_label['labelString'], fontsize='small')

                ax.grid(True, axis='y', linestyle=':', linewidth=0.5, color='grey', alpha=0.6)

            # Add legend
            show_legend = options.get('legend', {}).get('display', True)
            # Check if there are actual labels to display in the legend
            has_labels_in_datasets = any(ds.get('label') for ds in datasets)
            if show_legend and has_labels_in_datasets:
                legend_pos_chartjs = options.get('legend', {}).get('position', 'top') # Default to top
                # Mapping, prioritize placement outside plot area
                mpl_legend_pos_map = {
                    'top': ('upper center', (0.5, 1.15)),
                    'bottom': ('lower center', (0.5, -0.25)),
                    'left': ('center left', (-0.2, 0.5)),
                    'right': ('center right', (1.2, 0.5)),
                    'best': ('best', None) # Let matplotlib decide inside
                }
                loc, bbox = mpl_legend_pos_map.get(legend_pos_chartjs, ('best', None))
                # Adjust ncol for horizontal legends
                ncol = min(3, num_datasets) if legend_pos_chartjs in ['top', 'bottom'] else 1
                ax.legend(loc=loc, bbox_to_anchor=bbox, ncol=ncol, fontsize='small', frameon=False)


            # Improve spacing, adjust rect based on legend position
            pad = 1.5
            rect = [0.05, 0.1, 0.95, 0.9] # Default rect [left, bottom, right, top]
            if legend_pos_chartjs == 'bottom': rect[1] = 0.20
            if legend_pos_chartjs == 'top': rect[3] = 0.85
            if legend_pos_chartjs == 'left': rect[0] = 0.20
            if legend_pos_chartjs == 'right': rect[2] = 0.80
            if graph_type == 'horizontalbar': rect[0] = 0.25 # Ensure space for y-labels

            plt.tight_layout(pad=pad, rect=rect)

            # --- Save Figure ---
            # Ensure directory exists right before saving
            output_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, format='png', bbox_inches='tight', dpi=fig.dpi)
            logger.info(f"Graph successfully rendered and saved to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error rendering graph '{graph_data.get('title', 'Untitled')}': {e}", exc_info=True)
            return None
        finally:
            # CRITICAL: Close the figure to release memory
            if fig:
                plt.close(fig)


    # --- HTML Generation and Integration Methods ---

    def _convert_markdown_to_html(self, markdown_content: str, base_output_dir: Path) -> str:
        """
        Convert markdown content to HTML, extracting, rendering, and embedding graphs.
        """
        logger.debug(f"Starting markdown conversion. Base dir: {base_output_dir}")
        graphs_dir = base_output_dir / 'graphs'
        try:
            os.makedirs(graphs_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Could not create graphs directory {graphs_dir}: {e}. Skipping graph rendering.")
            return self._create_markdown_processor().convert(markdown_content) # Fallback

        processed_content = markdown_content
        graph_replacements = [] # Store (start_index, end_index, replacement_html)

        graph_pattern = r'<GRAPH_JSON>(.*?)</GRAPH_JSON>'
        for match in re.finditer(graph_pattern, markdown_content, re.DOTALL | re.IGNORECASE):
             json_string = match.group(1).strip()
             original_block = match.group(0)
             graph_data = None
             is_valid = False
             replacement_html = f"<!-- Error processing graph block at index {match.start()} -->" # Default replacement

             try:
                 json_string = re.sub(r',\s*([\}\]])', r'\1', json_string) # Fix trailing commas
                 graph_data = json.loads(json_string)
                 is_valid = isinstance(graph_data, dict) and self._validate_graph_data(graph_data)
             except json.JSONDecodeError as e:
                 logger.error(f"Failed to parse graph JSON at index {match.start()}: {e}.")
                 replacement_html = f"<!-- Error parsing graph JSON at index {match.start()} -->"
             except Exception as e:
                 logger.error(f"Unexpected error validating graph JSON at index {match.start()}: {e}")
                 replacement_html = f"<!-- Error validating graph JSON at index {match.start()} -->"

             if is_valid and graph_data:
                 try:
                      # Generate a stable filename based on content hash for potential caching
                      graph_hash = hashlib.md5(json.dumps(graph_data, sort_keys=True).encode()).hexdigest()[:12]
                      graph_filename = f"graph_{graph_data.get('type','chart')}_{graph_hash}.png"
                      graph_save_path = graphs_dir / graph_filename
                      graph_title = graph_data.get('title', 'Chart')
                      graph_desc = graph_data.get('description', '').strip() or graph_title
                      graph_source = graph_data.get('source', 'Not specified').strip()
                      # Clean source text slightly for display, remove citation markers
                      graph_source_cleaned = re.sub(r'\s*\[SSX\]\s*', '', graph_source).strip()

                      # --- Render graph ---
                      rendered_path = self._render_graph(graph_data, graph_save_path)
                      # --- End Render ---

                      if rendered_path:
                           # Use relative path for HTML src attribute, ensure forward slashes
                           graph_relative_path = Path('graphs') / graph_filename
                           html_src = str(graph_relative_path).replace('\\', '/')

                           # Generate HTML figure tag - escape attributes for safety
                           safe_alt = html.escape(graph_desc)
                           safe_caption = html.escape(graph_desc)
                           safe_source = html.escape(graph_source_cleaned)
                           safe_type = html.escape(graph_data.get('type','unknown'))

                           replacement_html = f"""
<figure class="graph-figure" data-graph-type="{safe_type}">
    <img src="{html.escape(html_src)}" alt="{safe_alt}" class="graph-image">
    <figcaption>{safe_caption}</figcaption>
    <p class="graph-source">Source: {safe_source}</p>
</figure>
"""
                           logger.info(f"Successfully prepared graph for embedding: {graph_title}")
                      else:
                           replacement_html = f"<!-- Graph rendering failed for: {html.escape(graph_title)} -->"
                           logger.warning(f"Graph rendering failed for '{graph_title}' at index {match.start()}, removing block.")
                 except Exception as e:
                      logger.error(f"Error during graph filename generation or HTML creation at index {match.start()}: {e}")
                      replacement_html = f"<!-- Error creating HTML for graph block at index {match.start()} -->"
             else:
                  # Invalid JSON or failed validation
                  if graph_data: # Log title if parsing worked but validation failed
                      logger.warning(f"Invalid/incomplete graph data for '{graph_data.get('title', 'Untitled')}' at index {match.start()}, removing block.")
                  else: # Parsing failed
                      logger.warning(f"Invalid JSON for graph at index {match.start()}, removing block.")
                  replacement_html = f"<!-- Invalid or incomplete graph data removed at index {match.start()} -->"


             graph_replacements.append({'start': match.start(), 'end': match.end(), 'html': replacement_html})


        # Apply replacements to the original markdown content - Efficiently
        if graph_replacements:
             parts = []
             last_end = 0
             for rep in sorted(graph_replacements, key=lambda x: x['start']):
                 parts.append(markdown_content[last_end:rep['start']]) # Add text before match
                 parts.append(rep['html']) # Add replacement HTML
                 last_end = rep['end']
             parts.append(markdown_content[last_end:]) # Add any remaining text
             processed_content = "".join(parts)


        # Convert the potentially modified Markdown (with graphs replaced by HTML figures) to HTML
        try:
            md_processor = self._create_markdown_processor()
            md_processor.reset()
            html_output = md_processor.convert(processed_content)
        except Exception as e:
            logger.error(f"Error during final Markdown to HTML conversion: {e}", exc_info=True)
            html_output = self._create_markdown_processor().convert(markdown_content) # Fallback
            html_output += "\n<p><em>Note: An error occurred during advanced content processing (e.g., graphs).</em></p>"

        # Post-process the generated HTML (tables, lists, headings etc.)
        try:
            soup = BeautifulSoup(html_output, 'html.parser')
            self._process_headings(soup)
            for list_root in soup.find_all(['ul', 'ol'], recursive=False):
                self._process_list(list_root, soup=soup)
            self._enhance_tables(soup)
            self._enhance_definition_lists(soup)
            self._enhance_footnotes(soup)
            final_html = str(soup)
        except Exception as e:
            logger.error(f"Error during HTML post-processing (BeautifulSoup): {e}", exc_info=True)
            final_html = html_output # Return potentially un-enhanced HTML if soup fails

        logger.debug("Markdown conversion with graph processing complete.")
        return final_html

    # --- Existing HTML Post-Processing Helpers ---
    def _process_headings(self, soup: BeautifulSoup):
        """Add classes and stable IDs to headings H1-H6."""
        used_ids = set()
        for i, h_tag in enumerate(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])):
            h_tag['class'] = h_tag.get('class', []) + [f'heading-{h_tag.name}']
            current_id = h_tag.get('id')
            if not current_id or current_id in used_ids: # Regenerate if missing or duplicate
                base_text = h_tag.get_text(strip=True)
                slug = base_text.lower()
                slug = re.sub(r'[^\w\s-]', '', slug)
                slug = re.sub(r'[\s-]+', '-', slug).strip('-')
                final_id = slug if slug else f'heading-{i}'
                orig_final_id = final_id
                counter = 1
                while final_id in used_ids:
                    final_id = f"{orig_final_id}-{counter}"
                    counter += 1
                h_tag['id'] = final_id
            used_ids.add(h_tag['id'])

    # --- Corrected Type Hint Here ---
    def _process_list(self, list_tag: Tag, level: int = 1, soup: BeautifulSoup = None):
        """Recursively process lists (ul, ol) to add styling classes based on nesting level."""
        list_base_class = 'enhanced-list' if level == 1 else 'nested-list'
        item_base_class = 'enhanced-list-item' if level == 1 else 'nested-list-item'
        level_class = f'level-{level}'

        current_classes = list_tag.get('class', [])
        if list_base_class not in current_classes: current_classes.append(list_base_class)
        if level > 1 and level_class not in current_classes: current_classes.append(level_class)
        list_tag['class'] = current_classes

        for li in list_tag.find_all('li', recursive=False):
            item_classes = li.get('class', [])
            if item_base_class not in item_classes: item_classes.append(item_base_class)
            if level > 1 and level_class not in item_classes: item_classes.append(level_class)
            li['class'] = item_classes

            nested_lists = [child for child in li.children if isinstance(child, Tag) and child.name in ['ul', 'ol']]
            for nested_list in nested_lists:
                self._process_list(nested_list, level=level + 1, soup=soup)

    def _enhance_tables(self, soup: BeautifulSoup):
        """Apply enhanced styling classes and responsive wrappers to tables."""
        for table in soup.find_all('table'):
            if not table.find_parent('figure', class_='graph-figure'):
                if not table.parent or 'table-responsive' not in table.parent.get('class', []):
                     wrapper_div = soup.new_tag('div', attrs={'class': ['table-responsive']})
                     table.wrap(wrapper_div)

                current_classes = table.get('class', [])
                if 'enhanced-table' not in current_classes: current_classes.append('enhanced-table')
                if 'zebra-stripe' not in current_classes: current_classes.append('zebra-stripe')
                if table.find('thead') and 'has-header' not in current_classes:
                    current_classes.append('has-header')
                table['class'] = current_classes

                for td in table.find_all('td'):
                    td_classes = td.get('class', [])
                    if 'text-right' in td_classes or 'text-center' in td_classes or 'text-left' in td_classes: continue
                    text = td.get_text(strip=True)
                    if re.fullmatch(r'[-+]?([¥$€£]?\s?\d{1,3}(?:,\d{3})*(?:\.\d+)?%?|\d+\.?\d*%?)', text):
                         td['class'] = td_classes + ['text-right']

    def _enhance_definition_lists(self, soup: BeautifulSoup):
        """Apply styling classes to definition lists (dl), terms (dt), and definitions (dd)."""
        for dl in soup.find_all('dl'):
            current_classes = dl.get('class', [])
            if 'definition-list' not in current_classes: dl['class'] = current_classes + ['definition-list']
            for dt in dl.find_all('dt'):
                dt_classes = dt.get('class', [])
                if 'term' not in dt_classes: dt['class'] = dt_classes + ['term']
            for dd in dl.find_all('dd'):
                dd_classes = dd.get('class', [])
                if 'definition' not in dd_classes: dd['class'] = dd_classes + ['definition']

    def _enhance_footnotes(self, soup: BeautifulSoup):
        """Apply styling classes to the footnotes section generated by the markdown extension."""
        footnotes_div = soup.find('div', class_='footnote')
        if footnotes_div:
            current_classes = footnotes_div.get('class', [])
            if 'enhanced-footnotes' not in current_classes:
                 current_classes = [c for c in current_classes if c != 'footnote'] + ['enhanced-footnotes']
                 footnotes_div['class'] = current_classes

            prev_sib = footnotes_div.find_previous_sibling()
            has_title = False
            if prev_sib and prev_sib.name in ['h2', 'h3'] and 'footnote' in prev_sib.get_text(strip=True).lower():
                 has_title = True
            if not has_title and not soup.find('h3', class_='footnote-title'): # Add title if not present
                title_tag = soup.new_tag('h3', attrs={'class': ['footnote-title']})
                title_tag.string = "Footnotes"
                footnotes_div.insert_before(title_tag)

            for ol in footnotes_div.find_all('ol'):
                ol_classes = ol.get('class', [])
                if 'footnote-list' not in ol_classes: ol['class'] = ol_classes + ['footnote-list']
            for li in footnotes_div.find_all('li'):
                 li_classes = li.get('class', [])
                 if 'footnote-item' not in li_classes: li['class'] = li_classes + ['footnote-item']


    # --- PDF Generation Orchestration ---
    def _generate_toc(self, sections: List[PDFSection]) -> str:
        """Generate a properly formatted and hyperlinked table of contents HTML."""
        if not sections:
            logger.warning("No sections provided for Table of Contents generation.")
            return ""

        toc_html = '<div class="table-of-contents">\n'
        toc_html += '<div class="toc-container">\n<h2 class="toc-title">Table of Contents</h2>\n<div class="toc-entries">\n'
        for idx, section in enumerate(sections, 1):
            # Use the processed section ID which should be stable
            section_id = section.id # Use the ID assigned in _process_sections
            section_title = section.title.strip()
            toc_html += f'<div class="toc-entry">\n'
            # Ensure href links to the correct ID (needs html escaping for safety)
            toc_html += f'  <a href="#{html.escape(section_id)}" class="toc-link">{html.escape(section_title)}</a>\n'
            toc_html += '</div>\n'
        toc_html += '</div>\n</div>\n</div>\n'
        return toc_html


    def _process_sections(self, sections_data: List[PDFSection], base_output_dir: Path) -> List[PDFSection]:
        """Process sections: extract metadata, generate intro/topics, convert markdown (with graphs)."""
        processed_sections = []
        if not sections_data:
            logger.warning("No section data provided to _process_sections.")
            return []

        for section in sections_data:
            if not isinstance(section, PDFSection):
                logger.warning(f"Skipping invalid section data: {section}")
                continue

            logger.info(f"Processing section: {section.title} ({section.id})")
            # Ensure section ID is valid for HTML anchors/CSS selectors
            section.id = re.sub(r'[^\w-]', '', section.id.lower().replace(' ', '-')).strip('-') or f"section-{abs(hash(section.title))}"

            try:
                metadata, raw_content = self._extract_section_metadata(section.content)
                section.metadata.update(metadata)
            except Exception as e:
                 logger.error(f"Error extracting metadata for section {section.id}: {e}")
                 raw_content = section.content

            main_content = self._cleanup_raw_markdown(raw_content)

            if main_content:
                try:
                    section.intro = self._extract_intro(main_content)
                    section.key_topics = self._extract_key_topics(main_content)
                    section.reading_time = self._estimate_reading_time(main_content)
                except Exception as e:
                    logger.error(f"Error extracting derived info for section {section.id}: {e}")
                    section.intro = section.intro or "<p>Overview content for this section.</p>"
                    section.key_topics = section.key_topics or ["Section Details"]
                    section.reading_time = section.reading_time or 2

                try:
                    section.html_content = self._convert_markdown_to_html(main_content, base_output_dir)
                except Exception as e:
                    logger.error(f"Failed to convert markdown to HTML for section {section.id}: {e}", exc_info=True)
                    section.html_content = f"<p><strong>Error processing content for this section. Please check logs.</strong></p>"
            else:
                 logger.warning(f"Section {section.id} has no main content after cleanup.")
                 section.html_content = "<p>No content available for this section.</p>"

            processed_sections.append(section)

        logger.info(f"Finished processing {len(processed_sections)} sections.")
        return processed_sections


    def _cleanup_raw_markdown(self, content: str) -> str:
        """Clean up common LLM formatting issues like literal '\n', extra spaces, etc."""
        if not isinstance(content, str): return ""
        content = content.replace('\\n', '\n').replace('\\t', '\t')
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        content = content.strip()
        # Reduce multiple blank lines down to one, preserving intentional paragraph breaks
        content = re.sub(r'\n\s*\n', '\n\n', content)
        if content.startswith('\ufeff'): # Remove BOM
            content = content[1:]
        return content


    def generate_pdf(self, sections_data: List[PDFSection], output_pdf_path: str, metadata: Dict) -> Optional[Path]:
        """Generate a PDF report from the provided section data and metadata."""
        output_pdf_path = Path(output_pdf_path)
        base_output_dir = output_pdf_path.parent.parent
        if not base_output_dir.is_dir():
             logger.error(f"Calculated base output directory does not exist: {base_output_dir}. Cannot generate PDF.")
             return None

        logger.info(f"Starting PDF generation. Output Base Dir: {base_output_dir}, Target PDF Path: {output_pdf_path}")

        try:
            processed_sections = self._process_sections(sections_data, base_output_dir)
        except Exception as e:
            logger.error(f"Critical error during section processing: {e}", exc_info=True)
            return None

        template_dir_path = Path(self.template_dir)
        logo_rel_path = Path('assets') / 'supervity_logo.png'
        favicon_rel_path = Path('assets') / 'supervity_favicon.png'

        context = {
            'company_name': metadata.get('company', 'Company'),
            'language': metadata.get('language', 'English'),
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sections': processed_sections,
            'toc': self._generate_toc(processed_sections),
            'metadata': metadata,
            'logo_path': logo_rel_path.as_posix(),
            'favicon_path': favicon_rel_path.as_posix()
        }

        try:
            final_html_content = self.template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering Jinja2 template: {e}", exc_info=True)
            return None

        try:
            # Set base_url relative to where the HTML string is conceptually "located"
            # If assets/ and graphs/ are resolved relative to project root, use that
            project_root_path = Path(__file__).parent.parent
            render_base_url = project_root_path.as_uri() + "/"
            logger.info(f"Using WeasyPrint base_url: {render_base_url}")

            html = HTML(string=final_html_content, base_url=render_base_url)
            font_config = FontConfiguration()

            # --- COMPLETE CSS EMBEDDED ---
            company_name_for_css = html.escape(metadata.get('company', 'Report'))
            css_string = """
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Noto+Sans:wght@400;700&display=swap');

                @page {
                    size: A4;
                    margin: 2.5cm 2cm; /* Standard margins */
                    @bottom-right {
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 9pt;
                        color: #666;
                        vertical-align: top; /* Align page number better */
                        padding-top: 1cm;
                    }
                    @bottom-left {
                        content: "%s"; /* Company Name Placeholder */
                        font-size: 9pt;
                        color: #666;
                        vertical-align: top;
                        padding-top: 1cm;
                    }
                    @top-right {
                        content: "Made by Supervity";
                        font-size: 9pt;
                        color: #666;
                        vertical-align: bottom;
                        padding-bottom: 1cm;
                    }
                }
                @page cover { margin: 0; @bottom-right { content: normal; } @bottom-left { content: normal; } @top-right { content: normal; } }
                @page section_cover { margin: 0; @bottom-right { content: normal; } @bottom-left { content: normal; } @top-right { content: normal; } }
                @page toc {
                    @bottom-right { content: "Page " counter(page) " of " counter(pages); font-size: 9pt; color: #666; vertical-align: top; padding-top: 1cm; }
                    @bottom-left { content: "%s"; /* Company Name Placeholder */ font-size: 9pt; color: #666; vertical-align: top; padding-top: 1cm; }
                    @top-right { content: "Made by Supervity"; font-size: 9pt; color: #666; vertical-align: bottom; padding-bottom: 1cm; }
                }
                @page end { margin: 0; @bottom-right { content: normal; } @bottom-left { content: normal; } @top-right { content: normal; } @top-left { content: normal; } }

                :root {
                    --primary-black: #000000; --primary-white: #ffffff; --navy-blue: #000b37; --lime-green: #85c20b;
                    --dark-gray: #474747; --light-gray: #c7c7c7; --soft-blue: #8289ec; --light-lime: #c3fb54;
                    --coral-orange: #ff9a5a; --soft-purple: #b181ff; --bright-cyan: #31b8e1; --light-pink: #ff94a8;
                }
                body {
                    font-family: 'Noto Sans', 'Noto Sans JP', 'Helvetica Neue', 'Arial', sans-serif; line-height: 1.6;
                    font-size: 10pt; color: var(--dark-gray); margin: 0; padding: 0; -webkit-font-smoothing: antialiased;
                    text-rendering: optimizeLegibility;
                }
                * { box-sizing: border-box; }
                h1, h2, h3, h4, h5, h6 { margin-top: 1.5em; margin-bottom: 0.5em; page-break-after: avoid; color: var(--navy-blue); font-weight: bold; line-height: 1.3; }
                h1 { font-size: 22pt; }
                h2 { font-size: 16pt; border-bottom: 1.5px solid var(--lime-green); padding-bottom: 0.3em; margin-top: 2em; margin-bottom: 1em;}
                h3 { font-size: 13pt; margin-top: 1.8em; margin-bottom: 0.8em; }
                h4 { font-size: 11pt; font-weight: bold; color: #34495e; margin-top: 1.5em; margin-bottom: 0.6em;}
                h5, h6 { font-size: 10pt; font-weight: bold; color: #7f8c8d; margin-top: 1.2em; margin-bottom: 0.5em;}
                h2:first-child, h3:first-child, h4:first-child { margin-top: 0.5em; }
                p, ul, ol, dl { margin-top: 0.6em; margin-bottom: 0.6em; text-align: justify; hyphens: auto; widows: 3; orphans: 3; }
                ul, ol { padding-left: 1.8em; } li { margin-bottom: 0.4em; }
                a { color: var(--soft-blue); text-decoration: none; } a:hover { text-decoration: underline; }
                a.long-url { word-wrap: break-word; word-break: break-all; font-size: 0.85em; color: #7f8c8d; font-family: monospace; line-height: 1.2; }
                .cover { page: cover; width: 21cm; height: 29.7cm; display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center; page-break-after: always; background: linear-gradient(135deg, var(--primary-white) 0%, #f8f9fa 100%); position: relative; overflow: hidden; padding: 0; }
                .cover-header-bar { position: absolute; top: 0; left: 0; right: 0; height: 15px; background: linear-gradient(90deg, var(--lime-green), var(--navy-blue)); z-index: 1; }
                .cover-footer-bar { position: absolute; bottom: 0; left: 0; right: 0; height: 10px; background: linear-gradient(90deg, var(--navy-blue), var(--lime-green)); z-index: 1; }
                .cover-wrapper { padding: 4cm 3cm; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-grow: 1; z-index: 2; }
                .cover-logo { width: auto; max-height: 80px; margin-bottom: 3cm; object-fit: contain; }
                .cover-content { margin-bottom: 4cm; }
                .cover h1 { font-size: 32pt; margin: 0 0 1cm 0; color: var(--navy-blue); font-weight: bold; line-height: 1.2; letter-spacing: -0.02em; }
                .cover .subtitle { font-size: 20pt; margin: 0 0 2cm 0; color: var(--soft-blue); font-weight: normal; line-height: 1.3; }
                .cover .date { font-size: 12pt; color: #7f8c8d; margin-top: 1cm; }
                .cover-footer-text { font-size: 10pt; color: #95a5a6; padding: 1cm 2cm; width: 100%; text-align: center; line-height: 1.4; z-index: 2; position: absolute; bottom: 2cm; left: 0; }
                .table-of-contents { padding: 1cm 0; page: toc; page-break-after: always; }
                .toc-container { margin: 0 auto; max-width: 17cm; background: white; padding: 1.5cm 0; }
                .toc-title { font-size: 20pt; color: var(--navy-blue); margin-bottom: 1.5em; text-align: center; font-weight: bold; letter-spacing: 0.05em; border-bottom: none; position: relative; padding-bottom: 0.5cm; }
                .toc-title::after { content: ""; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 8cm; height: 2px; background: linear-gradient(90deg, transparent, var(--lime-green), transparent); }
                .toc-entries { padding: 0; margin-top: 1em; }
                .toc-entry { margin: 0.6em 0; position: relative; display: flex; align-items: baseline; justify-content: space-between; font-size: 11pt; }
                .toc-entry::after { content: ""; position: absolute; bottom: 0.4em; left: 0; right: 0; border-bottom: 1px dotted var(--light-gray); z-index: 1; }
                .toc-link { font-weight: bold; color: var(--navy-blue); text-decoration: none; background: white; padding-right: 0.5em; position: relative; z-index: 2; display: inline-block; max-width: 85%; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
                .toc-link::after { content: target-counter(attr(href), page); position: absolute; right: -3em; top: 0; background: white; padding-left: 0.5em; color: var(--dark-gray); z-index: 2; font-weight: normal; font-size: 10pt; }
                .section-cover { page: section_cover; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; page-break-after: always; background: linear-gradient(145deg, #f8f9fa 0%, #f1f1f1 100%); min-height: 29.7cm; padding: 4cm 3cm; position: relative; border: 1px solid #eee; overflow: hidden; }
                .section-cover-side-bar { content: ""; position: absolute; top: 0; left: 0; width: 15px; height: 100%; background: linear-gradient(to bottom, var(--lime-green), var(--light-lime)); border-right: 1px solid rgba(0, 0, 0, 0.05); }
                .section-cover h2 { font-size: 28pt; margin-bottom: 2cm; color: var(--navy-blue); border: none; font-weight: bold; line-height: 1.2; position: relative; padding-bottom: 0.5cm; }
                .section-cover h2::after { content: ""; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 10cm; height: 2px; background: linear-gradient(90deg, transparent, var(--lime-green), transparent); }
                .section-cover .key-topics-box { margin: 0 auto; text-align: left; width: 80%; max-width: 600px; background: rgba(255, 255, 255, 0.7); padding: 1.5cm; border-radius: 8px; border: 1px solid #eee; }
                .section-cover .key-topics-box h3 { font-size: 16pt; color: var(--soft-blue); margin-top: 0; margin-bottom: 1.5cm; text-align: center; border: none; font-weight: normal; }
                .section-cover .key-topics-box p.section-topic { margin: 0.5em 0; font-size: 11pt; color: #34495e; line-height: 1.5; padding-left: 1.2em; text-indent: -1em; position: relative; }
                .section-cover .key-topics-box p.section-topic::before { content: "•"; position: absolute; left: 0; color: var(--lime-green); font-weight: bold; }
                .section-cover .reading-time { margin-top: 3cm; font-size: 11pt; color: #7f8c8d; font-style: italic; background: rgba(255, 255, 255, 0.8); padding: 0.5cm 1cm; border-radius: 50px; border: 1px solid #eee; }
                .section-cover .reading-time-value { font-weight: bold; color: var(--navy-blue); }
                .section-content { margin-bottom: 2cm; page-break-before: auto; }
                .section-intro { font-size: 11pt; font-style: italic; color: #555; margin-bottom: 1.5em; padding: 0.5em 1em; border-left: 3px solid var(--lime-green); background-color: #f9f9f9; border-radius: 4px; }
                .section-intro p:first-child { margin-top: 0; } .section-intro p:last-child { margin-bottom: 0; }
                figure:not(.graph-figure) { margin: 1.5em 0; page-break-inside: avoid; text-align: center; }
                figcaption:not(.graph-figure figcaption) { font-style: italic; font-size: 9pt; color: #7f8c8d; text-align: center; margin-top: 0.5em; }
                figure img:not(.graph-image) { max-width: 100%; height: auto; margin: 0 auto; display: block; border: 1px solid #ddd; padding: 2px; }
                .table-responsive { margin: 1em 0; width: 100%; overflow-x: auto; page-break-inside: auto; }
                .enhanced-table { width: 100%; border-collapse: collapse; margin-bottom: 1em; font-size: 9pt; table-layout: auto; }
                .enhanced-table thead { display: table-header-group; background-color: #f5f8fa; border-bottom: 2px solid var(--navy-blue); }
                .enhanced-table tbody tr { page-break-inside: avoid; }
                .enhanced-table tbody tr:nth-child(even) { background-color: #fcfdff; }
                .enhanced-table th { padding: 8px 10px; text-align: left; font-weight: bold; color: var(--navy-blue); white-space: nowrap; vertical-align: bottom; }
                .enhanced-table td { padding: 6px 10px; border-bottom: 1px solid #e9ecef; vertical-align: top; line-height: 1.4; }
                .enhanced-table td p:first-child { margin-top: 0; } .enhanced-table td p:last-child { margin-bottom: 0; }
                .enhanced-table tbody tr:last-child td { border-bottom: none; }
                .enhanced-table .text-right { text-align: right; } .enhanced_table .text-center { text-align: center; } .enhanced_table .text-left { text-align: left; }
                pre { background-color: #f8f9fa; padding: 12px 15px; border: 1px solid #dee2e6; border-radius: 4px; overflow-x: auto; font-family: 'Courier New', Courier, monospace; font-size: 9pt; line-height: 1.45; page-break-inside: avoid; white-space: pre-wrap; word-wrap: break-word; }
                code { font-family: 'Courier New', Courier, monospace; font-size: 0.9em; background-color: #e9ecef; padding: 2px 5px; border-radius: 3px; color: #495057; word-wrap: break-word; }
                blockquote { margin: 1.5em 0 1.5em 1.5em; padding: 1em 1.5em; border-left: 4px solid var(--lime-green); background-color: #fafdF3; color: var(--dark-gray); page-break-inside: avoid; border-radius: 0 4px 4px 0; }
                blockquote p { margin-top: 0; margin-bottom: 0.5em; font-style: italic; text-align: left; }
                blockquote p:last-child { margin-bottom: 0; }
                blockquote footer { font-size: 0.9em; color: #6c757d; margin-top: 1em; text-align: right; font-style: normal; }
                blockquote footer::before { content: "— "; }
                .enhanced-list, .nested-list { margin: 0.8em 0; padding-left: 1.8em; line-height: 1.5; }
                .enhanced-list-item, .nested-list-item { margin-bottom: 0.4em; padding-left: 0.2em; }
                ul.enhanced-list { list-style-type: disc; } ul.nested-list.level-2 { list-style-type: circle; } ul.nested-list.level-3 { list-style-type: square; } ul.nested-list.level-4 { list-style-type: '- '; }
                ol.enhanced-list { list-style-type: decimal; } ol.nested-list.level-2 { list-style-type: lower-alpha; } ol.nested-list.level-3 { list-style-type: lower-roman; } ol.nested-list.level-4 { list-style-type: decimal; }
                ul li::marker, ol li::marker { color: var(--dark-gray); font-weight: normal; }
                ul.enhanced-list > li::marker { color: var(--lime-green); font-weight: bold; }
                .definition-list { margin: 1em 0; padding: 0; } .definition-list dt.term { font-weight: bold; color: var(--navy-blue); margin-top: 1em; } .definition-list dd.definition { margin-left: 2em; margin-bottom: 1em; padding-left: 0.5em; border-left: 2px solid #eee; }
                .enhanced-footnotes { margin-top: 3em; padding-top: 1em; border-top: 1px solid #ddd; font-size: 9pt; color: #666; }
                h3.footnote-title { font-size: 11pt; color: var(--dark-gray); margin-bottom: 1em; border-bottom: none; }
                .footnote-list { list-style-type: decimal; padding-left: 1.5em; } .footnote-item { margin-bottom: 0.5em; line-height: 1.4; }
                .footnote-item p { margin: 0; display: inline; } .footnote-item a[href^="#fnref"] { color: var(--soft-blue); text-decoration: none; margin-left: 0.3em; font-weight: bold; }
                .footnote-item a[href^="#fnref"]:hover { text-decoration: underline; }
                .end-page { page: end; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); height: 29.7cm; position: relative; border: 1px solid #eee; overflow: hidden; }
                .end-page-header-bar { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 10px; background: linear-gradient(90deg, var(--navy-blue), var(--lime-green)); }
                .end-page-footer-bar { content: ""; position: absolute; bottom: 0; left: 0; right: 0; height: 10px; background: linear-gradient(90deg, var(--lime-green), var(--navy-blue)); }
                .end-page-content { max-width: 650px; padding: 3cm; background: rgba(255, 255, 255, 0.85); border-radius: 10px; border: 1px solid #eee; z-index: 1; }
                .end-page h2 { font-size: 28pt; margin-bottom: 1cm; color: var(--navy-blue); border-bottom: none; }
                .end-page p { font-size: 12pt; color: #34495e; margin-bottom: 1cm; line-height: 1.5; text-align: center; }
                .end-page .contact { font-size: 11pt; margin-top: 2cm; color: #7f8c8d; border-top: 1px solid rgba(0, 0, 0, 0.1); padding-top: 1cm; width: 100%; }
                .end-page .contact p { font-size: 11pt; margin-bottom: 0.5em;}
                .graph-figure { margin: 1.5em auto; page-break-inside: avoid; text-align: center; background: #ffffff; padding: 15px; border: 1px solid #eee; border-radius: 6px; max-width: 95%; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
                .graph-image { max-width: 100%; height: auto; margin: 0 auto 0.5em auto; display: block; border-radius: 4px; }
                .graph-figure figcaption { font-style: normal; font-size: 9pt; color: #555; text-align: center; margin-top: 0.8em; padding: 0 10px; line-height: 1.4; }
                .graph-source { font-size: 8pt; color: #888; text-align: right; margin-top: 0.5em; font-style: normal; padding-right: 10px; }
                @media print { .graph-figure { break-inside: avoid; box-shadow: none; } }
                .page-break-before { page-break-before: always; } .page-break-after { page-break-after: always; } .avoid-break { page-break-inside: avoid; }
                .text-right { text-align: right !important; } .text-center { text-align: center !important; } .text-left { text-align: left !important; }
            """ % (company_name_for_css, company_name_for_css) # Inject company name

            css = CSS(string=css_string, font_config=font_config)

            output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

            html.write_pdf(
                target=str(output_pdf_path),
                stylesheets=[css],
                presentational_hints=True,
                font_config=font_config
            )
            logger.info(f"PDF generated successfully: {output_pdf_path}")
            return output_pdf_path
        except Exception as e:
            logger.error(f"Error during WeasyPrint PDF generation: {e}", exc_info=True)
            debug_html_path = output_pdf_path.with_suffix('.debug.html')
            try:
                with open(debug_html_path, 'w', encoding='utf-8') as f_debug:
                    f_debug.write(final_html_content)
                logger.info(f"Debug HTML saved to: {debug_html_path}")
            except Exception as write_e:
                 logger.error(f"Could not write debug HTML file: {write_e}")
            return None


# --- Standalone Function ---
def process_markdown_files(base_dir: Path, company_name: str, language: str, template_path: Optional[str] = None) -> Optional[Path]:
    """Process all markdown files in the markdown directory and generate a PDF."""
    markdown_dir = base_dir / 'markdown'
    pdf_dir = base_dir / 'pdf'

    if not base_dir.is_dir():
        logger.error(f"Base directory provided does not exist: {base_dir}")
        return None

    try:
        os.makedirs(markdown_dir, exist_ok=True)
        os.makedirs(pdf_dir, exist_ok=True)
    except OSError as e:
         logger.error(f"Could not create necessary subdirectories in {base_dir}: {e}")
         return None

    if not markdown_dir.is_dir():
        logger.error(f"Markdown directory could not be created or found: {markdown_dir}")
        return None

    sections = []
    logger.info(f"Loading sections from: {markdown_dir} using SECTION_ORDER")
    for section_id, section_title in SECTION_ORDER:
        file_path = markdown_dir / f"{section_id}.md"
        if file_path.exists() and file_path.is_file():
            logger.debug(f"Reading markdown file: {file_path}")
            try:
                content = file_path.read_text(encoding='utf-8')
                if content.strip():
                    section = PDFSection(id=section_id, title=section_title, content=content)
                    sections.append(section)
                    logger.debug(f"Added section '{section_title}' from {file_path.name}")
                else:
                     logger.warning(f"Skipping empty markdown file: {file_path.name}")
            except Exception as e:
                 logger.error(f"Error reading markdown file {file_path}: {e}", exc_info=True)
        else:
             logger.warning(f"Markdown file not found for section '{section_id}' ({file_path}), skipping.")

    if not sections:
        logger.warning("No valid, non-empty markdown sections found to generate PDF.")
        return None

    logger.info(f"Found {len(sections)} sections to include in the PDF for {company_name} ({language}).")

    try:
        pdf_generator = EnhancedPDFGenerator(template_path)
    except Exception as e:
        logger.error(f"Failed to initialize EnhancedPDFGenerator: {e}", exc_info=True)
        return None

    output_pdf_path = pdf_dir / f"{company_name}_{language}_Report.pdf"

    report_metadata = {
        'title': f"{company_name} {language} Report",
        'company': company_name,
        'language': language,
    }

    generated_path = pdf_generator.generate_pdf(
        sections_data=sections,
        output_pdf_path=str(output_pdf_path),
        metadata=report_metadata
    )

    return generated_path