"""Shared typed declaration validation, using Decimal throughout valuation."""
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def number(value, *, positive=False, integer=False, precision=True):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Enter a finite number.') from None
    if not result.is_finite() or result < 0 or result > Decimal('1000000000000') or (positive and result <= 0):
        raise ValueError('Enter a finite positive value within the supported range.' if positive else 'Enter a finite nonnegative value within the supported range.')
    if precision and result.as_tuple().exponent < -8:
        raise ValueError('Use at most eight decimal places.')
    if integer and result != result.to_integral_value():
        raise ValueError('Package counts must be whole numbers.')
    return result


def money(value):
    return number(value, precision=False).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def hs_code(value):
    code = str(value or '').replace('.', '').strip()
    if not re.fullmatch(r'\d{6}(?:\d{2}){0,3}', code):
        raise ValueError('HS code must contain 6, 8, 10 or 12 digits.')
    return code


def validate_profile(values):
    cleaned = {}
    for key, value in values.items():
        if not isinstance(value, (str, int, float)) or isinstance(value, bool):
            raise ValueError(f'{key} must be a text or numeric value.')
        text = str(value).strip()
        if not text or len(text) > 200:
            raise ValueError(f'{key} must contain 1–200 characters.')
        if key == 'currency_rate':
            text = format(number(text, positive=True), 'f')
        elif key == 'container_flag':
            if text.lower() not in {'0', '1', 'true', 'false'}:
                raise ValueError('Container flag must be 0 or 1.')
            text = '1' if text.lower() in {'1', 'true'} else '0'
        elif key == 'transport_mode' and not re.fullmatch(r'[1-9]', text):
            raise ValueError('Transport mode must be a single numeric code from 1 to 9.')
        elif key == 'general_procedure_code' and not re.fullmatch(r'\d{1,4}', text):
            raise ValueError('Procedure code must contain 1–4 digits.')
        elif key == 'declaration_type':
            text = text.upper()
            if not re.fullmatch(r'[A-Z]{2}', text):
                raise ValueError('Declaration type must contain two letters.')
        cleaned[key] = text
    return cleaned


def allocate(total, weights):
    """Allocate rounded amounts deterministically while preserving their sum."""
    total = money(total)
    weights = [number(w, positive=True) for w in weights]
    denominator = sum(weights)
    result = [money(total*w/denominator) for w in weights[:-1]]
    result.append(total-sum(result))
    if any(v < 0 for v in result):
        raise ValueError('Allocation rounding would produce a negative item amount.')
    return result
