"""Input-contract tests using artificial records only; no dataset/network access."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import flores_pilot_data as data
from pilot_features import features, CLASSES


class PilotInputs(unittest.TestCase):
    def test_unicode_units_and_class_sum(self):
        row = features('A🙂कि')
        self.assertEqual(row['characters'], 4)
        self.assertEqual(row['utf16_units'], 5)
        self.assertEqual(row['utf8_bytes'], 11)
        self.assertEqual(sum(row['class_' + name] for name in CLASSES), 4)
        self.assertEqual(row['combining_mark_characters'], 1)

    def test_parallel_id_selection_is_frozen_before_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config').mkdir()
            plan = {'dataset': 'synthetic-test-only', 'revision': 'test', 'split': 'dev', 'sample_count': 4,
                    'selection_salt': 'test-seed', 'languages': [{'code': code, 'label': code, 'group': 'Test'} for code in ['a', 'b']]}
            plan_path = root / 'config/plan.json'
            plan_path.write_text(json.dumps(plan))
            files = {}
            for language in ['a', 'b']:
                ids = list(range(8)) + ([999] if language == 'a' else [])
                if language == 'b':
                    ids.reverse()
                path = root / (language + '.jsonl')
                path.write_text('\n'.join(json.dumps({'id': str(i), 'text': f'artificial {language} record {i}', 'split': 'dev'}) for i in ids))
                files['dev/' + language + '.jsonl'] = str(path)
            def fake_download(**kwargs):
                self.assertTrue(kwargs['filename'].startswith('dev/'))
                self.assertIs(kwargs['token'], False)
                return files[kwargs['filename']]
            with patch.object(data, 'ROOT', root), patch.object(data, 'PLAN', plan_path), patch.object(data, 'get_token', return_value=None), patch.object(data, 'hf_hub_download', side_effect=fake_download):
                texts, source = data.load_pilot(lambda _: None)
                second, second_source = data.load_pilot(lambda _: None)
                self.assertEqual(texts, second)
                self.assertEqual(source, second_source)
                self.assertEqual(source['selection']['common_ids_available'], 8)
                self.assertNotIn('999', source['selection']['ids_in_selection_order'])
                self.assertEqual([t['sentence_id'] for t in texts if t['language'] == 'a'], [t['sentence_id'] for t in texts if t['language'] == 'b'])
                self.assertTrue((root / 'config/flores-pilot-sample.json').exists())
                plan['selection_salt'] = 'different'
                plan_path.write_text(json.dumps(plan))
                with self.assertRaisesRegex(ValueError, 'Refusing to replace frozen input'):
                    data.load_pilot(lambda _: None)

    def test_access_errors_do_not_echo_exception_secrets(self):
        with patch.object(data, 'get_token', return_value='pretend-secret'), patch.object(data, 'hf_hub_download', side_effect=RuntimeError('pretend-secret')):
            with self.assertRaises(RuntimeError) as error:
                data.load_pilot(lambda _: None)
        self.assertNotIn('pretend-secret', str(error.exception))
        self.assertIn('Dataset access failed', str(error.exception))


if __name__ == '__main__':
    unittest.main()
