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

The project is organized as follows:

```
.
├── app/                # Main application package
│   ├── api/            # API routes and endpoints
│   │   └── main.py     # FastAPI application
│   └── core/           # Core functionality
│       ├── pdf/        # PDF generation module
│       │   ├── generator.py  # PDF generation functionality
│       │   └── __init__.py
│       ├── generator.py      # Re-exports from pdf module
│       ├── prompts.py        # Prompt utilities
│       ├── tasks.py          # Task processing
│       └── __init__.py
├── cli/                # Command-line interface scripts
│   ├── generate_pdf.py # Script to generate PDF from markdown
│   ├── pdf_cli.py      # CLI for PDF generation
│   └── test_agent_prompt.py  # Script to test agent prompts
├── config.py           # Configuration settings
├── prompt_testing.py   # Prompt functions for testing
├── templates/          # Templates for reports
│   ├── assets/         # Images and other assets for PDF
│   ├── css/            # CSS files for PDF styling
│   └── enhanced_report_template.html  # Main HTML template
├── tests/              # Test suite
│   └── test_app_boot.py  # Basic smoke tests
├── requirements.txt    # Project dependencies
├── setup.py            # Package installation setup
└── README.md           # This file
```

## Setup

### Dependencies

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. System dependencies for WeasyPrint (PDF generation):
   - **macOS**: `brew install cairo pango gdk-pixbuf libffi`
   - **Ubuntu/Debian**: `apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`
   - **Windows**: See [WeasyPrint installation docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. Install the package in development mode (recommended):
   ```bash
   pip install -e .
   ```

## Usage

### API Server

Start the API server:
```bash
uvicorn app.api.main:app --reload
```

The API will be available at http://127.0.0.1:8000 with interactive docs at http://127.0.0.1:8000/docs

### Command Line Interface

#### Generate a company report:
```bash
# Using the installed CLI tool
supervity-pdf --company-name "Google" --language "English" --interactive

# Or directly with the module
python -m cli.pdf_cli --company-name "Google" --language "English"
```

#### Generate a PDF from existing markdown files:
```bash
python -m cli.generate_pdf "Google" "English" --output-dir ./output
```

#### Test the agent prompt generation (full process):
```bash
python -m cli.test_agent_prompt
```

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

## System Requirements

The application has several system dependencies:

1. **Python 3.8+** - Required for all functionality

2. **WeasyPrint Dependencies** - For PDF generation:
   WeasyPrint requires system libraries for proper PDF rendering:
   - Cairo, Pango and GDK-PixBuf need to be installed separately
   - Refer to [WeasyPrint's installation docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) for platform-specific instructions
   
3. **Google Generative AI** - For content generation:
   - Requires an API key from Google AI Studio
   - Version is pinned to 0.8.4 for stability

4. **FastAPI and Uvicorn** - For API server functionality

All Python dependencies are specified in requirements.txt and setup.py, but the system libraries for WeasyPrint must be installed separately.