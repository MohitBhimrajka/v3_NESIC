"""PDF Generator Module."""

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
from bs4 import BeautifulSoup, Comment
import re
from typing import Optional, Dict, List, Tuple, Any
from config import SECTION_ORDER, PDF_CONFIG
from pydantic import BaseModel

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
    """Enhanced PDF Generator with better markdown support and styling."""
    
    def __init__(self, template_path: Optional[str] = None):
        """Initialize the PDF generator with an optional custom template path."""
        if template_path:
            self.template_dir = str(Path(template_path).parent)
            self.template_name = Path(template_path).name
        else:
            # Adjusted to handle new path location
            module_path = Path(__file__).parent.parent.parent.parent  # Go up to project root
            self.template_dir = str(module_path / 'templates')
            self.template_name = 'enhanced_report_template.html'
        
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self.template = self.env.get_template(self.template_name)
        
        # Initialize markdown with an expanded set of extensions
        self.md = markdown.Markdown(extensions=[
            'extra',  # Includes tables, fenced_code, footnotes, etc.
            'meta',
            'codehilite',
            'admonition',
            'attr_list',
            'toc',
            'def_list',  # Definition lists
            'footnotes',  # Footnotes support
            'abbr',  # Abbreviation support
            'md_in_html',  # Markdown inside HTML
            'sane_lists',  # Better list handling
            'nl2br',  # Convert newlines to <br> tags for proper line breaks
        ], extension_configs={
            'codehilite': {'css_class': 'highlight', 'guess_lang': False},
            'toc': {'permalink': False},  # Disable permalinks to remove ¶
            'footnotes': {'BACKLINK_TEXT': '↩'}
        })

    def _extract_section_metadata(self, content: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter and content from a markdown section."""
        metadata = {}
        content = content.lstrip()  # Remove leading whitespace
        if content.startswith('---'):
            try:
                # Split carefully, expecting '---', yaml block, '---', content
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    markdown_content = parts[2]
                    loaded_meta = yaml.safe_load(frontmatter)
                    # Ensure it's a dict, handle empty frontmatter gracefully
                    metadata = loaded_meta if isinstance(loaded_meta, dict) else {}
                    return metadata, markdown_content.strip()
            except (yaml.YAMLError, IndexError, ValueError) as e:
                # If debugging needed: print(f"Failed to parse YAML frontmatter: {e}")
                pass
        return metadata, content.strip()

    def _estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in minutes based on word count."""
        words = len(content.split())
        # Assuming faster reading speed (300 words per minute) and capping at 5 minutes
        estimated_time = min(5, max(1, round(words / 300)))
        return estimated_time

    def _extract_key_topics(self, content: str, max_topics: int = None) -> List[str]:
        """Extract key topics from the content based on headings.
        
        This extracts the subsection headings (h2, h3) from the content to build
        a table of contents.
        
        Args:
            content: The markdown content to extract topics from
            max_topics: Optional maximum number of topics to extract
            
        Returns:
            List of topic strings
        """
        # First convert the markdown to HTML to get proper heading structure
        temp_html = self._convert_markdown_to_html(content)
        soup = BeautifulSoup(temp_html, 'html.parser')
        
        # Only consider h2 and h3 headings for key topics
        headings = soup.find_all(['h2', 'h3'])
        topics = []
        
        # Skip the first h2 if it exists and looks like a title
        starting_index = 0
        if headings and headings[0].name == 'h2':
            # Check if it's the section title (usually matches the section.title)
            starting_index = 1
        
        for heading in headings[starting_index:]:
            # Get the clean text without numbers
            text = heading.get_text().strip()
            
            # Remove any leading numbers like "1. " or "1.1. " that might be present
            clean_text = re.sub(r'^\d+(\.\d+)*\.\s+', '', text)
            
            topics.append(clean_text)
            
            # Only limit if max_topics is specified
            if max_topics and len(topics) >= max_topics:
                break
        
        return topics

    def _create_markdown_processor(self):
        """Create a markdown processor with all necessary extensions."""
        md = markdown.Markdown(extensions=[
            'extra',  # Includes tables, fenced_code, footnotes, etc.
            'meta',
            'codehilite',
            'admonition',
            'attr_list',
            'toc',
            'def_list',  # Definition lists
            'footnotes',  # Footnotes support
            'abbr',  # Abbreviation support
            'md_in_html',  # Markdown inside HTML
            'sane_lists',  # Better list handling
            'nl2br',  # Convert newlines to <br> tags for proper line breaks
        ], extension_configs={
            'codehilite': {'css_class': 'highlight', 'guess_lang': False},
            'toc': {'permalink': False},  # Disable permalinks to remove ¶
            'footnotes': {'BACKLINK_TEXT': '↩'}
        })
        return md
        
    def _process_headings(self, soup):
        """Add classes and IDs to headings for better navigation without visible permalinks."""
        # Process all headings for better styling and navigation
        for h_tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            # Add classes based on heading level
            h_tag['class'] = h_tag.get('class', []) + [f'heading-{h_tag.name}']
            
            # Generate an ID from the heading text if it doesn't have one
            if not h_tag.get('id'):
                heading_text = h_tag.get_text().strip()
                heading_id = re.sub(r'[^\w\s-]', '', heading_text.lower())
                heading_id = re.sub(r'[\s-]+', '-', heading_id)
                h_tag['id'] = heading_id
            
            # We no longer add the visible paragraph symbol anchor
            # Just ensure the heading has an ID for internal linking

    def _convert_markdown_to_html(self, markdown_content):
        """
        Convert markdown content to HTML with enhanced styling.
        """
        # Create the markdown object with all extensions
        md = self._create_markdown_processor()
        
        # Convert markdown to HTML
        html = md.convert(markdown_content)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Process headings to add anchors for TOC
        self._process_headings(soup)
        
        # Process lists - first-level lists
        for ul in soup.find_all(['ul', 'ol'], recursive=False):
            self._process_list(ul, level=1, soup=soup)
        
        # Find any lists that may be inside other elements (not directly under body)
        for container in soup.find_all(['div', 'blockquote', 'td']):
            for ul in container.find_all(['ul', 'ol'], recursive=False):
                self._process_list(ul, level=1, soup=soup)
        
        # Process tables
        for table in soup.find_all('table'):
            table['class'] = table.get('class', []) + ['table', 'table-striped', 'table-hover']
            
            # If the table has a thead, add a class to it
            thead = table.find('thead')
            if thead:
                thead['class'] = thead.get('class', []) + ['thead-dark']
            
            # If the first row contains th elements, it's a header row
            # Create a thead if it doesn't exist
            first_row = table.find('tr')
            if first_row and first_row.find('th') and not thead:
                thead = soup.new_tag('thead')
                thead['class'] = ['thead-dark']
                table.insert(0, thead)
                thead.append(first_row)
        
        return str(soup)

    def _process_list(self, list_tag, level=1, soup=None):
        """Add classes to list elements for better styling."""
        # Add classes based on list type and level
        list_type = 'ul' if list_tag.name == 'ul' else 'ol'
        list_tag['class'] = list_tag.get('class', []) + [f'{list_type}-level-{level}']
        
        # Process all list items
        for li in list_tag.find_all('li', recursive=False):
            li['class'] = li.get('class', []) + [f'li-level-{level}']
            
            # Recursively process nested lists with increased level
            for nested_list in li.find_all(['ul', 'ol'], recursive=False):
                self._process_list(nested_list, level=level+1, soup=soup)

    def _generate_toc(self, sections):
        """Generate a table of contents from the sections."""
        toc_html = '<div class="toc-container"><div class="toc-header">Table of Contents</div><ul class="toc-list">'
        
        for idx, section in enumerate(sections, 1):
            # Skip empty sections
            if not section.html_content.strip():
                continue
                
            # Create a link to the section
            section_id = section.id.lower().replace(' ', '-')
            toc_html += f'<li class="toc-item"><a href="#{section_id}" class="toc-link">{section.title}</a>'
            
            # If the section has key topics, add them as nested links
            if section.key_topics:
                toc_html += '<ul class="toc-sublist">'
                for topic in section.key_topics:
                    topic_id = re.sub(r'[^\w\s-]', '', topic.lower()).replace(' ', '-')
                    toc_html += f'<li class="toc-subitem"><a href="#{topic_id}" class="toc-sublink">{topic}</a></li>'
                toc_html += '</ul>'
            
            toc_html += '</li>'
        
        toc_html += '</ul></div>'
        return toc_html

    def _process_sections(self, sections):
        """Process all sections to extract metadata and generate HTML content."""
        for section in sections:
            # Extract section metadata and clean content
            metadata, content = self._extract_section_metadata(section.content)
            section.metadata = metadata
            
            # Extract intro paragraph for section summaries
            section.intro = self._extract_intro(content)
            
            # Extract key topics/subsections for TOC and summaries
            section.key_topics = self._extract_key_topics(content, max_topics=5)
            
            # Estimate reading time
            section.reading_time = self._estimate_reading_time(content)
            
            # Convert markdown to HTML with enhanced processing
            section.html_content = self._convert_markdown_to_html(content)
        
        return sections

    def _extract_intro(self, content: str) -> str:
        """Extract the first paragraph for use as an introduction/summary."""
        # Find the first non-heading paragraph
        lines = content.split('\n')
        paragraph = []
        
        for line in lines:
            # Skip lines that look like headings or YAML markers
            if line.startswith('#') or line.startswith('---'):
                continue
            
            # If we find a non-empty line, start collecting
            if line.strip() and not paragraph:
                paragraph.append(line.strip())
            # Add more lines if we've already started a paragraph
            elif paragraph and line.strip():
                paragraph.append(line.strip())
            # Break when we hit an empty line after collecting some content
            elif paragraph and not line.strip():
                break
        
        intro = ' '.join(paragraph)
        
        # If the intro is very long, truncate it
        max_length = 200
        if len(intro) > max_length:
            intro = intro[:max_length].rsplit(' ', 1)[0] + '...'
        
        return intro

    def generate_pdf(self, sections_data: List[PDFSection], output_path: str, metadata: Dict) -> Path:
        """
        Generate a PDF from a list of processed sections.
        
        Args:
            sections_data: List of PDFSection objects with content already processed
            output_path: Path where the PDF should be saved
            metadata: Dict of metadata for the report (company name, language, etc.)
            
        Returns:
            Path to the generated PDF file
        """
        # Make sure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process all sections
        processed_sections = self._process_sections(sections_data)
        
        # Set default logo and favicon for simplicity
        base_url = str(Path.cwd())
        logo_url = metadata.get('logo', 'templates/assets/supervity_logo.png')
        favicon_url = metadata.get('favicon', 'templates/assets/supervity_favicon.png')
        
        print(f"Using logo URL: {logo_url}")
        print(f"Using favicon URL: {favicon_url}")
        print(f"Using base URL: {base_url}")
        
        # Check if logo exists, use a default if not
        if not Path(logo_url).exists():
            logo_url = str(Path(base_url) / 'templates/assets/supervity_logo.png')
        
        # Generate TOC
        toc_html = self._generate_toc(processed_sections)
        
        # Generate the HTML content from the template
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%d")
        
        html_content = self.template.render(
            title=f"{metadata.get('company_name', 'Company')} {metadata.get('report_type', 'Analysis')}",
            company_name=metadata.get('company_name', 'Company'),
            language=metadata.get('language', 'English'),
            date=formatted_date,
            sections=processed_sections,
            toc=toc_html,
            logo_url=logo_url,
            favicon_url=favicon_url,
            section_order=SECTION_ORDER,
            pdf_config=PDF_CONFIG
        )
        
        # Generate the PDF file from HTML
        font_config = FontConfiguration()
        html = HTML(string=html_content, base_url=base_url)
        
        # Define CSS for the PDF
        css_files = [
            str(Path(base_url) / 'templates/css/pdf.css'),
            str(Path(base_url) / 'templates/css/github-markdown.css'),
            str(Path(base_url) / 'templates/css/highlight.css')
        ]
        
        css = [CSS(filename=css_file) for css_file in css_files if Path(css_file).exists()]
        
        # If no CSS files exist, use default styles
        if not css:
            default_css = CSS(string="""
                @page {
                    margin: 1cm;
                    @top-center {
                        content: string(title);
                        font-size: 9pt;
                        font-weight: bold;
                    }
                    @bottom-right {
                        content: counter(page);
                        font-size: 9pt;
                    }
                }
                html {
                    font-size: 11pt;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                }
                h1 {
                    color: #333;
                    font-size: 2.0em;
                    margin-top: 1.5em;
                    string-set: title content();
                }
                h2 {
                    color: #333;
                    font-size: 1.75em;
                    margin-top: 1.2em;
                    border-bottom: 1px solid #eaecef;
                    padding-bottom: 0.3em;
                }
                h3 {
                    font-size: 1.5em;
                    margin-top: 1.1em;
                }
                h4 {
                    font-size: 1.25em;
                    margin-top: 1em;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1em 0;
                }
                table, th, td {
                    border: 1px solid #eaecef;
                }
                th {
                    background-color: #f6f8fa;
                    padding: 8px;
                    text-align: left;
                }
                td {
                    padding: 8px;
                }
                li {
                    margin: 0.5em 0;
                }
                .page-break {
                    page-break-after: always;
                }
                .section-cover {
                    text-align: center;
                    margin-top: 33vh;
                }
                .section-cover h1 {
                    font-size: 2.5em;
                    margin-top: 0;
                }
                .section-cover .section-subtitle {
                    font-size: 1.5em;
                    color: #666;
                    margin-top: 0.5em;
                }
                .chapter-heading {
                    margin-top: 2em;
                    font-size: 1.1em;
                    color: #666;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }
                .toc-container {
                    margin: 2em 0;
                }
                .toc-header {
                    font-size: 1.5em;
                    font-weight: bold;
                    margin-bottom: 1em;
                }
                .toc-list {
                    list-style-type: none;
                    padding-left: 0;
                }
                .toc-sublist {
                    list-style-type: none;
                    padding-left: 1.5em;
                }
                .toc-item {
                    margin: 0.7em 0;
                    font-weight: bold;
                }
                .toc-subitem {
                    margin: 0.3em 0;
                    font-weight: normal;
                }
                .toc-link, .toc-sublink {
                    text-decoration: none;
                    color: #333;
                }
                .toc-link::after, .toc-sublink::after {
                    content: leader('.') target-counter(attr(href), page);
                    margin-left: 0.5em;
                }
                .report-cover {
                    text-align: center;
                    margin-top: 30vh;
                }
                .report-title {
                    font-size: 2.8em;
                    font-weight: bold;
                    margin-bottom: 0.3em;
                }
                .report-subtitle {
                    font-size: 1.8em;
                    color: #666;
                    margin-bottom: 1em;
                }
                .report-date {
                    font-size: 1.2em;
                    color: #888;
                    margin-top: 1em;
                }
                .report-company {
                    font-size: 2em;
                    color: #333;
                    margin-bottom: 0.5em;
                }
                .report-logo {
                    max-width: 300px;
                    margin-bottom: 2em;
                }
                .footer {
                    text-align: center;
                    margin-top: 2em;
                    font-size: 0.9em;
                    color: #888;
                }
                
                /* Section intro boxes */
                .section-intro-box {
                    background-color: #f8f9fa;
                    border-left: 4px solid #007bff;
                    padding: 1em;
                    margin: 1.5em 0;
                }
                .section-intro-title {
                    font-weight: bold;
                    font-size: 1.1em;
                    margin-bottom: 0.5em;
                }
                .section-key-topics {
                    margin-top: 0.5em;
                }
                .section-key-topics-title {
                    font-weight: bold;
                    margin-bottom: 0.3em;
                }
                .section-key-topics-list {
                    margin: 0;
                    padding-left: 1.5em;
                }
                
                /* Source styling */
                .sources-section {
                    margin-top: 2em;
                    border-top: 1px solid #eaecef;
                    padding-top: 1em;
                }
                .sources-heading {
                    font-size: 1.5em;
                    margin-bottom: 1em;
                }
                .sources-list {
                    padding-left: 1.5em;
                }
                .source-item {
                    margin-bottom: 0.5em;
                }
            """)
            css = [default_css]
        
        # Generate the PDF
        html.write_pdf(output_path, stylesheets=css, font_config=font_config)
        
        print(f"PDF generated successfully: {output_path}")
        return Path(output_path)

    def _cleanup_raw_markdown(self, content: str) -> str:
        """Clean up raw markdown content before processing."""
        # Replace Windows-style line endings with Unix style
        content = content.replace('\r\n', '\n')
        
        # Ensure there's a newline at the end of each file
        if not content.endswith('\n'):
            content += '\n'
            
        return content

    def _extract_metadata_and_split_sources(self, raw_content: str) -> Tuple[Dict, str, str]:
        """Extract YAML frontmatter, main content, and sources section."""
        metadata, content_with_sources = self._extract_section_metadata(raw_content)
        
        # Try to split content and sources
        main_content = content_with_sources
        sources_content = ""
        
        # Look for a "Sources" or "##Sources" heading
        source_patterns = [
            r'(?i)##\s*sources\s*\n',  # ## Sources
            r'(?i)#\s*sources\s*\n',   # # Sources
            r'(?i)\*\*sources\*\*\s*\n',  # **Sources**
            r'(?i)sources:\s*\n',      # Sources:
        ]
        
        for pattern in source_patterns:
            match = re.search(pattern, content_with_sources)
            if match:
                split_index = match.start()
                main_content = content_with_sources[:split_index].strip()
                sources_content = content_with_sources[split_index:].strip()
                break
        
        return metadata, main_content, sources_content

def process_markdown_files(base_dir: Path, company_name: str, language: str, template_path: Optional[str] = None) -> Optional[Path]:
    """
    Process markdown files in the specified directory and generate a PDF report.
    
    Args:
        base_dir: Path to the base directory containing the markdown directory
        company_name: Name of the company for the report
        language: Language of the report
        template_path: Optional path to a custom template
        
    Returns:
        Path to the generated PDF, or None if an error occurred
    """
    try:
        markdown_dir = base_dir / "markdown"
        pdf_dir = base_dir / "pdf"
        
        # Ensure PDF directory exists
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a PDF generator
        pdf_generator = EnhancedPDFGenerator(template_path)
        
        # Collect all sections
        sections = []
        
        # Get the order of sections from config (if available)
        for section_id in SECTION_ORDER:
            section_file = markdown_dir / f"{section_id}.md"
            
            if not section_file.exists():
                # Skip sections that don't exist
                continue
                
            # Read the content
            content = section_file.read_text(encoding='utf-8')
            
            # Create a title based on section ID if not specified otherwise
            title = section_id.replace('_', ' ').title()
            
            # Create a section object
            section = PDFSection(
                id=section_id,
                title=title,
                content=content
            )
            
            sections.append(section)
        
        # Output file path
        output_path = pdf_dir / f"{company_name}_{language}_Report.pdf"
        
        # Generate the PDF
        pdf_path = pdf_generator.generate_pdf(
            sections,
            str(output_path),
            {
                'company_name': company_name,
                'language': language,
                'report_type': 'Analysis',
                'logo': 'templates/assets/supervity_logo.png',
                'favicon': 'templates/assets/supervity_favicon.png'
            }
        )
        
        return pdf_path
    
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return None 