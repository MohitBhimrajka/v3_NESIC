#!/bin/bash
# Simple shell script to run the digest generator

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed or not in PATH"
    exit 1
fi

# Determine python command
PYTHON_CMD="python"
if ! command -v python &> /dev/null && command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Parse arguments
INCLUDE_SAMPLE=""
CONFIG_FILE="digests/digest_config.json"
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --yes)
            INCLUDE_SAMPLE="--include-sample yes"
            shift
            ;;
        --no)
            INCLUDE_SAMPLE="--include-sample no"
            shift
            ;;
        --config)
            CONFIG_FILE="$2"
            shift
            shift
            ;;
        --output)
            OUTPUT_FILE="--output $2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--yes|--no] [--config CONFIG_FILE] [--output OUTPUT_FILE]"
            exit 1
            ;;
    esac
done

# Run the digest generator
echo "🔍 Running Code Digest Generator..."
$PYTHON_CMD digests/generate_digest.py $INCLUDE_SAMPLE --config "$CONFIG_FILE" $OUTPUT_FILE

# Make the script executable if it's not already
if [ ! -x "digests/generate_digest.py" ]; then
    chmod +x digests/generate_digest.py
fi

# Show success message
echo "✅ Digest generation completed!"
echo "👉 Check the 'digests/output' folder for results."

exit 0 