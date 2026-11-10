"""Helpers for volume history, rate validity and verified cleanup records."""
import datetime as dt
import math
import re


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
