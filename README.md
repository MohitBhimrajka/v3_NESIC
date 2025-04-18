# README.md
# Supervity PDF Report Generator

This project generates comprehensive company analysis reports in multiple languages using Google's Gemini API. It processes a set of prompts to create detailed sections on various aspects of a company and compiles them into a professionally formatted PDF report.

## Features

- Generate detailed company analysis reports covering key aspects including: Basic Info, Vision, Management Strategy, Message, Crisis Management, DX, Financials, Competition, Regulatory, Business Structure, Strategy Research
- Multi-language support (Japanese, English, Chinese, Korean, Vietnamese, Thai, Indonesian, Spanish, German, French)
- **Company Disambiguation:** Interactive step to confirm the correct target company, improving report accuracy.
- Professional PDF generation with table of contents, section covers, and consistent styling
- Token usage tracking and execution time statistics
- Parallel processing for faster generation
- Graceful handling of interruptions
- Dynamic platform company name integration for strategy research

## Project Structure

- `test_agent_prompt.py`: Main script to handle user input, company confirmation, LLM calls, and PDF generation orchestration.
- `generate_pdf.py`: Standalone script to generate PDFs from existing markdown files.
- `pdf_generator.py`: PDF generation logic and utilities.
- `prompt_testing.py`: Contains prompt templates for each section, designed to focus on the confirmed company.
- `config.py`: Configuration constants and settings.
- `templates/`: Contains HTML templates for PDF generation.
- `output/`: Directory where generated content is stored.

## Setup

1.  Clone the repository
2.  Install dependencies:

```bash
pip install -r requirements.txt
```

3.  Create a `.env` file with your Gemini API key (see `.env.example`):

```
GEMINI_API_KEY=your_api_key_here
```

4.  Optional: Configure LLM parameters in `.env`:

```
LLM_MODEL=gemini-2.5-pro-preview-03-25
LLM_TEMPERATURE=0.63
```

## Usage

### Generate a Complete Report

Run the main script:

```bash
python test_agent_prompt.py
```

Follow the prompts to enter:
1.  **Target company name** (e.g., "Marvel", "Acme Corp"). The script will use this to search for potential matches.
2.  **Platform company name** (e.g., "NESIC") - used for strategy research and alignment sections.
3.  **Confirm the correct target company:** The script will display potential matches found via search (including name, website, industry, ticker). Select the correct company number from the list, choose 'm' to manually enter key details (website/ticker) if the desired company isn't listed or parsing fails, or 'c' to cancel. *This step is crucial for ensuring the report focuses on the intended entity.*
4.  **Language selection** (1-10, comma separated).
5.  **Section selection** (comma-separated numbers, or 0 for all).

The script will then:
1.  Generate all selected sections **for the confirmed company** in parallel.
2.  Save markdown files in `output/<ConfirmedCompanyName>_<language>_<timestamp>/markdown/`
3.  Generate a PDF report in `output/<ConfirmedCompanyName>_<language>_<timestamp>/pdf/`
4.  Save usage statistics and configuration (including confirmed company details) in `output/<ConfirmedCompanyName>_<language>_<timestamp>/misc/`

### Generate a PDF from Existing Markdown Files

If you already have markdown files in the correct structure (e.g., within an output directory generated previously), you can generate a PDF without re-running the LLM:

```bash
python generate_pdf.py "Confirmed Company Name" "Language" -o path/to/output/directory_containing_markdown_and_pdf_subdirs
```
*Note: This script expects the output structure created by `test_agent_prompt.py`.*

*Alternatively, use the interactive PDF CLI:*
```bash
python pdf_cli.py --interactive
```
*This CLI helps find existing generated reports in the `output` directory and regenerate PDFs.*

## Output Structure

For each generation, the following directory structure is created (using the **confirmed** company name):

```
output/
└── ConfirmedCompanyName_Language_YYYYMMDD_HHMMSS/
    ├── markdown/                # Individual markdown files for each section
    │   ├── basic.md
    │   ├── vision.md
    │   ├── management_strategy.md
    │   └── ...
    ├── pdf/                     # Generated PDF report
    │   └── ConfirmedCompanyName_Language_Report.pdf
    └── misc/                    # Metadata and statistics
        ├── generation_config.yaml # Includes initial input and confirmed details
        └── token_usage_report.json
```

## Customization

- Modify section prompt templates in `prompt_testing.py` (prompts are now designed to incorporate confirmed company details).
- Adjust PDF styling in `templates/enhanced_report_template.html`.
- Configure section order and available languages in `config.py`.
- Customize platform company name integration in strategy research sections.

## Dependencies

- python-dotenv==1.0.0
- markdown==3.4.3
- pyyaml==6.0.1
- beautifulsoup4==4.12.2
- rich==13.5.3
- google-generativeai
- weasyprint>=60.1
- pygments>=2.16.1
- jinja2>=3.1.2
- tiktoken
- gitingest>=0.1.4
- matplotlib>=3.5.0

## License

This project is proprietary and confidential.

## Requirements

- Python 3.8+
- Google Generative AI API access
- Dependencies listed in `requirements.txt`