# service/calc_lines.py
# Shared quote/invoice line aggregation (per-line tax + discount flags).

from decimal import Decimal

D2 = Decimal('0.01')


def line_signed_total(line) -> Decimal:
    """Positive ``line_total`` contributes positively; ``is_discount`` negates."""
    raw = line.line_total if isinstance(line.line_total, Decimal) else Decimal(
        str(line.line_total or 0)
    )
    if getattr(line, 'is_discount', False):
        return -raw
    return raw


def line_taxable_signed_total(line) -> Decimal:
    """Portion of the signed line that participates in the header ``tax_rate``."""
    if not getattr(line, 'is_taxable', True):
        return Decimal('0')
    return line_signed_total(line)
