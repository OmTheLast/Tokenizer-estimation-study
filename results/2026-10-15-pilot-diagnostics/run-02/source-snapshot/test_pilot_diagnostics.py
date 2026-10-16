"""Independent small examples for error signs, thresholds, quantiles and ties."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_pilot_errors import metrics, band, outliers, group_result

class DiagnosticsTests(unittest.TestCase):
    def test_known_errors_and_strict_threshold(self):
        rows=[{'token_count':100,'estimate':p} for p in [79,80,100,120]]
        m=metrics(rows,'estimate')
        self.assertEqual(m['undercount_fraction'],.5)
        self.assertEqual(m['under_by_more_than_20_percent_fraction'],.25)
        self.assertEqual(m['within_20_percent_fraction'],.75)
        self.assertEqual(m['median_absolute_percent_error'],20)
        self.assertAlmostEqual(m['p95_absolute_percent_error'],20.85)
        self.assertEqual(m['mean_token_shortfall_all_rows'],10.25)
        self.assertEqual(m['max_token_shortfall'],21)
    def test_empty_and_boundaries(self):
        self.assertIsNone(metrics([],'estimate')['p95_absolute_percent_error'])
        self.assertEqual([band(n) for n in [49,50,99,100,199,200]],['[0,50)','[50,100)','[50,100)','[100,200)','[100,200)','[200,infinity)'])
    def test_outlier_ranks_and_ties(self):
        rows=[{'language':'a','sentence_id':i,'token_count':n,'estimate':p} for i,n,p in [('2',10,5),('10',10,5),('3',100,80),('4',1,2)]]
        o=outliers(rows,'estimate')
        self.assertEqual([r['sentence_id'] for r in o['largest_percentage_undercounts']],['10','2','3'])
        self.assertEqual(o['largest_token_shortfalls'][0]['sentence_id'],'3')
    def test_paired_difference(self):
        r=[{'language':'a','token_count':100,'estimate':90,'old_estimate':50}]
        g=group_result(r,{'localmind':'estimate','legacy_utf16_div_3_5':'old_estimate'})
        self.assertEqual(g['localmind_minus_legacy']['median_absolute_percent_error'],-40)
        self.assertEqual(g['localmind_minus_legacy']['min_signed_percent_error'],40)

if __name__=='__main__':unittest.main()
