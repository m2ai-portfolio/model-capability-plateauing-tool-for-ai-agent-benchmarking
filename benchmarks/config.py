"""
Configuration management for Model Capability Plateauing Tool.

Supports environment variables with sensible defaults.
"""

import os


class Config:
    """Configuration for benchmarks."""

    # Benchmark configuration
    REASONING_BASELINE_ACCURACY = float(os.getenv('REASONING_BASELINE_ACCURACY', '0.75'))
    REASONING_SUCCESS_THRESHOLD = float(os.getenv('REASONING_SUCCESS_THRESHOLD', '0.80'))

    # Tool Use benchmark configuration
    TOOL_USE_BASELINE_SUCCESS_RATE = float(os.getenv('TOOL_USE_BASELINE_SUCCESS_RATE', '0.70'))
    TOOL_USE_FAILURE_RATE = float(os.getenv('TOOL_USE_FAILURE_RATE', '0.2'))

    # Ablation configuration
    ABLATION_MODULES = ['symbolic_reasoning', 'planning', 'multi_step']

    @classmethod
    def get(cls, key, default=None):
        """Get configuration value."""
        return getattr(cls, key, default)
