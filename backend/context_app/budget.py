"""Conservative database-backed reservation before every billable request."""
import os
import math
from sqlalchemy.dialects.postgresql import insert
from database.connection import SessionLocal
from .models import UsageBudget


def reserve(input_upper_bound, output_limit):
    ceiling = float(os.getenv("AGENT_BUDGET_USD", "0"))
    rate_in = float(os.getenv("MODEL_INPUT_USD_PER_MILLION", "0"))
    rate_out = float(os.getenv("MODEL_OUTPUT_USD_PER_MILLION", "0"))
    if not all(math.isfinite(v) for v in (ceiling, rate_in, rate_out)) or min(ceiling, rate_in, rate_out) <= 0:
        raise ValueError("Configure a positive API budget and verified model prices before enabling live calls.")
    amount = (input_upper_bound * rate_in + output_limit * rate_out) / 1_000_000
    with SessionLocal() as db:
        db.execute(insert(UsageBudget).values(id="application", charged_usd=0, reserved_usd=0,
            input_tokens=0, output_tokens=0).on_conflict_do_nothing())
        row = db.query(UsageBudget).filter_by(id="application").with_for_update().one()
        if row.charged_usd + row.reserved_usd + amount > ceiling:
            raise ValueError("Application API budget reached. No model call was sent.")
        row.reserved_usd += amount
        db.commit()
    return amount, rate_in, rate_out


def reconcile(reservation, input_tokens=None, output_tokens=None):
    amount, rate_in, rate_out = reservation
    # Unknown outcome remains charged at the reserved upper bound; do not allow
    # retries to repeatedly release money after a possibly billable timeout.
    charged = amount if input_tokens is None else (input_tokens * rate_in + output_tokens * rate_out) / 1_000_000
    with SessionLocal() as db:
        row = db.query(UsageBudget).filter_by(id="application").with_for_update().one()
        row.reserved_usd = max(0, row.reserved_usd - amount)
        row.charged_usd += charged
        row.input_tokens += input_tokens or 0
        row.output_tokens += output_tokens or 0
        db.commit()
    return charged
