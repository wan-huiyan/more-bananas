"""Helpers for volume history, rate validity and verified cleanup records."""


def derive_rates(previous, current):
    return {'reason': 'not_implemented', 'rates': {k: None for k in current['counters']}}


def normalize_cleanup_receipt(receipt, digest):
    return None


def volume_reading(stat):
    return {}
