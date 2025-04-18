"""Prompt templates and utilities."""

# Import from the project root without using sys.path.append
from prompt_testing import *

def get_prompt_fn(name):
    """Get a prompt function by name from the prompt_testing module."""
    return globals().get(name)

__all__ = ["get_prompt_fn"] 