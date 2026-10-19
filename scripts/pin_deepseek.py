"""Pin official tokenizer assets and compare identity without encoding study text."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def main(v3, r1, output):
    records = []
    for key, repo, revision, licenses in [
        ('deepseek-v3', 'deepseek-ai/DeepSeek-V3', v3, ['LICENSE-CODE', 'LICENSE-MODEL']),
        ('deepseek-r1', 'deepseek-ai/DeepSeek-R1', r1, ['LICENSE'])]:
        assert re.fullmatch('[0-9a-f]{40}', revision)
        cache = ROOT/'.cache/tokenizers'/key/revision
        cache.mkdir(parents=True, exist_ok=True)
        assets = []
        for name in ['tokenizer.json', 'tokenizer_config.json', 'README.md'] + licenses:
            path = cache/name
            url = f'https://huggingface.co/{repo}/resolve/{revision}/{name}'
            if not path.exists():
                partial = path.with_suffix('.download')
                subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location', '--retry', '2', '--max-time', '120', '--output', str(partial), url], check=True)
                partial.replace(path)
            assets.append({'filename': name, 'url': url, 'sha256': sha(path), 'bytes': path.stat().st_size})
        tokenizer = Tokenizer.from_file(str(cache/'tokenizer.json'))
        definition = json.loads(tokenizer.to_str())
        config = json.loads((cache/'tokenizer_config.json').read_text())
        assert not definition.get('truncation') and not definition.get('padding') and not definition['model'].get('dropout')
        record = {'model_key': key, 'repository': repo, 'revision': revision,
                  'cache_directory': str(cache.relative_to(ROOT)), 'assets': assets,
                  'runtime_model_type': type(tokenizer.model).__name__,
                  'base_vocab_entries': tokenizer.get_vocab_size(False),
                  'effective_vocab_entries': tokenizer.get_vocab_size(True),
                  'definition_sha256': fingerprint(definition),
                  'components_sha256': {k: fingerprint(definition.get(k)) for k in ['model', 'normalizer', 'pre_tokenizer', 'decoder', 'post_processor', 'added_tokens']},
                  'tokenizer_config_sha256': sha(cache/'tokenizer_config.json'),
                  'chat_template_sha256': fingerprint(config.get('chat_template')),
                  'add_special_tokens': False,
                  'selection_reason': 'Official full-model DeepSeek V3/R1 coverage; selected before counts, excluding distilled variants.',
                  'asset_use': 'Tokenizer/config and source notices only; kept in ignored local cache. No weights or repository code executed.'}
        dest = ROOT/'config'/f'{key}-tokenizer.lock.json'
        if dest.exists():
            assert json.loads(dest.read_text()) == record
        else:
            dest.write_text(json.dumps(record, indent=2)+'\n')
        records.append(record)
    a, b = records
    report = {'repositories': [{k: r[k] for k in ['model_key', 'repository', 'revision', 'runtime_model_type', 'base_vocab_entries', 'effective_vocab_entries', 'definition_sha256', 'components_sha256', 'chat_template_sha256']} for r in records],
              'tokenizer_json_byte_identical': a['assets'][0]['sha256'] == b['assets'][0]['sha256'],
              'serialized_definition_identical': a['definition_sha256'] == b['definition_sha256'],
              'component_matches': {k: a['components_sha256'][k] == b['components_sha256'][k] for k in a['components_sha256']},
              'tokenizer_config_identical': a['tokenizer_config_sha256'] == b['tokenizer_config_sha256'],
              'chat_template_identical': a['chat_template_sha256'] == b['chat_template_sha256'],
              'study_inputs_encoded': 0, 'script_sha256': sha(Path(__file__))}
    assert not output.exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'repositories'}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--v3', required=True); p.add_argument('--r1', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); main(a.v3, a.r1, a.output)
