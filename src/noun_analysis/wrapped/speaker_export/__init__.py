"""Speaker export module - individual Bundestag Wrapped profiles.

This module provides functionality to export individual "Bundestag Wrapped"
profiles for each speaker, including:
- Spirit animal assignment based on speaking behavior
- Signature word and adjective analysis
- Quiz generation about speaker vocabulary
- Comprehensive rankings and statistics

Usage:
    from noun_analysis.wrapped.speaker_export import SpeakerExporter

    exporter = SpeakerExporter(wrapped_data)
    exporter.export_all(output_dir)
"""

from .constants import ANIMAL_CRITERIA, SPIRIT_ANIMALS
from .exporter import SpeakerExporter
from .utils import generate_slug

__all__ = [
    'SpeakerExporter',
    'generate_slug',
    'SPIRIT_ANIMALS',
    'ANIMAL_CRITERIA',
]
