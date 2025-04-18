from setuptools import setup, find_packages

setup(
    name="supervity",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.85.0",
        "uvicorn>=0.18.0",
        "jinja2>=3.1.0",
        "markdown>=3.4.3",
        "weasyprint>=59.0",
        "pydantic>=2.0.0",
        "google-generativeai==0.8.4",
        "python-dotenv>=1.0.0",
        "pytest>=7.0.0",
    ],
    python_requires=">=3.8",
    author="Supervity Team",
    description="PDF Generator Service",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "supervity-pdf=cli.pdf_cli:main",
        ],
    },
) 