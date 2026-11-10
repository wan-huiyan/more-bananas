"""A processor estimate that exceeds the catalog must not hide useful options."""
import datetime as dt
from pathlib import Path
import sys
import tempfile
import unittest

import test_storage_history as helpers

APP = Path(__file__).resolve().parents[1] / 'skills/more-bananas/app'
sys.path.insert(0, str(APP))
import report


def report_for_workload(memory, swap, load):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / 'icon').mkdir()
        (root / 'icon/fav64.b64').write_text('AA==')
        now = dt.datetime.now().replace(second=0, microsecond=0)
        times = [(now - dt.timedelta(minutes=119-i)).strftime('%Y-%m-%d %H:%M') for i in range(120)]
        (root / 'mem.csv').write_text(''.join(f'{t},{memory},{swap},1,1,1\n' for t in times))
        (root / 'live.csv').write_text(''.join(f'{t},0,0,2,3,4\n' for t in times))
        (root / 'cpu.csv').write_text(''.join(f'{t},5,{load},10\n' for t in times))
        values = helpers.MissingRateReportTests().page_data(directory)
        values.update(HOME=directory, stamp=times[-1], TOTAL_GB=24, out_mb=0, cfg={}, terms=1,
                      mood='calm', tone='#34d399', fav='', by_group={}, now_d={}, cores=10,
                      load1=load, swapped_total_gb=0, comp_gb=2, wired_gb=3, squeezed_gb=4,
                      hours='all')
        return report.render(values)


class RecommendationFallbackTests(unittest.TestCase):
    def test_excessive_load_still_shows_closest_compatible_mac_and_limit(self):
        page = report_for_workload(17, 15, 25)
        self.assertIn('Consider <em>MacBook Pro M5 Pro</em>', page)
        self.assertIn('48 GB memory, 18-core CPU', page)
        self.assertIn('0.0% of recorded load readings', page)
        self.assertIn('below the 90% processor-screening target', page)
        self.assertIn('64 GB', page)
        self.assertIn('not yet measured', page)
        self.assertNotIn('No listed MacBook fits every estimate', page)

    def test_normal_candidate_still_wins_when_cpu_screen_is_met(self):
        page = report_for_workload(17, 15, 14)
        self.assertIn('48 GB memory, 15-core CPU', page)
        self.assertNotIn('below the 90% processor-screening target', page)

    def test_does_not_claim_a_model_meets_memory_beyond_catalog(self):
        page = report_for_workload(120, 20, 25)
        self.assertIn('No listed MacBook fits every estimate', page)
        self.assertNotIn('below the 90% processor-screening target', page)
