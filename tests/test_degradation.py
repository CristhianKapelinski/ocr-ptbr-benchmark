"""Unit tests for the HYB per-degradation tagging."""
from __future__ import annotations

from ocr_bench.degradation import degradation_of


def test_degradation_of_strips_page_prefix_and_index():
    assert degradation_of("page103_Noise_SaltAndPepper_0.png") == "Noise_SaltAndPepper"
    assert degradation_of("page102_Rot_color_0.png") == "Rot_color"
    assert degradation_of("page50_Phantom_0.85_3.png") == "Phantom_0.85"


def test_degradation_of_handles_missing_suffix():
    assert degradation_of("page1_Bleed_0") == "Bleed"
