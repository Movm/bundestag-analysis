"""Tests for Bundeskanzler speech parsing.

The issue: Friedrich Merz as Bundeskanzler uses the format:
    "Friedrich Merz, Bundeskanzler:"

This doesn't match:
- Regular speaker pattern: "Name (PARTY):"
- President pattern: "Bundeskanzler Name:"

We need to add a new pattern or modify existing ones to capture this format.
"""

import pytest
from noun_analysis.parser import parse_speeches_from_protocol


class TestBundeskanzlerParsing:
    """Test cases for Bundeskanzler speech detection."""

    SAMPLE_PROTOCOL_WITH_KANZLER = """
Plenarprotokoll 21/6
Deutscher Bundestag
Stenografischer Bericht

Präsidentin Julia Klöckner:
Wir kommen nun zur Regierungserklärung des Bundeskanzlers.

Friedrich Merz, Bundeskanzler:
Frau Präsidentin! Meine sehr verehrten Damen und Herren!
Deutschland steht vor großen Herausforderungen. Wir müssen
gemeinsam handeln, um unsere Zukunft zu sichern. Die wirtschaftliche
Lage erfordert entschlossenes Handeln. Wir werden die notwendigen
Reformen umsetzen. Unsere Infrastruktur muss modernisiert werden.
Der Klimaschutz bleibt eine wichtige Aufgabe. Wir stehen zu unseren
internationalen Verpflichtungen. Die Bundeswehr wird gestärkt.
Vielen Dank.

Präsidentin Julia Klöckner:
Vielen Dank, Herr Bundeskanzler. Als Nächster hat das Wort der
Fraktionsvorsitzende der AfD.

Tino Chrupalla (AfD):
Frau Präsidentin! Meine Damen und Herren! Der Herr Bundeskanzler
hat viele Versprechungen gemacht, aber wenig Konkretes gesagt.
Das kennen wir schon von seinen Vorgängern.

Präsidentin Julia Klöckner:
Vielen Dank. Als Nächster hat das Wort Lars Klingbeil für die SPD.

Lars Klingbeil (SPD):
Frau Präsidentin! Liebe Kolleginnen und Kollegen! Wir als
Koalitionspartner stehen hinter dieser Regierung und werden
gemeinsam die Herausforderungen meistern.
"""

    def test_kanzler_speech_is_detected(self):
        """Verify that 'Friedrich Merz, Bundeskanzler:' speeches are captured."""
        speeches = parse_speeches_from_protocol(self.SAMPLE_PROTOCOL_WITH_KANZLER)

        # Find Merz's speech
        merz_speeches = [s for s in speeches if 'Merz' in s['speaker']]

        assert len(merz_speeches) >= 1, (
            f"Expected at least 1 Merz speech, found {len(merz_speeches)}. "
            f"All speakers: {[s['speaker'] for s in speeches]}"
        )

    def test_kanzler_has_correct_party(self):
        """Verify that Bundeskanzler Merz is attributed to CDU/CSU."""
        speeches = parse_speeches_from_protocol(self.SAMPLE_PROTOCOL_WITH_KANZLER)

        merz_speeches = [s for s in speeches if 'Merz' in s['speaker']]

        assert len(merz_speeches) >= 1, "No Merz speeches found"

        for speech in merz_speeches:
            assert speech['party'] == 'CDU/CSU', (
                f"Expected party 'CDU/CSU', got '{speech['party']}' for {speech['speaker']}"
            )

    def test_kanzler_speech_has_content(self):
        """Verify that Kanzler speech text is properly extracted."""
        speeches = parse_speeches_from_protocol(self.SAMPLE_PROTOCOL_WITH_KANZLER)

        merz_speeches = [s for s in speeches if 'Merz' in s['speaker']]

        assert len(merz_speeches) >= 1, "No Merz speeches found"

        # Check that the speech has substantial content
        speech_text = merz_speeches[0]['text']
        assert len(speech_text) > 100, f"Speech too short: {len(speech_text)} chars"
        assert 'Herausforderungen' in speech_text, "Expected content word not found"

    def test_regular_speakers_still_work(self):
        """Verify that regular 'Name (PARTY):' pattern still works."""
        speeches = parse_speeches_from_protocol(self.SAMPLE_PROTOCOL_WITH_KANZLER)

        # Find AfD and SPD speakers
        afd_speeches = [s for s in speeches if s['party'] == 'AfD']
        spd_speeches = [s for s in speeches if s['party'] == 'SPD']

        assert len(afd_speeches) >= 1, "AfD speaker not found"
        assert len(spd_speeches) >= 1, "SPD speaker not found"

    def test_president_still_skipped(self):
        """Verify that Präsidentin speeches are still skipped (used as boundaries)."""
        speeches = parse_speeches_from_protocol(self.SAMPLE_PROTOCOL_WITH_KANZLER)

        # Presidents should not appear as speakers
        president_speeches = [s for s in speeches if 'Präsident' in s['speaker']]

        assert len(president_speeches) == 0, (
            f"Presidents should be skipped, found: {[s['speaker'] for s in president_speeches]}"
        )


class TestKanzlerFormats:
    """Test various Bundeskanzler name formats."""

    def test_kanzler_with_comma_format(self):
        """Test 'Name, Bundeskanzler:' format."""
        text = """
Präsidentin Julia Klöckner:
Das Wort hat der Bundeskanzler.

Friedrich Merz, Bundeskanzler:
Frau Präsidentin! Meine Damen und Herren! Ich freue mich,
heute vor Ihnen sprechen zu dürfen. Die Lage ist ernst aber
wir werden gemeinsam Lösungen finden. Deutschland ist stark.
"""
        speeches = parse_speeches_from_protocol(text)
        merz_speeches = [s for s in speeches if 'Merz' in s['speaker']]

        assert len(merz_speeches) >= 1, "Comma format Kanzler not detected"
        assert merz_speeches[0]['party'] == 'CDU/CSU'

    def test_kanzlerin_format(self):
        """Test 'Name, Bundeskanzlerin:' format (feminine)."""
        text = """
Präsident Wolfgang Schäuble:
Das Wort hat die Bundeskanzlerin.

Angela Merkel, Bundeskanzlerin:
Herr Präsident! Meine Damen und Herren! Die Lage in Europa
ist angespannt. Wir müssen zusammenstehen und gemeinsam handeln.
Deutschland übernimmt Verantwortung in dieser schweren Zeit.
"""
        speeches = parse_speeches_from_protocol(text)
        merkel_speeches = [s for s in speeches if 'Merkel' in s['speaker']]

        assert len(merkel_speeches) >= 1, "Kanzlerin format not detected"
        assert merkel_speeches[0]['party'] == 'CDU/CSU'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
