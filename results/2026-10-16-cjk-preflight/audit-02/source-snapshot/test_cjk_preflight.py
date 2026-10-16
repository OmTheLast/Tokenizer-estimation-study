import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_cjk_candidates import parse_conllu,norm,near,source_group,Union
class PreflightTests(unittest.TestCase):
    def test_exact_original_text_and_document_persistence(self):
        source='# newdoc id = article-a\n# sent_id = a1\n# text = two  spaces\n1\ttwo\n\n# sent_id = a2\n# text = last sentence\n1\tlast\n'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data.conllu';p.write_text(source);records=parse_conllu(p)
        self.assertEqual([r['doc'] for r in records],['article-a','article-a'])
        self.assertEqual(records[0]['text'],'two  spaces')
    def test_normalization_and_near_rule(self):
        self.assertEqual(norm(' e\u0301\t x\n'),'é x')
        self.assertTrue(near('short','short'))
        self.assertFalse(near('short','shOrt'))
        s=''.join(chr(0x4e00+i) for i in range(100))
        self.assertTrue(near(s,s+'x'))
        self.assertFalse(near(s,'z'*100))
    def test_source_groups_not_sentence_ids(self):
        self.assertIsNone(source_group({'code':'ja_gsd','id':'train-s1'}))
        self.assertEqual(source_group({'code':'yue_hk','id':'410'}),'yue_hk:film1')
        self.assertEqual(source_group({'code':'yue_hk','id':'411'}),'yue_hk:film2')
    def test_union_transitive(self):
        u=Union(4);u.join(0,1);u.join(1,2)
        self.assertEqual(u.find(0),u.find(2));self.assertNotEqual(u.find(0),u.find(3))
if __name__=='__main__':unittest.main()
