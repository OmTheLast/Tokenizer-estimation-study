import {commit, estimator, fixtures} from './localmind_source.mjs';
const keys = [...Object.keys(estimator.TOKEN_PROFILE_BY_MODEL), 'unknown-model'];
const predictions = text => Object.fromEntries(keys.map(k => [k, estimator.countTokens(text, k)]));
const boundaries = [0, 32, 65, 90, 97, 122, 128, 0x24f, 0x400, 0x52f, 0x600, 0x6ff,
  0x900, 0x97f, 0x980, 0x9ff, 0xa00, 0xa7f, 0xa80, 0xaff, 0xb00, 0xb7f, 0xb80, 0xbff,
  0xc00, 0xc7f, 0xc80, 0xcff, 0xd00, 0xd7f, 0x3040, 0x30ff, 0x3400, 0x4dbf,
  0x4e00, 0x9fff, 0xac00, 0xd7af, 0xd800, 0xdfff, 0xffff, 0x10000, 0x10ffff];
const points = [...new Set(boundaries.flatMap(n => [n - 1, n, n + 1]).filter(n => n >= 0 && n <= 0x10ffff))];
const cases = [
  {name: 'null', text: null}, {name: 'empty', text: ''},
  {name: 'spaces', text: ' \t\n\r'}, {name: 'emoji-joiners', text: '🙂👨‍👩‍👧‍👦🇮🇳'},
  {name: 'combining', text: 'e\u0301 é कि ಕಿ 한 한'},
  {name: 'unpaired-surrogates', text: '\ud800x\udfff'},
  {name: 'surrogate-pair', text: '\ud83d\ude42'},
  ...points.map(cp => ({name: `boundary-${cp}`, text: String.fromCodePoint(cp)})),
  ...[1, 2, 3, 10, 100, 1000].map(n => ({name: `rounding-${n}`, text: 'a क 🙂 .'.repeat(n)})),
];
process.stdout.write(JSON.stringify({localmind_commit: commit,
  profiles: {classes: estimator.TOKEN_CLASSES, weights: estimator.TOKEN_WEIGHTS, model_profiles: estimator.TOKEN_PROFILE_BY_MODEL},
  fixtures: fixtures.map(s => ({...s, estimates: predictions(s.text)})),
  classification: points.map(cp => ({code_point: cp, class_index: estimator.tokenClassIndex(cp)})),
  edge_cases: cases.map(c => ({...c, estimates: predictions(c.text)}))}, null, 2) + '\n');
