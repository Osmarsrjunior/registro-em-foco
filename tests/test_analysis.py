import csv
import hashlib
import json
import math
import unittest
from pathlib import Path
from src.analysis import missing_events, relative_change, scenario

ROOT=Path(__file__).resolve().parents[1]


class AnalysisTests(unittest.TestCase):
    def test_percentage_units(self):
        self.assertEqual(missing_events(1000,2),20)
        self.assertEqual(missing_events(1000,0),0)
        self.assertEqual(missing_events(1000,100),1000)

    def test_invalid_rates_and_totals(self):
        for total,rate in [(-1,2),(1,-1),(1,101),(math.nan,2),(1,math.inf)]:
            with self.assertRaises(ValueError):missing_events(total,rate)

    def test_relative_and_absolute_change_are_distinct(self):
        self.assertAlmostEqual(relative_change(2,1),-50)
        self.assertIsNone(relative_change(0,1))

    def test_scenario_boundaries(self):
        self.assertEqual(scenario(2,0,3),[2]*4)
        self.assertEqual(scenario(2,100,3),[2,0,0,0])
        self.assertAlmostEqual(scenario(.9548,10,5)[-1],.563799852)
        for args in [(2,-1,3),(2,10,0),(2,10,11),(2,10,1.5)]:
            with self.assertRaises(ValueError):scenario(*args)


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT/'data/processed/territories.csv').open(encoding='utf-8') as f:
            cls.rows=list(csv.DictReader(f))

    def test_raw_hashes(self):
        for source in json.loads((ROOT/'data/sources.json').read_text(encoding='utf-8')):
            self.assertEqual(hashlib.sha256((ROOT/source['file']).read_bytes()).hexdigest(),source['sha256'])

    def test_unique_keys_and_state_coverage(self):
        self.assertEqual(len(self.rows),len({(r['year'],r['code']) for r in self.rows}))
        for year in ['2022','2023','2024']:
            self.assertEqual(sum(r['year']==year and r['level']=='state' for r in self.rows),27)

    def test_country_totals_include_unknown_residence(self):
        for year in ['2022','2023','2024']:
            rows=[r for r in self.rows if r['year']==year]
            summed=sum(float(r['estimated_births']) for r in rows if r['level'] in ['state','unknown'])
            br=next(float(r['estimated_births']) for r in rows if r['code']=='BR')
            self.assertLessEqual(abs(summed-br),.03)

    def test_derived_volumes_and_bounds(self):
        for r in self.rows:
            rate=float(r['rate']);total=float(r['estimated_births'])
            self.assertTrue(0<=rate<=100)
            self.assertAlmostEqual(float(r['estimated_missing']),total*rate/100,places=5)

    def test_missing_municipalities_not_converted_to_zero(self):
        with (ROOT/'data/processed/municipalities_2024.csv').open(encoding='utf-8') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),5570)
        self.assertEqual(len({r['code'] for r in rows}),5570)
        missing=[r for r in rows if r['rate']=='']
        self.assertEqual({r['code'] for r in missing},{'3532157','4212601','5201207'})
        self.assertTrue(all(r['estimated_missing']=='' for r in missing))

    def test_headline_results_against_published_cells(self):
        br=next(r for r in self.rows if r['year']=='2024' and r['code']=='BR')
        self.assertEqual(float(br['rate']),.9548)
        rr=next(r for r in self.rows if r['year']=='2024' and r['code']=='RR')
        self.assertEqual(float(rr['rate']),13.8634)
        states=[r for r in self.rows if r['year']=='2024' and r['level']=='state']
        self.assertEqual(max(states,key=lambda r:float(r['estimated_missing']))['code'],'PA')


if __name__=='__main__':unittest.main()
