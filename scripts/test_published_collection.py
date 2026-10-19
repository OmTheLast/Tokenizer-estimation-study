"""Focused boundary and data-integrity checks for the collection step."""
import unittest
from decimal import Decimal
from collect_published_text import paragraphs, strict_json, features, git_blob, screening, grams
from screen_published_passages import outside_links


class CollectionChecks(unittest.TestCase):
    def test_utf8_crlf_offsets_preserve_exact_bytes(self):
        raw = 'தமிழ் first\r\nsecond\r\n\r\nnext\n'.encode()
        spans = paragraphs(raw)
        self.assertEqual([raw[a:b].decode() for a, b, _ in spans],
                         ['தமிழ் first\r\nsecond\r\n', 'next\n'])
        self.assertTrue(all(reason is None for _, _, reason in spans))

    def test_fence_context_survives_blank_lines_and_short_markers(self):
        raw = b'````python\ncode\n\n```\n\nmore code\n````\n\nActual prose.\n'
        spans = paragraphs(raw)
        self.assertTrue(all(reason == 'fenced_code' for _, _, reason in spans[:-1]))
        self.assertIsNone(spans[-1][2])

    def test_rst_directives_literals_and_resumption(self):
        raw = b'.. code-block:: python\n\n   x = 1\n\n   y = 2\n\nProse::\n\n   example\n\nNormal narrative.\n'
        spans = paragraphs(raw, rst=True)
        self.assertEqual([r for _, _, r in spans], ['rst_directive_or_comment',
            'rst_directive_or_literal_body', 'rst_directive_or_literal_body',
            None, 'rst_directive_or_literal_body', None])

    def test_frontmatter_and_rst_heading(self):
        self.assertEqual(paragraphs(b'---\nname: value\n\nkey: value\n---\n\nProse\n')[0][2], 'frontmatter')
        self.assertEqual(paragraphs(b'Title\n=====\n\nProse\n', True)[0][2], 'heading')

    def test_strict_json_precision_and_rejections(self):
        obj = strict_json('{"large":123456789012345678901,"decimal":0.1234567890123456789}')
        self.assertEqual(obj['large'], 123456789012345678901)
        self.assertEqual(obj['decimal'], Decimal('0.1234567890123456789'))
        for text in ('{"a":1,"a":2}', '{"a":{"b":1,"b":2}}', '{"x":NaN}', '[]', '{"x":1,}'):
            with self.assertRaises(ValueError):
                strict_json(text)

    def test_length_units_and_duplicate_screen(self):
        f = features('a😀')
        self.assertEqual((f['codepoints'], f['utf8_bytes'], f['utf16_units']), (2, 5, 3))
        self.assertEqual(screening(' e\u0301\n x  '), screening('é x'))
        self.assertEqual(grams('abcdef'), {'abcde', 'bcdef'})
        self.assertEqual(git_blob(b''), 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')

    def test_url_only_english_is_not_narrative_english(self):
        self.assertEqual(outside_links('[தமிழ்](https://example.com/english) 中文'), 'தமிழ் 中文')
        self.assertEqual(outside_links('![English caption](image.png) தமிழ்'), ' தமிழ்')

    def test_visible_technical_link_label_remains(self):
        self.assertEqual(outside_links('[Python](https://python.org) தமிழ் `data`'), 'Python தமிழ் `data`')


if __name__ == '__main__':
    unittest.main()
