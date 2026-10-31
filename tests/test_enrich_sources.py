import unittest

from enrich_sources import transcript_text


class TranscriptExtractionTests(unittest.TestCase):
    def test_scoped_nested_divs_and_entities(self):
        body = 'Texte de conférence &amp; source. ' * 60
        html = ('<div class>Navigation</div><div class="su-media-transcript">'
                '<p>' + body + '</p><div><p>Conclusion.</p></div></div>'
                '<div>Recommandations hors transcription</div>')
        text = transcript_text(html)
        self.assertIn('conférence & source', text)
        self.assertIn('Conclusion.', text)
        self.assertNotIn('Navigation', text)
        self.assertNotIn('Recommandations', text)

    def test_gsb_selects_full_transcript_not_summary(self):
        html = ('<div class="description">Résumé seulement</div>'
                '<div class="description"><h2>Full Transcript</h2><p>'
                + 'Intervention complète. ' * 90 + '</p></div>')
        text = transcript_text(html, gsb=True)
        self.assertNotIn('Résumé', text)
        self.assertIn('Intervention complète', text)

    def test_missing_or_short_transcript_rejected(self):
        with self.assertRaises(ValueError):
            transcript_text('<div class="su-media-transcript">Résumé court</div>')
