"""Missing readings, restarted counters and cleanup provenance must stay honest."""
import importlib.util
import ast
import collections
import datetime as dt
from pathlib import Path
import os
import sys
from types import SimpleNamespace
import json
import tempfile
import unittest

path = Path(__file__).resolve().parents[1] / 'skills/more-bananas/app/storage_history.py'
spec = importlib.util.spec_from_file_location('storage_history', path)
storage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(storage)


class IntervalTests(unittest.TestCase):
    def setUp(self):
        self.prev = {'epoch': 1000, 'boot': 'boot-a', 'counters': {'swap_out': 1048576, 'disk_write': 2097152}}
        self.now = {'epoch': 1060, 'boot': 'boot-a', 'counters': {'swap_out': 3145728, 'disk_write': 6291456}}

    def test_rates_use_elapsed_time_and_counter_deltas(self):
        result = storage.derive_rates(self.prev, self.now)
        self.assertEqual(result['reason'], 'ok')
        self.assertEqual(result['rates'], {'swap_out': 2.0, 'disk_write': 4.0})

    def test_first_sample_is_unknown(self):
        result = storage.derive_rates(None, self.now)
        self.assertEqual(result['reason'], 'no_previous')
        self.assertEqual(result['rates'], {'swap_out': None, 'disk_write': None})

    def test_boot_change_is_unknown_even_when_counters_are_higher(self):
        self.now['boot'] = 'boot-b'
        result = storage.derive_rates(self.prev, self.now)
        self.assertEqual(result['reason'], 'boot_changed')
        self.assertEqual(result['rates']['swap_out'], None)

    def test_gap_and_clock_reversal_are_unknown(self):
        for epoch, reason in ((1301, 'gap'), (999, 'clock_reversed')):
            with self.subTest(reason=reason):
                self.now['epoch'] = epoch
                result = storage.derive_rates(self.prev, self.now)
                self.assertEqual(result['reason'], reason)
                self.assertEqual(result['rates']['swap_out'], None)

    def test_one_counter_reset_does_not_erase_other_valid_rates(self):
        self.now['counters']['swap_out'] = 1
        result = storage.derive_rates(self.prev, self.now)
        self.assertIsNone(result['rates']['swap_out'])
        self.assertEqual(result['rates']['disk_write'], 4.0)


class EvidenceTests(unittest.TestCase):
    def test_volume_free_and_user_available_are_distinct(self):
        stat = SimpleNamespace(f_frsize=4096, f_blocks=100, f_bfree=30, f_bavail=20)
        self.assertEqual(storage.volume_reading(stat), {'total_bytes': 409600, 'free_bytes': 122880, 'available_bytes': 81920})

    def test_completed_receipt_keeps_cleanup_and_shared_delta_separate(self):
        receipt = {'status': 'RESOURCE_END_EXAMPLE_COMPLETE', 'UTC': '2026-11-06T00:14:55+00:00', 'scope': 'example', 'admission': 'example-admission', 'originalExit': 0, 'unconfirmedDeletions': 0, 'actualDeletedLogicalBytes': 100, 'actualDeletedAllocatedEntryBytes': 120, 'newCacheProofLogicalBytes': 4, 'newCacheProofAllocatedEntryBytes': 8, 'availableBeforeBytes': 1000, 'actorAvailableAfterBytes': 1080}
        event = storage.normalize_cleanup_receipt(receipt, 'a' * 64)
        self.assertIsNotNone(event)
        self.assertEqual(event['deleted_logical_bytes'], 100)
        self.assertEqual(event['deleted_allocated_entry_bytes'], 120)
        self.assertEqual(event['proof_allocated_entry_bytes'], 8)
        self.assertEqual(event['observed_shared_available_delta_bytes'], 80)

    def test_unentered_or_unconfirmed_receipts_never_become_cleanup_events(self):
        self.assertIsNone(storage.normalize_cleanup_receipt({'runtimeEntered': False, 'plannedLogicalBytes': 100}, 'b' * 64))
        self.assertIsNone(storage.normalize_cleanup_receipt({'status': 'RESOURCE_END_EXAMPLE_COMPLETE', 'unconfirmedDeletions': 1}, 'c' * 64))

    def test_import_is_idempotent_and_keeps_original_receipt(self):
        receipt = {'status': 'RESOURCE_END_EXAMPLE_COMPLETE', 'UTC': '2026-11-06T00:14:55+00:00', 'scope': 'example', 'originalExit': 0, 'unconfirmedDeletions': 0, 'actualDeletedLogicalBytes': 100, 'actualDeletedAllocatedEntryBytes': 120, 'availableBeforeBytes': 1000, 'actorAvailableAfterBytes': 1080}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'receipt.json'
            log = Path(directory) / 'cleanup.jsonl'
            original = json.dumps(receipt)
            source.write_text(original)
            self.assertTrue(storage.import_cleanup_receipt(source, log))
            self.assertFalse(storage.import_cleanup_receipt(source, log))
            self.assertEqual(source.read_text(), original)
            events = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]['deleted_logical_bytes'], 100)

    def test_import_refuses_unentered_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'receipt.json'
            log = Path(directory) / 'cleanup.jsonl'
            source.write_text('{"runtimeEntered": false, "plannedLogicalBytes": 999}')
            with self.assertRaises(ValueError):
                storage.import_cleanup_receipt(source, log)
            self.assertFalse(log.exists())

    def test_dashboard_separates_cleanup_from_shared_space_movement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'storage.jsonl').write_text(json.dumps({'at': '2026-11-10T14:00:00+00:00', 'status': 'ok', 'available_bytes': 2000000000, 'free_bytes': 3000000000, 'total_bytes': 10000000000}) + '\n')
            event = {'at': '2026-11-10T13:00:00+00:00', 'scope': 'sample', 'deleted_logical_bytes': 1000000000, 'deleted_allocated_entry_bytes': 1200000000, 'proof_logical_bytes': 100000000, 'proof_allocated_entry_bytes': 200000000, 'observed_shared_available_delta_bytes': 800000000}
            (root / 'cleanup-events.jsonl').write_text(json.dumps(event) + '\n')
            page = storage.render_storage(root)
            self.assertIn('2.00 GB', page)
            self.assertIn('1.00 GB', page)
            self.assertIn('1.20 GB', page)
            self.assertIn('0.80 GB', page)
            self.assertIn('shared', page.lower())
            self.assertIn('0.20 GB', page)
            self.assertNotIn('recovered 1.20', page.lower())

    def test_volume_sampling_records_real_values_and_missing_path_as_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            storage.record_volume(root, root, 'boot-a', epoch=1000)
            storage.record_volume(root, root / 'does-not-exist', 'boot-a', epoch=1060)
            self.assertTrue((root / 'storage.jsonl').exists())
            first, missing = [json.loads(line) for line in (root / 'storage.jsonl').read_text().splitlines()]
            self.assertEqual(first['status'], 'ok')
            self.assertEqual(first['boot'], 'boot-a')
            self.assertGreater(first['total_bytes'], 0)
            self.assertEqual(missing['status'], 'unavailable')
            self.assertNotIn('available_bytes', missing)


class MissingRateReportTests(unittest.TestCase):
    def page_data(self, directory):
        source = path.with_name('memlog.py')
        module = ast.parse(source.read_text())
        function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'page_data')
        namespace = {'collections': collections, 'dt': dt, 'os': os}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
        return namespace['page_data'](directory)

    def test_unknown_swap_rate_does_not_become_zero_or_break_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'mem.csv').write_text('2024-01-01 12:00,12,1,1,1,1\n' * 60)
            (root / 'live.csv').write_text('2024-01-01 12:00,,,2,3,4\n2024-01-01 12:01,2.5,1,2,3,4\n')
            try:
                result = self.page_data(directory)
            except ValueError:
                self.fail('an unknown interval must not break the report')
            self.assertEqual(result['LO'], [2.5])
            self.assertEqual(result['LT'], ['2024-01-01 12:01'])

    def test_full_report_and_buddy_handle_no_valid_swap_rate(self):
        sys.path.insert(0, str(path.parent))
        try:
            import report
            import buddy
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
                (root / 'mem.csv').write_text((stamp + ',12,1,1,1,1\n') * 60)
                (root / 'live.csv').write_text(stamp + ',,,2,3,4\n')
                (root / 'cpu.csv').write_text(stamp + ',5,1,8\n')
                v = self.page_data(directory)
                v.update(HOME=directory, stamp=stamp, TOTAL_GB=24, out_mb=None, cfg={}, terms=1, mood='unknown',
                         tone='#8793a9', fav='', by_group={}, now_d={}, cores=8, load1=1,
                         swapped_total_gb=0, comp_gb=2, wired_gb=3, squeezed_gb=4)
                page = buddy.theme(report.render(v), 'unknown', [])
                self.assertIn('Swap rate unavailable', page)
                self.assertIn('desired concurrent work is not yet sized', page)
                self.assertIn('Storage history &amp; cleanup evidence', page)
        finally:
            sys.path.pop(0)
