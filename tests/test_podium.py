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


def page_for(apps, cpu_apps=None, tools=None, keep=None):
    """Render the page from per-app memory (and optionally processor and Claude tool) readings."""
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
        if tools:
            (root / 'tools.csv').write_text(''.join(f'{t},session-a,{job},{x}\n' for t in times for job, x in tools.items()))
        values = helpers.MissingRateReportTests().page_data(directory)
        values.update(HOME=directory, stamp=times[-1], TOTAL_GB=24, out_mb=0, cfg={}, terms=1,
                      mood='calm', tone='#34d399', fav='', by_group={}, now_d={}, cores=10,
                      load1=4, swapped_total_gb=0, comp_gb=2, wired_gb=3, squeezed_gb=4, hours='all')
        page = report.render(values)
        if keep is not None:
            keep.update(values)
        return page


def podium_for(apps, cpu_apps=None, tools=None):
    """The page's podium data."""
    page = page_for(apps, cpu_apps, tools)
    assert 'id=podium-host' in page, 'the podium card is missing from the page'
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


    def test_claude_tools_place_by_kind_and_keep_the_lists_totals(self):
        # The list lumps Claude's tools into two rows; the podium splits them by kind, scaled to those rows' totals.
        pod = podium_for({'Browsers Claude drives': 2.9, 'Tools Claude starts': 1.0, 'macOS system': 2.4, 'Slack': 0.4},
                         tools={'Chrome opened by check_dashboard.py': 2.0, 'build_page.py': 0.4, 'check_dashboard.py': 0.1})
        top = dict(pod['wins']['now']['mem'])
        self.assertEqual(list(top), ["Claude's test browsers", 'macOS system', "Claude's build scripts"])
        self.assertEqual(top["Claude's test browsers"], 2.9)
        self.assertEqual(top["Claude's build scripts"], 0.8)
        for win in pod['wins'].values():
            self.assertFalse({'Browsers Claude drives', 'Tools Claude starts'} & {g for g, _ in win['mem']})

    def test_without_a_tool_log_the_lumped_rows_still_place_under_claudes_name(self):
        pod = podium_for({'Browsers Claude drives': 2.9, 'Tools Claude starts': 1.0, 'macOS system': 0.4})
        self.assertEqual([g for g, _ in pod['wins']['now']['mem']], ["Claude's test browsers", "Claude's other tools", 'macOS system'])


    def test_the_list_shows_claudes_tools_by_kind_not_lumped(self):
        page = page_for({'Browsers Claude drives': 2.9, 'Tools Claude starts': 1.0, 'macOS system': 2.4},
                        tools={'Chrome opened by check_dashboard.py': 2.0, 'build_page.py': 0.4, 'check_dashboard.py': 0.1})
        rows = re.findall(r'<div class="row ur"[^>]*><span>([^<]+)</span>', page)
        self.assertIn('Claude&#x27;s test browsers', rows)
        self.assertIn('Claude&#x27;s build scripts', rows)
        self.assertNotIn('Browsers Claude drives', rows)
        self.assertNotIn('Tools Claude starts', rows)
        self.assertIn('build_page.py', page)        # each kind opens into its scripts


    def test_the_yard_gets_this_minutes_split_by_kind(self):
        values = {}
        page_for({'Browsers Claude drives': 2.9, 'Tools Claude starts': 1.0, 'macOS system': 2.4},
                 tools={'Chrome opened by check_dashboard.py': 2.0, 'build_page.py': 0.4, 'check_dashboard.py': 0.1}, keep=values)
        split = values['yard_split']
        self.assertEqual(split["Claude's test browsers"]['gb'], 2.9)
        self.assertEqual(split["Claude's build scripts"]['gb'], 0.8)
        self.assertNotIn('Browsers Claude drives', split)


if __name__ == '__main__':
    unittest.main()
