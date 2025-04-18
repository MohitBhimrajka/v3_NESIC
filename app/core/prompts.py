"""Prompt templates and utilities."""

import prompt_testing as _p

def get_prompt_fn(name):
    """Get a prompt function by name from the prompt_testing module."""
    return getattr(_p, name)

__all__ = ["get_prompt_fn"] 