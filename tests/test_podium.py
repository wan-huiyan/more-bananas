"""The What uses the Mac podium ranks the same app groups as the list beside it."""
import datetime as dt
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

import test_storage_history as helpers

APP = Path(__file__).resolve().parents[1] / 'skills/more-bananas/app'
sys.path.insert(0, str(APP))
import report


def podium_for(apps, cpu_apps=None):
    """Render the page from per-app memory (and optionally processor) readings, and return its podium data."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / 'icon').mkdir()
        (root / 'icon/fav64.b64').write_text('AA==')
        now = dt.datetime.now().replace(second=0, microsecond=0)
        times = [(now - dt.timedelta(minutes=59 - i)).strftime('%Y-%m-%d %H:%M') for i in range(60)]
        (root / 'mem.csv').write_text(''.join(f'{t},12,1,1,1,1\n' for t in times))
        (root / 'live.csv').write_text(''.join(f'{t},0,0,2,3,4\n' for t in times))
        (root / 'cpu.csv').write_text(''.join(f'{t},5,4,10\n' for t in times))
        (root / 'apps.csv').write_text(''.join(f'{t},{g},{x}\n' for t in times for g, x in apps.items()))
        if cpu_apps:
            (root / 'cpu_apps.csv').write_text(''.join(f'{t},{g},{x}\n' for t in times for g, x in cpu_apps.items()))
        values = helpers.MissingRateReportTests().page_data(directory)
        values.update(HOME=directory, stamp=times[-1], TOTAL_GB=24, out_mb=0, cfg={}, terms=1,
                      mood='calm', tone='#34d399', fav='', by_group={}, now_d={}, cores=10,
                      load1=4, swapped_total_gb=0, comp_gb=2, wired_gb=3, squeezed_gb=4, hours='all')
        page = report.render(values)
    found = re.search(r'<script type=application/json id=podium-data>(.*?)</script>', page)
    return json.loads(found.group(1))


class PodiumTests(unittest.TestCase):
    def test_top_three_by_memory_in_list_order_without_the_catch_all(self):
        pod = podium_for({'Other apps': 9.0, 'Chrome (incl. Meet)': 3.5, 'Slack': 0.4, 'macOS system': 2.2, 'Claude desktop app': 1.1})
        self.assertEqual([g for g, _ in pod['wins']['now']['mem']], ['Chrome (incl. Meet)', 'macOS system', 'Claude desktop app'])
        self.assertEqual(pod['wins']['d7']['mem'][0], ['Chrome (incl. Meet)', 3.5])
        for win in pod['wins'].values():
            self.assertNotIn('Other apps', [g for g, _ in win['mem']])

    def test_no_processor_podium_without_per_app_processor_readings(self):
        pod = podium_for({'Chrome (incl. Meet)': 3.5})
        self.assertEqual(pod['wins']['now']['cpu'], [])
        self.assertEqual(pod['first'], 'mem')

    def test_processor_podium_ranks_share_of_the_cores_and_drops_tiny_ones(self):
        pod = podium_for({'Chrome (incl. Meet)': 3.5}, {'Google Drive': 14, 'macOS system': 13, 'Safari': 0.2, 'Other apps': 40})
        self.assertEqual(pod['wins']['now']['cpu'], [['Google Drive', 14], ['macOS system', 13]])


if __name__ == '__main__':
    unittest.main()
