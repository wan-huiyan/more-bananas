"""Helpers for volume history, rate validity and verified cleanup records."""
import datetime as dt
from collections import deque
import fcntl
import hashlib
import html
import json
import math
import os
import re
import stat
import time
from pathlib import Path


def derive_rates(previous, current):
    counters = current.get('counters', {})
    rates = {key: None for key in counters}
    reasons = {key: None for key in counters}
    if not previous:
        reason = 'no_previous'
    elif not previous.get('boot') or not current.get('boot'):
        reason = 'missing_boot'
    elif previous['boot'] != current['boot']:
        reason = 'boot_changed'
    else:
        try:
            elapsed = float(current['epoch']) - float(previous['epoch'])
            reason = ('clock_reversed' if not math.isfinite(elapsed) or elapsed <= 0
                      else 'gap' if elapsed > 300 else 'ok')
        except (KeyError, TypeError, ValueError):
            reason = 'invalid_time'
    if reason != 'ok':
        return {'reason': reason, 'rates': rates, 'reasons': {key: reason for key in counters}}
    for key, value in counters.items():
        old = previous.get('counters', {}).get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0 or isinstance(old, bool) or not isinstance(old, int) or old < 0:
            reasons[key] = 'unavailable'
        elif value < old:
            reasons[key] = 'counter_reset'
        else:
            rates[key] = (value - old) / 2**20 * 60 / elapsed
            reasons[key] = 'ok'
    return {'reason': 'ok' if all(x == 'ok' for x in reasons.values()) else 'partial',
            'rates': rates, 'reasons': reasons, 'elapsed_seconds': elapsed}


def normalize_cleanup_receipt(receipt, digest):
    if not isinstance(receipt, dict) or not re.fullmatch(r'[0-9a-f]{64}', digest or ''):
        return None
    status = receipt.get('status')
    if (not isinstance(status, str) or not status.startswith('RESOURCE_END_') or not status.endswith('_COMPLETE')
            or receipt.get('originalExit') != 0 or receipt.get('unconfirmedDeletions') != 0
            or receipt.get('independentVerifierExit', 0) != 0):
        return None
    fields = ('actualDeletedLogicalBytes', 'actualDeletedAllocatedEntryBytes',
              'availableBeforeBytes', 'actorAvailableAfterBytes')
    if any(isinstance(receipt.get(k), bool) or not isinstance(receipt.get(k), int) or receipt[k] < 0 for k in fields):
        return None
    for k in ('newCacheProofLogicalBytes', 'newCacheProofAllocatedEntryBytes'):
        v = receipt.get(k)
        if v is not None and (isinstance(v, bool) or not isinstance(v, int) or v < 0):
            return None
    try:
        stamp = dt.datetime.fromisoformat(receipt['UTC'].replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            return None
    except (KeyError, TypeError, ValueError):
        return None
    return {'receipt_sha256': digest, 'at': stamp.isoformat(),
            'scope': str(receipt.get('scope', 'cleanup'))[:200],
            'admission': str(receipt.get('admission', ''))[:100],
            'deleted_logical_bytes': receipt['actualDeletedLogicalBytes'],
            'deleted_allocated_entry_bytes': receipt['actualDeletedAllocatedEntryBytes'],
            'proof_logical_bytes': receipt.get('newCacheProofLogicalBytes'),
            'proof_allocated_entry_bytes': receipt.get('newCacheProofAllocatedEntryBytes'),
            'available_before_bytes': receipt['availableBeforeBytes'],
            'available_after_bytes': receipt['actorAvailableAfterBytes'],
            'observed_shared_available_delta_bytes': receipt['actorAvailableAfterBytes'] - receipt['availableBeforeBytes']}


def volume_reading(stat):
    unit = stat.f_frsize or stat.f_bsize
    total, free, available = stat.f_blocks * unit, stat.f_bfree * unit, stat.f_bavail * unit
    if not 0 <= available <= free <= total or unit <= 0:
        raise ValueError('invalid filesystem counters')
    return {'total_bytes': total, 'free_bytes': free, 'available_bytes': available}


def import_cleanup_receipt(source, log):
    fd = os.open(os.fspath(source), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 2 * 1024 * 1024:
            raise ValueError('receipt must be a regular file no larger than 2 MiB')
        raw = stream.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('receipt exceeds size limit')
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError('receipt is not valid JSON') from exc
    event = normalize_cleanup_receipt(data, hashlib.sha256(raw).hexdigest())
    if event is None:
        raise ValueError('receipt does not prove a completed cleanup')
    event['receipt_path'] = os.path.abspath(os.fspath(source))
    with open(log, 'a+', encoding='utf-8') as output:
        fcntl.flock(output, fcntl.LOCK_EX)
        output.seek(0)
        for line in output:
            if json.loads(line).get('receipt_sha256') == event['receipt_sha256']:
                return False
        output.seek(0, os.SEEK_END)
        output.write(json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n')
        output.flush()
        os.fsync(output.fileno())
    return True


def render_storage(home):
    def records(name, limit):
        try:
            with open(Path(home) / name, encoding='utf-8') as source:
                lines = deque(source, maxlen=limit)
            values = []
            for line in lines:
                try:
                    value = json.loads(line)
                    if isinstance(value, dict):
                        values.append(value)
                except ValueError:
                    continue
            return values
        except OSError:
            return []
    def gb(value):
        return f'{value / 1e9:.2f} GB' if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else 'unknown'
    rows = records('storage.jsonl', 43200)
    latest = rows[-1] if rows else {}
    if latest.get('status') == 'ok':
        available = gb(latest.get('available_bytes'))
        stamp = html.escape(str(latest.get('at', 'unknown')))
        usage = f'<b>{available} available</b> on the Data volume at {stamp}; filesystem free {gb(latest.get("free_bytes"))}, total {gb(latest.get("total_bytes"))}.'
    else:
        usage = '<b>Data-volume availability is unknown.</b> No successful current sample is available.'
    recent = [row['available_bytes'] for row in rows if row.get('status') == 'ok'
              and isinstance(row.get('epoch'), (int, float)) and 0 <= time.time() - row['epoch'] <= 86400
              and isinstance(row.get('available_bytes'), int)]
    recent_note = f' Lowest observed available in the last 24 hours: {gb(min(recent))}.' if recent else ' No valid samples in the last 24 hours.'
    events = records('cleanup-events.jsonl', 1000)[-5:]
    items = []
    for event in reversed(events):
        scope = html.escape(str(event.get('scope', 'cleanup')))
        stamp = html.escape(str(event.get('at', 'unknown')))
        items.append(f'<li>{stamp} &middot; {scope}: {gb(event.get("deleted_logical_bytes"))} logical and {gb(event.get("deleted_allocated_entry_bytes"))} allocated-entry deleted; proof {gb(event.get("proof_logical_bytes"))} logical and {gb(event.get("proof_allocated_entry_bytes"))} allocated-entry; observed shared available-space change {gb(event.get("observed_shared_available_delta_bytes"))}.</li>')
    details = '<ul>' + ''.join(items) + '</ul>' if items else '<p>No completed cleanup receipts have been imported.</p>'
    return (f'<div class="c en"><h3>Storage history &amp; cleanup evidence</h3><p>{usage}{recent_note}</p>'
            '<p>Available and free are different filesystem counters. Purgeable space is not measured. '
            'Changes in shared APFS availability do not identify a cause or prove exclusive recovery; '
            'disk read/write traffic is not retained file growth. Gaps are unknown.</p>' + details + '</div>')


def record_volume(home, path, boot, epoch=None):
    epoch = time.time() if epoch is None else epoch
    sample = {'at': dt.datetime.fromtimestamp(epoch, dt.timezone.utc).isoformat(),
              'epoch': epoch, 'boot': boot, 'volume': os.fspath(path)}
    try:
        sample.update(volume_reading(os.statvfs(path)))
        sample.update(device=os.stat(path).st_dev, status='ok')
    except (OSError, ValueError):
        sample['status'] = 'unavailable'
    with open(Path(home) / 'storage.jsonl', 'a', encoding='utf-8') as output:
        fcntl.flock(output, fcntl.LOCK_EX)
        output.write(json.dumps(sample, separators=(',', ':')) + '\n')
        output.flush()
    return sample
