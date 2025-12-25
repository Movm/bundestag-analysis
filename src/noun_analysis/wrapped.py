"""Backwards compatibility shim - import from wrapped package.

This file re-exports all public symbols from the wrapped/ package
for backwards compatibility with existing imports like:

    from noun_analysis.wrapped import WrappedData, WrappedRenderer

New code should import directly from the package:

    from noun_analysis.wrapped import WrappedData, WrappedRenderer
"""

from noun_analysis.wrapped import *  # noqa: F401, F403
