"""Bundestag Wrapped 2025 - Year in review analysis.

This package provides wrapped analysis functionality split into focused modules:
- types: Constants, dataclass definitions
- wrapped_loader: Data loading from disk
- queries: Analytics query methods
- tone: Tone analysis (Scheme D)
- export: Web/JSON export
- renderer: Terminal rendering
"""

from .types import (
    WrappedDataBase,
    PARTY_COLORS,
    PARTY_EMOJI,
    INTERRUPTER_PATTERN,
    APPLAUSE_PATTERN,
    HECKLE_PATTERN,
    normalize_name_for_comparison,
    Gender,
    SpeakerProfile,
    GenderStats,
    GenderPartyStats,
)
from .wrapped_loader import load_wrapped_data
from .queries import WrappedDataQueries
from .tone import ToneAnalysisMixin
from .speaker_analysis import GenderAnalysisMixin
from .export import ExportMixin
from .renderer import WrappedRenderer


class WrappedData(
    WrappedDataQueries,
    ToneAnalysisMixin,
    GenderAnalysisMixin,
    ExportMixin,
    WrappedDataBase,
):
    """Container for all wrapped analysis data.

    Composed from mixins providing:
    - WrappedDataQueries: General analytics methods (get_top_speakers, etc.)
    - ToneAnalysisMixin: Scheme D tone analysis methods
    - GenderAnalysisMixin: Gender and speaker analysis methods
    - ExportMixin: JSON export and quiz generation
    - WrappedDataBase: Core dataclass fields
    """

    @classmethod
    def load(cls, results_dir, data_dir):
        """Load all data needed for wrapped analysis.

        Args:
            results_dir: Path to analysis results directory (full_data.json, CSVs)
            data_dir: Path to raw data directory (protocols, speeches.json)

        Returns:
            WrappedData instance with all analysis data loaded
        """
        return load_wrapped_data(results_dir, data_dir, cls)


__all__ = [
    # Main classes
    'WrappedData',
    'WrappedRenderer',
    # Gender/speaker analysis types
    'Gender',
    'SpeakerProfile',
    'GenderStats',
    'GenderPartyStats',
    # Constants
    'PARTY_COLORS',
    'PARTY_EMOJI',
    # For advanced usage
    'load_wrapped_data',
]
