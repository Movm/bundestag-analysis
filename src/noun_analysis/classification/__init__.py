"""Speech classification utilities.

This subpackage provides functions for classifying speech types
based on content and context in Bundestag protocols.
"""

from .speech_start import classify_speech_start, starts_with_president_address
from .context import classify_speech_type, classify_by_preceding_context
from .qa_session import find_qa_session_ranges, is_in_qa_session

__all__ = [
    "classify_speech_start",
    "starts_with_president_address",
    "classify_speech_type",
    "classify_by_preceding_context",
    "find_qa_session_ranges",
    "is_in_qa_session",
]
