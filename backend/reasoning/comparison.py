"""Shared deterministic prototype policy; no regulatory compliance claim."""
from decimal import Decimal, InvalidOperation

VERSION = 'comparison-v2'
WEIGHT_FIELDS = {'GROSS_WEIGHT', 'NET_WEIGHT'}
MONEY_FIELDS = {'TOTAL_AMOUNT', 'FREIGHT_AMOUNT', 'INSURANCE_AMOUNT'}


def tolerance(field, policy=None):
    if field == 'PACKAGE_COUNT':
        return Decimal('0')
    if field in WEIGHT_FIELDS:
        return Decimal(str((policy or {}).get('weight_absolute_tolerance', '0.01')))
    return Decimal('0.01')


def numeric_equal(left, right, field='', policy=None):
    try:
        a, b = Decimal(str(left)), Decimal(str(right))
        if not a.is_finite() or not b.is_finite():
            return False
        if field == 'PACKAGE_COUNT' and (a != a.to_integral_value() or b != b.to_integral_value()):
            return False
        return abs(a - b) <= tolerance(field, policy)
    except (InvalidOperation, ValueError, TypeError):
        return False


def describe(policy=None):
    return {'version': VERSION, 'weight_absolute_tolerance': str(tolerance('GROSS_WEIGHT', policy)),
        'count_tolerance': '0', 'money_absolute_tolerance': '0.01',
        'unit_policy': 'Compare only compatible supplied units; mixed units require review.',
        'authority_status': 'prototype'}
