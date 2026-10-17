# Phase 09 — Canonical Normalization + Dossier Upload

> **Priority:** MUST *(upgraded from SHOULD — see § Cross-Team Impact below)*
> **Estimated Time:** 3–4 hours *(+1 h for Dossier Upload layer)*
> **Dependencies:** Phase 06 (raw extraction output), Phase 10 (pipeline)
> **Blocks:** Accuracy of Aloka's discrepancy detection AND knowledge graph conflict detection
> **🚨 Critical for Aloka:** `knowledge_graph.py` reads `entity.get("normalized_value", entity["value"])` for conflict comparisons. Without reliable `normalized_value` fields, numeric comparisons can fail or produce false conflicts.

## Architecture Update — What Changed

Phase 09 now owns the **full ingest-to-normalize path**. In addition to the three-tier normalization engine, you must implement:

| New Capability | Description |
| --- | --- |
| ✅ Dossier Upload | A single HTTP call that accepts one or more PDF files belonging to one shipment |
| ✅ `POST /api/upload` | FastAPI endpoint that receives `multipart/form-data`, creates a `dossier_id`, and queues processing |
| ✅ Multi-file shipment grouping | Multiple documents (invoice + packing list + AWB + B/L) grouped under one `dossier_id` |
| ✅ Processing status / `dossier_id` | `GET /api/upload/{dossier_id}/status` returns per-document processing state |
| ✅ Gemini-based entity extraction | Phase 06 `EntityExtractor` uses Gemini Vision — Phase 09 normalizes its output |

Every new capability reuses the existing modules:

| Existing Component | Role |
| --- | --- |
| ✅ PaddleOCR | OCR engine for bounding-box text extraction |
| ✅ Bounding-box mapping | `_find_bbox()` maps Gemini-extracted values to OCR token positions |
| ✅ Database-backed `norm_cache` | PostgreSQL semantic canonicalization cache |
| ✅ Deterministic normalization | Python rules for weights, volumes, dates, numbers, identifiers |
| ✅ Tier 1 → DB → Gemini | Three-tier semantic normalization path |
| ✅ Confidence scoring | `ConfidenceScorer` runs after normalization inside pipeline |

---

# Goal

Transform raw OCR-extracted strings into canonical, machine-comparable values.

Examples:

```text
"450 KG"
"450.00 Kilograms"
"1,000.00 LBS"
```

should become:

```text
450.0 kg
450.0 kg
453.592 kg
```

The original OCR/Gemini value must always be preserved in:

```text
value
```

The canonical machine-readable representation is stored in:

```text
normalized_value
unit
warn
```

This allows Aloka's Knowledge Graph to reliably compare values across invoices, packing lists, AWBs, B/Ls, and other shipping documents.

---

# Why

Without normalization, the discrepancy engine can produce false conflicts or runtime failures.

### Same physical value

```text
"450 KG"
"450.00 kg"
```

Without normalization:

```text
Different strings
→ possible false conflict
```

With normalization:

```text
450.0 kg
450.0 kg
→ comparable
```

### Different units

```text
"1,000 LBS"
"453.592 KG"
```

Without normalization:

```text
Incompatible raw strings
```

With normalization:

```text
453.592 kg
453.592 kg
→ comparable
```

### Incoterm variants

```text
"FOB Colombo"
"Free On Board"
```

become:

```text
FOB
FOB
```

### Numeric crash

```python
float("450.00 KG")
```

can raise:

```text
ValueError
```

whereas:

```python
float(450.0)
```

works correctly.

---

# Architecture — Hybrid Three-Tier Normalization

Phase 09 uses two normalization paths.

## Path A — Deterministic Rules

Use Python rules whenever the value can be normalized reliably without an LLM.

Examples:

```text
Weights
Volumes
Dates
Numbers
Identifiers
Package counts
Incoterms
Currency
```

These do NOT require a Gemini API call.

---

## Path B — Semantic Canonicalization

Use the three-tier architecture for values that require semantic understanding.

Examples:

```text
CONSIGNEE_NAME
SHIPPER_NAME
PORT_LOADING
PORT_DISCHARGE
VESSEL_NAME
```

The flow is:

```text
                          RAW ENTITY
                              │
                              ▼
                  ┌─────────────────────────┐
                  │ Deterministic Rule?     │
                  └────────────┬────────────┘
                               │
                       ┌───────┴───────┐
                       │               │
                      YES              NO
                       │               │
                       ▼               ▼
                Python Rules        Tier 1
                       │          Cache Key
                       │               │
                       │               ▼
                       │        Tier 2 — PostgreSQL
                       │               │
                       │          ┌────┴────┐
                       │          │         │
                       │         HIT       MISS
                       │          │         │
                       │          │         ▼
                       │          │     Tier 3 — Gemini
                       │          │         │
                       │          │         ▼
                       │          │      Save DB
                       │          │         │
                       └──────────┴─────────┘
                                  │
                                  ▼
                        NORMALIZED RESULT
```

---

# Important Responsibility Boundary

Phase 09 must NOT modify the original extracted value.

Phase 06:

```text
value = "1,000.00 LBS"
```

Phase 09:

```text
normalized_value = 453.592
unit = "kg"
```

Final entity:

```json
{
  "entity_type": "GROSS_WEIGHT",
  "value": "1,000.00 LBS",
  "normalized_value": 453.592,
  "unit": "kg"
}
```

The raw value remains available for auditing and XAI.

---

# Tier 1 — Canonical Cache-Key Generation

Tier 1 creates a deterministic lookup key for semantic text values.

It is NOT the final normalized value.

### Example

Input A:

```text
"Colombo Custom Port"
```

Input B:

```text
"Port Custom Colombo"
```

After cleaning:

```text
colombo custom port
```

After sorting:

```text
colombo custom port
```

Both produce:

```text
PORT_LOADING:colombo custom port
```

### Algorithm

1. Lowercase
2. Replace punctuation with spaces
3. Normalize whitespace
4. Split into tokens
5. Sort alphabetically
6. Rejoin
7. Prefix with `entity_type`

Implementation:

```python
def _tier1_key(entity_type: str, raw: str) -> str:
    cleaned = re.sub(
        r"[^a-z0-9\s]",
        " ",
        raw.lower()
    )

    tokens = sorted(cleaned.split())

    return f"{entity_type}:{' '.join(tokens)}"
```

### Important

The Tier 1 result is a cache key only.

Example:

```text
value:
"Port Custom Colombo"

cache_key:
"PORT_LOADING:colombo custom port"

normalized_value:
"Colombo Port (LKCMB)"
```

---

# Tier 2 — PostgreSQL Normalization Cache

Semantic canonicalization results are stored in the existing PostgreSQL database.

This replaces:

```text
backend/data/norm_cache.json
```

with:

```text
PostgreSQL
└── norm_cache
```

## Why PostgreSQL?

A database is preferable for a deployed multi-request backend because it provides:

```text
• Shared persistent cache
• Indexed lookup
• Concurrent access
• Cache analytics
• hit_count tracking
• last_used tracking
• Manual corrections
• Persistence across application restarts
• Future cleanup/eviction based on last_used
```

The cache should not be treated as the source of truth for the original document. It is a reusable canonical-mapping store.

---

# Database Schema

Add this to:

```text
backend/schema.sql
```

```sql
CREATE TABLE IF NOT EXISTS norm_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cache_key VARCHAR(255) NOT NULL UNIQUE,

    entity_type VARCHAR(50) NOT NULL,

    raw_value TEXT NOT NULL,

    canonical TEXT NOT NULL,

    source VARCHAR(20) NOT NULL DEFAULT 'llm'
        CHECK (source IN ('llm', 'rule', 'manual')),

    hit_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    last_used TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_norm_cache_key
    ON norm_cache(cache_key);

CREATE INDEX IF NOT EXISTS idx_norm_cache_entity
    ON norm_cache(entity_type);

CREATE INDEX IF NOT EXISTS idx_norm_cache_last_used
    ON norm_cache(last_used);
```

---

# Database Column Meaning

| Column        | Purpose                                 |
| ------------- | --------------------------------------- |
| `id`          | Unique cache-row identifier             |
| `cache_key`   | Tier 1 key used for lookup              |
| `entity_type` | Type of entity being canonicalized      |
| `raw_value`   | Original value that created the mapping |
| `canonical`   | Canonical semantic value                |
| `source`      | `rule`, `llm`, or `manual`              |
| `hit_count`   | Number of successful cache hits         |
| `created_at`  | Time mapping was created                |
| `last_used`   | Last successful lookup                  |

---

# Tier 2 Cache Behavior

## Cache Hit

```text
Tier 1 key
    ↓
PostgreSQL
    ↓
MATCH
    ↓
hit_count += 1
last_used = NOW()
    ↓
Return canonical
```

Example:

```text
PORT_LOADING:colombo custom port
```

returns:

```text
Colombo Port (LKCMB)
```

without calling Gemini.

---

## Cache Miss

```text
Tier 1 key
    ↓
PostgreSQL
    ↓
NO MATCH
    ↓
Tier 3 Gemini
```

Gemini returns the canonical value.

Then:

```text
Gemini result
    ↓
INSERT into norm_cache
    ↓
Return canonical
```

The next occurrence can use the database.

---

# Pre-Seed Common Values

Pre-seed common values to reduce unnecessary Gemini calls during the demo.

```sql
INSERT INTO norm_cache (
    cache_key,
    entity_type,
    raw_value,
    canonical,
    source
)
VALUES

(
    'CONSIGNEE_NAME:burlington inc industries',
    'CONSIGNEE_NAME',
    'Burlington Industries Inc.',
    'Burlington Industries Inc.',
    'rule'
),

(
    'PORT_LOADING:cmb colombo',
    'PORT_LOADING',
    'Colombo (CMB)',
    'Colombo Port (LKCMB)',
    'rule'
),

(
    'PORT_DISCHARGE:angeles lax los',
    'PORT_DISCHARGE',
    'Los Angeles (LAX)',
    'Los Angeles (USLAX)',
    'rule'
),

(
    'INCOTERM:fob',
    'INCOTERM',
    'FOB',
    'FOB',
    'rule'
),

(
    'INCOTERM:cif',
    'INCOTERM',
    'CIF',
    'CIF',
    'rule'
)

ON CONFLICT (cache_key)
DO NOTHING;
```

---

# Tier 3 — Gemini Semantic Canonicalization

Gemini is only called when:

```text
1. The entity requires semantic canonicalization
AND
2. The PostgreSQL cache has no mapping
```

Typical examples:

```text
"Colombo Custom Port"
"Port of Colombo"
"Burlington Industries, Inc."
"Industries Burlington Inc."
```

Deterministic values such as:

```text
1000 lbs
12.5 CBM
15-Aug-2026
1,250.50
```

must NOT be sent to Gemini.

---

# Gemini Integration

Use the current Google GenAI Python SDK:

```python
from google import genai
```

The Gemini model should be configurable using:

```text
GEMINI_MODEL
```

Example:

```text
GEMINI_MODEL=gemini-3.8-flash
```

Google's current documentation uses the `google-genai` SDK and supports structured JSON-schema/Pydantic output. `gemini-2.0-flash` has been shut down and must not be used for the new implementation.

---

# Structured Gemini Output

Do not rely only on free-form text parsing.

Use a small schema:

```python
from pydantic import BaseModel


class CanonicalizationResult(BaseModel):
    canonical: str
```

Then configure Gemini to return JSON matching this schema.

Conceptually:

```python
response = client.models.generate_content(
    model=self._gemini_model,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=CanonicalizationResult,
    ),
)
```

Then:

```python
result = CanonicalizationResult.model_validate_json(
    response.text
)

canonical = result.canonical
```

This reduces malformed JSON handling compared with manually parsing arbitrary model text.

---

# Gemini Prompt

```text
You are a customs document normalization assistant.

Entity type:
{entity_type}

Raw value:
{raw_value}

Task:
Return the canonical representation of this trade entity.

Rules:

1. Ports and locations:
   - Return a canonical location name.
   - Include UN/LOCODE only when confidently identifiable.
   - Example:
     Colombo Port → Colombo Port (LKCMB)
   - Never invent a UN/LOCODE.

2. Company names:
   - Normalize capitalization.
   - Normalize common legal-name formatting.
   - Preserve the actual company identity.
   - Do not invent information.

3. Vessel names:
   - Normalize spacing and capitalization.
   - Preserve vessel identity.

4. If a reliable canonical representation cannot be determined:
   - Return the original value with minimal formatting cleanup.

Return ONLY the canonical value.
Do not provide an explanation.
```

---

# LLM Safety Rule

Never convert uncertainty into fabricated certainty.

Bad:

```text
Raw:
Unknown Port XYZ

Gemini:
Unknown Port (ZZXXX)
```

Good:

```text
Raw:
Unknown Port XYZ

Gemini:
Unknown Port XYZ
```

The normalizer must prefer a safe fallback over an invented canonical identifier.

---

# Standardization Specifications

# Weights — Base Unit `kg`

| Raw OCR Input     | `normalized_value` | `unit` |
| ----------------- | -----------------: | ------ |
| `"450.00 KG"`     |            `450.0` | `"kg"` |
| `"450 Kilograms"` |            `450.0` | `"kg"` |
| `"1,000.00 LBS"`  |          `453.592` | `"kg"` |
| `"2 MT"`          |           `2000.0` | `"kg"` |
| `"500 g"`         |              `0.5` | `"kg"` |

### Conversion factors

```text
lb / lbs / pound / pounds
→ × 0.453592

MT / metric ton / metric tons / tonne / tonnes
→ × 1000.0

g / gram / grams
→ ÷ 1000.0
```

---

# Volumes — Base Unit `cbm`

| Raw OCR Input    | `normalized_value` | `unit`  |
| ---------------- | -----------------: | ------- |
| `"12.5 CBM"`     |             `12.5` | `"cbm"` |
| `"12500 liters"` |             `12.5` | `"cbm"` |

```text
1 liter = 0.001 cbm
```

---

# Dates — ISO 8601

All recognized dates become:

```text
YYYY-MM-DD
```

| Raw Input       | `normalized_value` |
| --------------- | ------------------ |
| `"15-Aug-2026"` | `"2026-08-15"`     |
| `"08/15/2026"`  | `"2026-08-15"`     |
| `"2026.08.15"`  | `"2026-08-15"`     |

Use:

```python
from dateutil import parser

parsed = parser.parse(
    raw,
    fuzzy=True
)

normalized = parsed.strftime(
    "%Y-%m-%d"
)
```

If parsing fails, return `None`.

---

# Numbers & Locale Formats

| Raw Input         | `normalized_value` |
| ----------------- | -----------------: |
| `"1,250.50"`      |           `1250.5` |
| `"1.250,50"`      |           `1250.5` |
| `"USD 49,740.00"` |          `49740.0` |
| `"1,250"`         |           `1250.0` |
| `"450,00"`        |            `450.0` |

## Detection

When both `,` and `.` occur:

```text
The separator appearing last is assumed to be the decimal separator.
```

Example:

```text
1,250.50
→ 1250.50
```

```text
1.250,50
→ 1250.50
```

When only comma occurs:

```text
1,250
→ thousands separator
→ 1250.0
```

```text
450,00
→ decimal comma
→ 450.0
```

## Implementation

```python
def _normalize_number(
    raw: str
) -> Optional[float]:

    if not raw:
        return None

    s = str(raw).strip()

    # Remove a leading currency code.
    s = re.sub(
        r"^[A-Z]{3}\s*",
        "",
        s.upper()
    )

    has_comma = "," in s
    has_dot = "." in s

    if has_comma and has_dot:

        if s.rindex(",") > s.rindex("."):
            # European:
            # 1.250,50 → 1250.50
            s = s.replace(".", "")
            s = s.replace(",", ".")
        else:
            # US/UK:
            # 1,250.50 → 1250.50
            s = s.replace(",", "")

    elif has_comma:

        if re.search(
            r",\d{3}$",
            s
        ):
            # 1,250
            s = s.replace(",", "")
        else:
            # 450,00
            s = s.replace(",", ".")

    match = re.search(
        r"[-+]?\d+(?:\.\d+)?",
        s
    )

    if not match:
        return None

    try:
        return float(match.group())
    except ValueError:
        return None
```

---

# Identifiers — Exact-Match Sanitization

Fields:

```text
HS_CODE
BL_NUMBER
CONTAINER_NUMBER
AWB_NUMBER
INVOICE_NUMBER
```

Rules:

1. Strip whitespace
2. Remove `-`
3. Remove `/`
4. Remove `.`
5. Uppercase

Examples:

```text
"MAEU 123 456 789"
→ "MAEU123456789"
```

```text
"6310-12345678"
→ "631012345678"
```

```text
"8516.72.00.00"
→ "8516720000"
```

---

# Package Counts

| Raw Input      | `normalized_value` | `unit`      |
| -------------- | -----------------: | ----------- |
| `"25 Cartons"` |               `25` | `"cartons"` |
| `"25 CTNS"`    |               `25` | `"cartons"` |
| `"25 Pieces"`  |               `25` | `"pieces"`  |
| `"25 PCS"`     |               `25` | `"pieces"`  |
| `"10 Bales"`   |               `10` | `"bales"`   |
| `"20 Rolls"`   |               `20` | `"rolls"`   |

Suggested aliases:

```text
carton / cartons / ctn / ctns
→ cartons

piece / pieces / pc / pcs
→ pieces

bale / bales
→ bales

roll / rolls
→ rolls
```

---

# Incoterms

Incoterms should be normalized locally whenever possible.

| Raw Input                      | `normalized_value` |
| ------------------------------ | ------------------ |
| `"FOB Colombo"`                | `"FOB"`            |
| `"Free On Board"`              | `"FOB"`            |
| `"CIF London"`                 | `"CIF"`            |
| `"Cost Insurance and Freight"` | `"CIF"`            |
| `"EXW Factory"`                | `"EXW"`            |
| `"DAP Colombo"`                | `"DAP"`            |
| `"DDP London"`                 | `"DDP"`            |

Supported codes:

```text
EXW
FCA
CPT
CIP
DAP
DPU
DDP
FAS
FOB
CFR
CIF
```

Do not send ordinary Incoterm variants to Gemini.

---

# Currency

Currency normalization must use explicit aliases.

Do NOT use:

```python
raw.upper()[:3]
```

because:

```text
"US Dollar"
→ "US "
```

would be wrong.

Use:

```python
CURRENCY_ALIASES = {
    "usd": "USD",
    "us dollar": "USD",
    "us dollars": "USD",
    "u.s. dollar": "USD",
    "u.s. dollars": "USD",

    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",

    "gbp": "GBP",
    "pound sterling": "GBP",

    "jpy": "JPY",
    "yen": "JPY",

    "lkr": "LKR",
    "sri lankan rupee": "LKR",
    "sri lankan rupees": "LKR",
}
```

Example:

```text
CURRENCY:
"US Dollar"
→ "USD"
```

But:

```text
TOTAL_AMOUNT:
"USD 49,740.00"
→ 49740.0
```

The currency component must not be confused with the numeric amount.

---

# Edge Case Handling

# Missing Unit — Graceful Default

Scenario:

```text
entity_type = GROSS_WEIGHT
raw_value = "450"
```

Return:

```json
{
  "normalized_value": 450.0,
  "unit": "kg",
  "original_value": "450",
  "warn": true
}
```

The system should continue processing.

---

# Unparseable Numeric Value

Example:

```text
"45O.OO KG"
```

where `O` is the letter `O`.

Return:

```json
{
  "normalized_value": null,
  "unit": null,
  "original_value": "45O.OO KG",
  "warn": true
}
```

Never raise an exception.

---

# Unparseable Date

Example:

```text
"31-FOO-2026"
```

Return:

```json
{
  "normalized_value": null,
  "unit": null,
  "original_value": "31-FOO-2026",
  "warn": true
}
```

---

# Database Unavailable — Graceful Degradation

If PostgreSQL is unavailable:

```text
Application starts
      ↓
Log warning
      ↓
Tier 2 disabled
      ↓
Deterministic rules continue
      ↓
Semantic values may fall back to Gemini
      ↓
Pipeline continues
```

Example log:

```text
DB cache unavailable — running without Tier 2 cache
```

The database must never become a single point of failure for the entire AI pipeline.

---

# Gemini Unavailable

### Database hit

```text
DB hit
→ Return canonical value
```

### Database miss

Return the safe raw value:

```json
{
  "normalized_value": "Colombo Port",
  "unit": null,
  "original_value": "Colombo Port",
  "warn": true
}
```

Never crash the pipeline.

---

# Database Write Failure

Example:

```text
Gemini
 ↓
Canonical value
 ↓
DB INSERT fails
 ↓
Log warning
 ↓
Return canonical value
```

A cache write failure must not invalidate a successful normalization.

---

# Database Connection Strategy

Do not create one raw PostgreSQL connection and share it across concurrent FastAPI requests.

Use a connection pool.

Example:

```python
from psycopg2.pool import ThreadedConnectionPool
```

Architecture:

```text
FastAPI Requests
       │
       ▼
PostgreSQL Connection Pool
       │
       ├── Connection 1
       ├── Connection 2
       ├── Connection 3
       └── ...
       │
       ▼
   norm_cache
```

This is preferable to keeping a single connection inside every `EntityNormalizer` instance.

---

# Implementation — `normalizer.py`

> **Important:** Do not change the public function signature.
>
> Phase 10 calls:
>
> ```python
> normalizer.normalize(entity_type, raw_value)
> ```
>
> and expects:
>
> ```python
> {
>     "normalized_value": ...,
>     "unit": ...,
>     "original_value": ...,
>     "warn": ...
> }
> ```

```python
# backend/ai_pipeline/normalizer.py

import logging
import os
import re
from pathlib import Path
from typing import Optional

from dateutil import parser as date_parser
from dotenv import load_dotenv

load_dotenv(
    Path(__file__).parent.parent / ".env"
)

logger = logging.getLogger(__name__)


class EntityNormalizer:

    WEIGHT_TYPES = {
        "GROSS_WEIGHT",
        "NET_WEIGHT",
        "TARE_WEIGHT",
    }

    IDENTIFIER_TYPES = {
        "BL_NUMBER",
        "AWB_NUMBER",
        "CONTAINER_NUMBER",
        "INVOICE_NUMBER",
        "HS_CODE",
    }

    SEMANTIC_TYPES = {
        "CONSIGNEE_NAME",
        "SHIPPER_NAME",
        "PORT_LOADING",
        "PORT_DISCHARGE",
        "VESSEL_NAME",
    }

    def __init__(self):

        # ========================================================
        # Tier 2 — PostgreSQL Connection Pool
        # ========================================================

        self._db_pool = None

        try:
            from psycopg2.pool import ThreadedConnectionPool

            database_url = os.getenv("DATABASE_URL")

            if database_url:

                self._db_pool = ThreadedConnectionPool(
                    minconn=1,
                    maxconn=5,
                    dsn=database_url,
                )

                logger.info(
                    "EntityNormalizer: PostgreSQL cache enabled"
                )

            else:

                logger.warning(
                    "DATABASE_URL not set — "
                    "Tier 2 cache disabled"
                )

        except Exception as exc:

            logger.warning(
                "PostgreSQL cache unavailable: %s",
                exc,
            )

        # ========================================================
        # Tier 3 — Gemini
        # ========================================================

        self._gemini = None

        self._gemini_model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash"
        )

        api_key = os.getenv(
            "GEMINI_API_KEY",
            ""
        )

        if api_key and api_key != "your_key_here":

            try:
                from google import genai

                self._gemini = genai.Client(
                    api_key=api_key
                )

                logger.info(
                    "EntityNormalizer: Gemini enabled "
                    "model=%s",
                    self._gemini_model,
                )

            except Exception as exc:

                logger.warning(
                    "Gemini initialization failed: %s",
                    exc,
                )

    # ============================================================
    # PUBLIC API
    # ============================================================

    def normalize(
        self,
        entity_type: str,
        raw_value: str
    ) -> dict:

        try:

            raw_value = (
                str(raw_value)
                if raw_value is not None
                else ""
            )

            # ----------------------------------------------------
            # WEIGHT
            # ----------------------------------------------------

            if entity_type in self.WEIGHT_TYPES:

                number, unit, warn = (
                    self._normalize_weight(raw_value)
                )

                return {
                    "normalized_value": number,
                    "unit": unit,
                    "original_value": raw_value,
                    "warn": warn,
                }

            # ----------------------------------------------------
            # VOLUME
            # ----------------------------------------------------

            if entity_type == "VOLUME":

                number, unit, warn = (
                    self._normalize_volume(raw_value)
                )

                return {
                    "normalized_value": number,
                    "unit": unit,
                    "original_value": raw_value,
                    "warn": warn,
                }

            # ----------------------------------------------------
            # PACKAGE COUNT
            # ----------------------------------------------------

            if entity_type == "PACKAGE_COUNT":

                number, unit, warn = (
                    self._normalize_package_count(
                        raw_value
                    )
                )

                return {
                    "normalized_value": number,
                    "unit": unit,
                    "original_value": raw_value,
                    "warn": warn,
                }

            # ----------------------------------------------------
            # INCOTERM
            # ----------------------------------------------------

            if entity_type == "INCOTERM":

                return {
                    "normalized_value":
                        self._normalize_incoterm(
                            raw_value
                        ),
                    "unit": None,
                    "original_value": raw_value,
                    "warn": False,
                }

            # ----------------------------------------------------
            # CURRENCY
            # ----------------------------------------------------

            if entity_type == "CURRENCY":

                return {
                    "normalized_value":
                        self._normalize_currency(
                            raw_value
                        ),
                    "unit": None,
                    "original_value": raw_value,
                    "warn": False,
                }

            # ----------------------------------------------------
            # NUMERIC FIELDS
            # ----------------------------------------------------

            if entity_type in {
                "TOTAL_AMOUNT",
                "UNIT_PRICE",
                "TOTAL_PRICE",
            }:

                number = self._normalize_number(
                    raw_value
                )

                return {
                    "normalized_value": number,
                    "unit": None,
                    "original_value": raw_value,
                    "warn": number is None,
                }

            # ----------------------------------------------------
            # DATES
            # ----------------------------------------------------

            if entity_type in {
                "INVOICE_DATE",
                "EXPIRY_DATE",
            }:

                normalized_date = (
                    self._normalize_date(
                        raw_value
                    )
                )

                return {
                    "normalized_value":
                        normalized_date,
                    "unit": None,
                    "original_value": raw_value,
                    "warn":
                        normalized_date is None,
                }

            # ----------------------------------------------------
            # IDENTIFIERS
            # ----------------------------------------------------

            if entity_type in self.IDENTIFIER_TYPES:

                identifier = (
                    self._normalize_identifier(
                        raw_value
                    )
                )

                return {
                    "normalized_value": identifier,
                    "unit": None,
                    "original_value": raw_value,
                    "warn": False,
                }

            # ----------------------------------------------------
            # SEMANTIC TEXT
            # ----------------------------------------------------

            if entity_type in self.SEMANTIC_TYPES:

                return self._normalize_semantic(
                    entity_type,
                    raw_value,
                )

            # ----------------------------------------------------
            # UNKNOWN TEXT
            # ----------------------------------------------------

            return {
                "normalized_value":
                    raw_value.strip(),
                "unit": None,
                "original_value": raw_value,
                "warn": False,
            }

        except Exception:

            logger.exception(
                "Normalization failed: "
                "entity_type=%s raw_value=%r",
                entity_type,
                raw_value,
            )

            return {
                "normalized_value": None,
                "unit": None,
                "original_value": raw_value,
                "warn": True,
            }

    # ============================================================
    # TIER 1 — CACHE KEY
    # ============================================================

    def _tier1_key(
        self,
        entity_type: str,
        raw: str
    ) -> str:

        cleaned = re.sub(
            r"[^a-z0-9\s]",
            " ",
            raw.lower(),
        )

        tokens = sorted(
            cleaned.split()
        )

        return (
            f"{entity_type}:"
            f"{' '.join(tokens)}"
        )

    # ============================================================
    # SEMANTIC NORMALIZATION
    # ============================================================

    def _normalize_semantic(
        self,
        entity_type: str,
        raw_value: str
    ) -> dict:

        key = self._tier1_key(
            entity_type,
            raw_value,
        )

        # --------------------------------------------------------
        # Tier 2 — PostgreSQL
        # --------------------------------------------------------

        cached = self._db_get(key)

        if cached is not None:

            self._db_increment_hit(key)

            return {
                "normalized_value": cached,
                "unit": None,
                "original_value": raw_value,
                "warn": False,
            }

        # --------------------------------------------------------
        # Tier 3 — Gemini
        # --------------------------------------------------------

        canonical = self._llm_canonicalize(
            entity_type,
            raw_value,
        )

        if not canonical:

            canonical = raw_value.strip()

        # --------------------------------------------------------
        # Save result
        # --------------------------------------------------------

        self._db_set(
            key=key,
            entity_type=entity_type,
            raw_value=raw_value,
            canonical=canonical,
            source="llm",
        )

        return {
            "normalized_value": canonical,
            "unit": None,
            "original_value": raw_value,
            "warn": False,
        }

    # ============================================================
    # DATABASE — GET
    # ============================================================

    def _db_get(
        self,
        key: str
    ) -> Optional[str]:

        if self._db_pool is None:
            return None

        conn = None

        try:

            conn = self._db_pool.getconn()

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT canonical
                    FROM norm_cache
                    WHERE cache_key = %s
                    LIMIT 1
                    """,
                    (key,),
                )

                row = cur.fetchone()

                return (
                    row[0]
                    if row
                    else None
                )

        except Exception as exc:

            logger.warning(
                "DB cache read failed: %s",
                exc,
            )

            if conn is not None:

                try:
                    conn.rollback()
                except Exception:
                    pass

            return None

        finally:

            if conn is not None:
                self._db_pool.putconn(conn)

    # ============================================================
    # DATABASE — INSERT / UPDATE
    # ============================================================

    def _db_set(
        self,
        key: str,
        entity_type: str,
        raw_value: str,
        canonical: str,
        source: str = "llm",
    ) -> None:

        if self._db_pool is None:
            return

        conn = None

        try:

            conn = self._db_pool.getconn()

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO norm_cache (
                        cache_key,
                        entity_type,
                        raw_value,
                        canonical,
                        source
                    )
                    VALUES (
                        %s, %s, %s, %s, %s
                    )

                    ON CONFLICT (cache_key)
                    DO UPDATE SET
                        canonical = EXCLUDED.canonical,
                        last_used = NOW()
                    """,
                    (
                        key,
                        entity_type,
                        raw_value,
                        canonical,
                        source,
                    ),
                )

            conn.commit()

        except Exception as exc:

            logger.warning(
                "DB cache write failed: %s",
                exc,
            )

            if conn is not None:

                try:
                    conn.rollback()
                except Exception:
                    pass

        finally:

            if conn is not None:
                self._db_pool.putconn(conn)

    # ============================================================
    # DATABASE — HIT COUNTER
    # ============================================================

    def _db_increment_hit(
        self,
        key: str
    ) -> None:

        if self._db_pool is None:
            return

        conn = None

        try:

            conn = self._db_pool.getconn()

            with conn.cursor() as cur:

                cur.execute(
                    """
                    UPDATE norm_cache

                    SET
                        hit_count = hit_count + 1,
                        last_used = NOW()

                    WHERE cache_key = %s
                    """,
                    (key,),
                )

            conn.commit()

        except Exception as exc:

            logger.warning(
                "DB hit update failed: %s",
                exc,
            )

            if conn is not None:

                try:
                    conn.rollback()
                except Exception:
                    pass

        finally:

            if conn is not None:
                self._db_pool.putconn(conn)

    # ============================================================
    # GEMINI — TIER 3
    # ============================================================

    def _llm_canonicalize(
        self,
        entity_type: str,
        raw_value: str,
    ) -> str:

        if self._gemini is None:

            return raw_value.strip()

        prompt = f"""
You are a customs document normalization assistant.

Entity type:
{entity_type}

Raw value:
{raw_value}

Task:
Return the canonical representation.

Rules:

1. Ports and locations:
   - Return a canonical location name.
   - Include UN/LOCODE only when confidently identifiable.
   - Never invent a UN/LOCODE.

2. Company names:
   - Normalize capitalization.
   - Normalize common legal-name formatting.
   - Preserve the actual company identity.

3. Vessel names:
   - Normalize spacing and capitalization.
   - Preserve vessel identity.

4. If reliable canonicalization is not possible:
   - Return the original value with minimal cleanup.

Return only the canonical value.
No explanation.
"""

        try:

            from pydantic import BaseModel
            from google.genai import types

            class CanonicalizationResult(
                BaseModel
            ):
                canonical: str

            response = (
                self._gemini
                .models
                .generate_content(
                    model=self._gemini_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=(
                            CanonicalizationResult
                        ),
                    ),
                )
            )

            parsed = (
                CanonicalizationResult
                .model_validate_json(
                    response.text
                )
            )

            return parsed.canonical.strip()

        except Exception as exc:

            logger.warning(
                "Gemini canonicalization failed: %s",
                exc,
            )

            return raw_value.strip()

    # ============================================================
    # FIELD-SPECIFIC NORMALIZERS
    # ============================================================

    def _normalize_weight(
        self,
        raw: str
    ) -> tuple:

        text = raw.lower().strip()

        number = self._normalize_number(
            text
        )

        if number is None:

            return (
                None,
                None,
                True,
            )

        if re.search(
            r"\b(kg|kgs|kilogram|kilograms)\b",
            text,
        ):

            return (
                number,
                "kg",
                False,
            )

        if re.search(
            r"\b(lb|lbs|pound|pounds)\b",
            text,
        ):

            return (
                round(
                    number * 0.453592,
                    3,
                ),
                "kg",
                False,
            )

        if re.search(
            r"\b(mt|metric ton|metric tons|"
            r"tonne|tonnes)\b",
            text,
        ):

            return (
                round(
                    number * 1000.0,
                    3,
                ),
                "kg",
                False,
            )

        if re.search(
            r"\b(g|gram|grams)\b",
            text,
        ):

            return (
                round(
                    number / 1000.0,
                    6,
                ),
                "kg",
                False,
            )

        # No explicit unit:
        # use kg as a best-effort default.
        return (
            number,
            "kg",
            True,
        )

    def _normalize_volume(
        self,
        raw: str
    ) -> tuple:

        text = raw.lower().strip()

        number = self._normalize_number(
            text
        )

        if number is None:

            return (
                None,
                None,
                True,
            )

        if re.search(
            r"\b(cbm|m3|m³|cubic meter|"
            r"cubic meters)\b",
            text,
        ):

            return (
                number,
                "cbm",
                False,
            )

        if re.search(
            r"\b(l|liter|liters|"
            r"litre|litres)\b",
            text,
        ):

            return (
                round(
                    number * 0.001,
                    6,
                ),
                "cbm",
                False,
            )

        return (
            number,
            "cbm",
            True,
        )

    def _normalize_package_count(
        self,
        raw: str
    ) -> tuple:

        text = raw.lower().strip()

        number = self._normalize_number(
            text
        )

        if number is None:

            return (
                None,
                None,
                True,
            )

        if re.search(
            r"\b(ctn|ctns|carton|cartons)\b",
            text,
        ):

            return (
                int(number),
                "cartons",
                False,
            )

        if re.search(
            r"\b(pc|pcs|piece|pieces)\b",
            text,
        ):

            return (
                int(number),
                "pieces",
                False,
            )

        if re.search(
            r"\b(bale|bales)\b",
            text,
        ):

            return (
                int(number),
                "bales",
                False,
            )

        if re.search(
            r"\b(roll|rolls)\b",
            text,
        ):

            return (
                int(number),
                "rolls",
                False,
            )

        return (
            int(number),
            None,
            True,
        )

    def _normalize_incoterm(
        self,
        raw: str
    ) -> Optional[str]:

        text = raw.lower().strip()

        aliases = {
            "free on board": "FOB",
            "fob": "FOB",

            "cost insurance and freight":
                "CIF",
            "cost, insurance and freight":
                "CIF",
            "cif": "CIF",

            "cost and freight": "CFR",
            "cfr": "CFR",

            "ex works": "EXW",
            "exw": "EXW",

            "free carrier": "FCA",
            "fca": "FCA",

            "carriage paid to": "CPT",
            "cpt": "CPT",

            "carriage and insurance paid to":
                "CIP",
            "cip": "CIP",

            "delivered at place": "DAP",
            "dap": "DAP",

            "delivered at place unloaded": "DPU",
            "dpu": "DPU",

            "delivered duty paid": "DDP",
            "ddp": "DDP",

            "free alongside ship": "FAS",
            "fas": "FAS",
        }

        if text in aliases:
            return aliases[text]

        for code in [
            "EXW",
            "FCA",
            "CPT",
            "CIP",
            "DAP",
            "DPU",
            "DDP",
            "FAS",
            "FOB",
            "CFR",
            "CIF",
        ]:

            if re.search(
                rf"\b{code.lower()}\b",
                text,
            ):

                return code

        return raw.strip().upper()

    def _normalize_currency(
        self,
        raw: str
    ) -> Optional[str]:

        text = raw.lower().strip()

        aliases = {
            "usd": "USD",
            "us dollar": "USD",
            "us dollars": "USD",
            "u.s. dollar": "USD",
            "u.s. dollars": "USD",

            "eur": "EUR",
            "euro": "EUR",
            "euros": "EUR",

            "gbp": "GBP",
            "pound sterling": "GBP",

            "jpy": "JPY",
            "yen": "JPY",

            "lkr": "LKR",
            "sri lankan rupee": "LKR",
            "sri lankan rupees": "LKR",
        }

        if text in aliases:
            return aliases[text]

        if re.fullmatch(
            r"[A-Za-z]{3}",
            text,
        ):
            return text.upper()

        return raw.strip().upper()

    def _normalize_number(
        self,
        raw: str
    ) -> Optional[float]:

        if not raw:
            return None

        s = str(raw).strip()

        # Remove leading currency code.
        s = re.sub(
            r"^[A-Z]{3}\s*",
            "",
            s.upper(),
        )

        has_comma = "," in s
        has_dot = "." in s

        if has_comma and has_dot:

            if s.rindex(",") > s.rindex("."):

                # European:
                # 1.250,50
                s = s.replace(".", "")
                s = s.replace(",", ".")

            else:

                # US / UK:
                # 1,250.50
                s = s.replace(",", "")

        elif has_comma:

            if re.search(
                r",\d{3}$",
                s,
            ):

                # 1,250
                s = s.replace(",", "")

            else:

                # 450,00
                s = s.replace(",", ".")

        match = re.search(
            r"[-+]?\d+(?:\.\d+)?",
            s,
        )

        if not match:
            return None

        try:
            return float(match.group())

        except ValueError:
            return None

    def _normalize_date(
        self,
        raw: str
    ) -> Optional[str]:

        try:

            parsed = date_parser.parse(
                raw,
                fuzzy=True,
            )

            return parsed.strftime(
                "%Y-%m-%d"
            )

        except Exception:

            return None

    def _normalize_identifier(
        self,
        raw: str
    ) -> str:

        return re.sub(
            r"[\s\-/\.]",
            "",
            raw,
        ).upper()
```

---

# Acceptance Criteria

## Deterministic normalization

* [ ] `"450 KG"` → `450.0 kg`
* [ ] `"450.00 Kilograms"` → `450.0 kg`
* [ ] `"1,000.00 LBS"` → `453.592 kg`
* [ ] `"2 MT"` → `2000.0 kg`
* [ ] `"500 g"` → `0.5 kg`
* [ ] `"12.5 CBM"` → `12.5 cbm`
* [ ] `"12500 liters"` → `12.5 cbm`
* [ ] `"25 CTNS"` → `25 cartons`
* [ ] `"25 Cartons"` → `25 cartons`
* [ ] `"25 Pieces"` → `25 pieces`
* [ ] `"15-Aug-2026"` → `"2026-08-15"`
* [ ] `"1.250,50"` → `1250.5`
* [ ] `"1,250.50"` → `1250.5`
* [ ] `"1,250"` → `1250.0`
* [ ] `"450,00"` → `450.0`
* [ ] `"MAEU 123 456 789"` → `"MAEU123456789"`
* [ ] `"FOB Colombo"` → `"FOB"`
* [ ] `"Free On Board"` → `"FOB"`
* [ ] `"usd"` → `"USD"`
* [ ] `"US Dollar"` → `"USD"`

## Semantic normalization

* [ ] `"Colombo Custom Port"` can be canonicalized
* [ ] Semantic canonicalization uses Tier 1 cache key
* [ ] PostgreSQL cache hit returns cached value
* [ ] PostgreSQL cache hit increments `hit_count`
* [ ] PostgreSQL cache hit updates `last_used`
* [ ] PostgreSQL cache miss reaches Gemini
* [ ] Gemini result is inserted into PostgreSQL
* [ ] Second lookup avoids Gemini
* [ ] Raw value remains unchanged
* [ ] Unknown location is not assigned a fabricated UN/LOCODE

## Error handling

* [ ] Unparseable numeric value returns `normalized_value: null`
* [ ] Unparseable date returns `normalized_value: null`
* [ ] Missing weight unit defaults to `kg` with `warn: true`
* [ ] Missing volume unit produces `warn: true`
* [ ] Database unavailable does not crash startup
* [ ] Database read failure does not crash normalization
* [ ] Database write failure does not crash normalization
* [ ] Gemini unavailable does not crash normalization
* [ ] Gemini + DB unavailable still returns a safe fallback

## Concurrency

* [ ] PostgreSQL connection pool is used
* [ ] Connections are returned to the pool
* [ ] Database exceptions trigger rollback
* [ ] Concurrent FastAPI requests can use the cache safely

---

# Database Cache Test

The test must demonstrate:

```text
First lookup
    ↓
Tier 1
    ↓
DB MISS
    ↓
Gemini
    ↓
DB INSERT

Second lookup
    ↓
Tier 1
    ↓
DB HIT
    ↓
hit_count + 1
    ↓
NO Gemini call
```

Example test structure:

```python
def test_semantic_cache_hit(normalizer, mocker):

    first = normalizer.normalize(
        "PORT_LOADING",
        "Colombo Custom Port"
    )

    second = normalizer.normalize(
        "PORT_LOADING",
        "Port Custom Colombo"
    )

    assert (
        first["normalized_value"]
        == second["normalized_value"]
    )
```

The test should also verify the Gemini mock is called at most once.

---

# Trap Test — Unit Conversion

### Commercial Invoice

```text
GROSS_WEIGHT
"1000 lbs"
```

becomes:

```text
453.592 kg
```

### Bill of Lading

```text
GROSS_WEIGHT
"453.59 kg"
```

becomes:

```text
453.59 kg
```

Expected:

```text
453.592 ≈ 453.59
```

Aloka's configured tolerance should therefore recognize the values as compatible.

---

# Trap Test — Token Sorting

Document A:

```text
"Burlington Industries Inc."
```

Document B:

```text
"Industries Burlington, Inc."
```

Expected Tier 1 key:

```text
CONSIGNEE_NAME:burlington inc industries
```

Both should reach the same semantic cache path.

---

# Trap Test — Incoterm

Document A:

```text
"FOB Colombo Port"
```

Document B:

```text
"Free On Board"
```

Expected:

```text
FOB
FOB
```

---

# Example Final Entity

```json
{
  "entity_type": "GROSS_WEIGHT",
  "value": "1,000.00 LBS",
  "normalized_value": 453.592,
  "unit": "kg",
  "page": 1,
  "bbox": [120, 240, 410, 290],
  "extraction_confidence": 0.94,
  "classification_confidence": 0.97,
  "normalization_warning": false
}
```

---

# Integration With Phase 10

Phase 10 must execute:

```text
OCR
 ↓
Classification
 ↓
Entity Extraction
 ↓
Normalization
 ↓
Confidence Scoring
 ↓
Master ExtractionResult
```

For every extracted entity:

```python
norm = normalizer.normalize(
    entity["entity_type"],
    entity["value"]
)

entity["normalized_value"] = (
    norm["normalized_value"]
)

entity["unit"] = norm["unit"]

entity["normalization_warning"] = (
    norm["warn"]
)
```

Raw:

```python
entity["value"]
```

must remain unchanged.

---

# Integration With Aloka

Aloka's Knowledge Graph should prefer:

```python
value = entity.get("normalized_value")

if value is None:
    value = entity["value"]
```

Do NOT use:

```python
entity.get("normalized_value") or entity["value"]
```

because:

```text
0
```

is a valid normalized numeric value but evaluates to `False` in Python.

For numeric comparison:

```python
value = entity.get("normalized_value")

if value is None:
    return

numeric_value = float(value)
```

---

# Critical Cross-Document Fields

Aloka's graph compares:

```text
GROSS_WEIGHT
NET_WEIGHT
PACKAGE_COUNT
CONSIGNEE_NAME
SHIPPER_NAME
INCOTERM
```

Expected normalized representations:

| Field            | Expected         |
| ---------------- | ---------------- |
| `GROSS_WEIGHT`   | `float` + `kg`   |
| `NET_WEIGHT`     | `float` + `kg`   |
| `PACKAGE_COUNT`  | `integer` + unit |
| `CONSIGNEE_NAME` | canonical string |
| `SHIPPER_NAME`   | canonical string |
| `INCOTERM`       | 3-letter code    |

---

# Responsibility Boundary

| Responsibility              | Owner                     |
| --------------------------- | ------------------------- |
| Extract raw text            | Phase 06                  |
| Preserve raw `value`        | Phase 06                  |
| Map bbox                    | Phase 06                  |
| Extraction confidence       | Phase 08                  |
| Weight conversion           | Phase 09                  |
| Volume conversion           | Phase 09                  |
| Number parsing              | Phase 09                  |
| Date normalization          | Phase 09                  |
| Identifier normalization    | Phase 09                  |
| Package count normalization | Phase 09                  |
| Currency normalization      | Phase 09                  |
| Incoterm normalization      | Phase 09                  |
| Semantic canonicalization   | Phase 09                  |
| Persistent semantic cache   | **PostgreSQL / Phase 09** |
| Matching confidence         | Aloka                     |
| Cross-document comparison   | Aloka                     |
| Knowledge Graph reasoning   | Aloka                     |

---

# Outputs

Create/update:

```text
backend/ai_pipeline/normalizer.py
backend/ai_pipeline/test_normalizer.py
backend/schema.sql
```

Database:

```text
norm_cache
```

Remove:

```text
backend/data/norm_cache.json
```

Required environment variables:

```text
DATABASE_URL=...
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.8-flash
```

---

# Final Architecture

```text
                         ENTITY FROM PHASE 06
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Entity Type      │
                         │ + Raw Value      │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              DETERMINISTIC                 SEMANTIC
                 ENTITY                       ENTITY
                    │                           │
                    ▼                           ▼
              Python Rules                  Tier 1
                    │                     Cache Key
                    │                           │
                    │                           ▼
                    │                      PostgreSQL
                    │                       norm_cache
                    │                           │
                    │                      ┌────┴────┐
                    │                      │         │
                    │                     HIT       MISS
                    │                      │         │
                    │                      │         ▼
                    │                      │      Gemini
                    │                      │         │
                    │                      │         ▼
                    │                      │      Save DB
                    │                      │         │
                    └──────────────────────┴─────────┘
                                                   │
                                                   ▼
                                          normalized_value
                                                 +
                                                unit
                                                 +
                                                warn
                                                   │
                                                   ▼
                                           PHASE 10 PIPELINE
                                                   │
                                                   ▼
                                           MASTER JSON RESULT
                                                   │
                                  ┌────────────────┴────────────────┐
                                  ▼                                 ▼
                           ALOKA / GRAPH                      KAVEEN / UI
                           Cross-document                     PDF BBox
                           comparison                         Overlay
                           Conflict detection                  Visual XAI
                           Reasoning                           Entity display
```

---

# Phase 09 Definition of Done

Phase 09 is complete when:

```text
RAW ENTITY
    │
    ▼
Deterministic Python normalization
       OR
Tier 1 → PostgreSQL → Gemini
    │
    ▼
normalized_value + unit + warn
    │
    ▼
Phase 10 Master Result
    │
    ├──→ Aloka Knowledge Graph
    │
    └──→ Kaveen Frontend / XAI
```

The core principle is:

> **Normalize deterministic values locally. Use PostgreSQL as the persistent semantic canonicalization cache. Use Gemini only for semantic cache misses. Preserve the original value at every stage. Never allow a normalization or cache failure to crash the document pipeline.**

---

# Dossier Upload Architecture

This section extends Phase 09 with the upload and grouping layer that sits **above** the pipeline. The normalization engine is unchanged — this layer feeds it.

## Concept

```text
HTTP Client
    │
    │  POST /api/upload
    │  multipart/form-data
    │  files=[invoice.pdf, packing_list.pdf, awb.pdf]
    ▼
FastAPI /api/upload
    │
    ├─ Validate files
    ├─ Generate dossier_id (UUID)
    ├─ Save PDFs to uploads/{dossier_id}/
    ├─ Insert dossier + document rows → PostgreSQL
    └─ Enqueue background processing
             │
             ▼
    Background Task per document
             │
             ├─ PaddleOCR (bounding boxes)
             ├─ Gemini Vision (entity extraction)
             ├─ Phase 09 Normalization (three-tier)
             ├─ Confidence Scoring
             └─ Write ExtractionResult → DB
                         │
                         ▼
             GET /api/upload/{dossier_id}/status
             Returns per-document status + results
```

---

## Database Schema Additions

Add to `backend/schema.sql`:

```sql
-- -------------------------------------------------------
-- Dossier: one shipment = one dossier (many documents)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS dossiers (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status      VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'processing', 'done', 'error'))
);

-- -------------------------------------------------------
-- Document: one PDF file within a dossier
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS dossier_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id      UUID NOT NULL REFERENCES dossiers(id) ON DELETE CASCADE,
    original_name   TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    document_type   VARCHAR(50),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'processing', 'done', 'error')),
    error_message   TEXT,
    extraction_json JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dossier_documents_dossier
    ON dossier_documents(dossier_id);
```

---

## FastAPI Router — `upload_router.py`

Create:

```text
backend/api/upload_router.py
```

```python
# backend/api/upload_router.py

import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ..ai_pipeline.dossier_manager import DossierManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])

_manager = DossierManager()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", summary="Upload one shipment dossier (multi-file)")
async def upload_dossier(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
) -> JSONResponse:
    """
    Accept 1–N PDF files that belong to ONE shipment.
    Returns a dossier_id immediately.
    Processing runs in the background.
    """

    if not files:
        raise HTTPException(
            status_code=422,
            detail="At least one file is required.",
        )

    dossier_id = str(uuid.uuid4())
    dossier_dir = UPLOAD_DIR / dossier_id
    dossier_dir.mkdir(parents=True)

    saved: list[dict] = []

    for upload in files:
        if not upload.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=422,
                detail=f"{upload.filename} is not a PDF.",
            )

        dest = dossier_dir / upload.filename
        dest.write_bytes(await upload.read())

        saved.append({
            "original_name": upload.filename,
            "file_path": str(dest),
        })

    # Persist dossier + document rows, queue processing
    doc_ids = _manager.create_dossier(
        dossier_id=dossier_id,
        documents=saved,
    )

    background_tasks.add_task(
        _manager.process_dossier,
        dossier_id=dossier_id,
    )

    return JSONResponse(
        status_code=202,
        content={
            "dossier_id": dossier_id,
            "document_count": len(saved),
            "document_ids": doc_ids,
            "status": "processing",
            "status_url": f"/api/upload/{dossier_id}/status",
        },
    )


@router.get("/{dossier_id}/status", summary="Poll dossier processing status")
async def dossier_status(dossier_id: str) -> JSONResponse:
    """
    Returns the processing status for each document in the dossier.
    When all documents are 'done', the full extraction results are included.
    """
    result = _manager.get_status(dossier_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dossier {dossier_id} not found.",
        )

    return JSONResponse(content=result)
```

---

## DossierManager — `dossier_manager.py`

Create:

```text
backend/ai_pipeline/dossier_manager.py
```

```python
# backend/ai_pipeline/dossier_manager.py
"""
Manages dossier lifecycle:
  - Creating DB rows for a new dossier
  - Processing all documents in a dossier through the AI pipeline
  - Returning per-document status + extraction results
"""

import logging
import os
import uuid
from typing import Optional

from psycopg2.pool import ThreadedConnectionPool

from .pipeline import get_pipeline

logger = logging.getLogger(__name__)


class DossierManager:

    def __init__(self):
        self._pool: Optional[ThreadedConnectionPool] = None
        self._pipeline = get_pipeline()

        db_url = os.getenv("DATABASE_URL")
        if db_url:
            try:
                self._pool = ThreadedConnectionPool(
                    minconn=1,
                    maxconn=5,
                    dsn=db_url,
                )
                logger.info("DossierManager: DB pool ready")
            except Exception as exc:
                logger.warning("DossierManager: DB unavailable: %s", exc)

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def create_dossier(
        self,
        dossier_id: str,
        documents: list[dict],
    ) -> list[str]:
        """
        Insert dossier + document rows.
        Returns list of document_ids in insertion order.
        """
        doc_ids: list[str] = []

        if self._pool is None:
            # No DB — return synthetic IDs and continue
            return [str(uuid.uuid4()) for _ in documents]

        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO dossiers (id, status)
                    VALUES (%s, 'pending')
                    """,
                    (dossier_id,),
                )

                for doc in documents:
                    doc_id = str(uuid.uuid4())
                    cur.execute(
                        """
                        INSERT INTO dossier_documents (
                            id, dossier_id, original_name, file_path, status
                        )
                        VALUES (%s, %s, %s, %s, 'pending')
                        """,
                        (
                            doc_id,
                            dossier_id,
                            doc["original_name"],
                            doc["file_path"],
                        ),
                    )
                    doc_ids.append(doc_id)

            conn.commit()

        except Exception as exc:
            logger.warning("create_dossier DB error: %s", exc)
            if conn:
                conn.rollback()

        finally:
            if conn:
                self._pool.putconn(conn)

        return doc_ids

    # ------------------------------------------------------------------
    # PROCESS
    # ------------------------------------------------------------------

    def process_dossier(self, dossier_id: str) -> None:
        """
        Background task: process every document in the dossier through
        the AI pipeline (OCR → Classify → Extract → Normalize → Score).
        """
        docs = self._fetch_pending_docs(dossier_id)

        self._set_dossier_status(dossier_id, "processing")

        all_ok = True

        for doc in docs:
            doc_id   = doc["id"]
            pdf_path = doc["file_path"]

            self._set_document_status(doc_id, "processing")

            try:
                result = self._pipeline.process_document(
                    pdf_path=pdf_path,
                    document_id=doc_id,
                )

                self._save_result(
                    doc_id=doc_id,
                    document_type=result.get("document_type"),
                    extraction_json=result,
                )

                self._set_document_status(doc_id, "done")

            except Exception as exc:
                logger.exception(
                    "process_dossier: doc %s failed",
                    doc_id,
                )
                self._set_document_status(
                    doc_id,
                    "error",
                    error_message=str(exc),
                )
                all_ok = False

        final_status = "done" if all_ok else "error"
        self._set_dossier_status(dossier_id, final_status)

    # ------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------

    def get_status(self, dossier_id: str) -> Optional[dict]:
        """
        Return dossier + per-document status.
        Returns None if not found.
        """
        if self._pool is None:
            return None

        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT id, status, created_at
                    FROM dossiers
                    WHERE id = %s
                    """,
                    (dossier_id,),
                )
                row = cur.fetchone()

                if row is None:
                    return None

                dossier_status = {
                    "dossier_id":  str(row[0]),
                    "status":      row[1],
                    "created_at":  row[2].isoformat(),
                }

                cur.execute(
                    """
                    SELECT
                        id,
                        original_name,
                        document_type,
                        status,
                        error_message,
                        extraction_json
                    FROM dossier_documents
                    WHERE dossier_id = %s
                    ORDER BY created_at
                    """,
                    (dossier_id,),
                )
                doc_rows = cur.fetchall()

                dossier_status["documents"] = [
                    {
                        "document_id":     str(r[0]),
                        "original_name":   r[1],
                        "document_type":   r[2],
                        "status":          r[3],
                        "error_message":   r[4],
                        "extraction_result": r[5],
                    }
                    for r in doc_rows
                ]

                return dossier_status

        except Exception as exc:
            logger.warning("get_status DB error: %s", exc)
            return None

        finally:
            if conn:
                self._pool.putconn(conn)

    # ------------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------------

    def _fetch_pending_docs(
        self,
        dossier_id: str,
    ) -> list[dict]:
        if self._pool is None:
            return []

        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, file_path
                    FROM dossier_documents
                    WHERE dossier_id = %s
                      AND status = 'pending'
                    ORDER BY created_at
                    """,
                    (dossier_id,),
                )
                return [
                    {"id": str(r[0]), "file_path": r[1]}
                    for r in cur.fetchall()
                ]
        except Exception as exc:
            logger.warning("_fetch_pending_docs: %s", exc)
            return []
        finally:
            if conn:
                self._pool.putconn(conn)

    def _set_dossier_status(
        self,
        dossier_id: str,
        status: str,
    ) -> None:
        self._run_sql(
            """
            UPDATE dossiers
            SET status = %s
            WHERE id = %s
            """,
            (status, dossier_id),
        )

    def _set_document_status(
        self,
        doc_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        self._run_sql(
            """
            UPDATE dossier_documents
            SET status = %s,
                error_message = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (status, error_message, doc_id),
        )

    def _save_result(
        self,
        doc_id: str,
        document_type: Optional[str],
        extraction_json: dict,
    ) -> None:
        import json
        self._run_sql(
            """
            UPDATE dossier_documents
            SET document_type   = %s,
                extraction_json = %s,
                status          = 'done',
                updated_at      = NOW()
            WHERE id = %s
            """,
            (
                document_type,
                json.dumps(extraction_json),
                doc_id,
            ),
        )

    def _run_sql(self, sql: str, params: tuple) -> None:
        if self._pool is None:
            return
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()
        except Exception as exc:
            logger.warning("DossierManager SQL error: %s", exc)
            if conn:
                conn.rollback()
        finally:
            if conn:
                self._pool.putconn(conn)
```

---

## API Response Contract

### `POST /api/upload` — 202 Accepted

```json
{
  "dossier_id": "a1b2c3d4-...",
  "document_count": 3,
  "document_ids": [
    "doc-uuid-1",
    "doc-uuid-2",
    "doc-uuid-3"
  ],
  "status": "processing",
  "status_url": "/api/upload/a1b2c3d4-.../status"
}
```

### `GET /api/upload/{dossier_id}/status` — 200 OK

```json
{
  "dossier_id": "a1b2c3d4-...",
  "status": "done",
  "created_at": "2026-09-24T10:00:00Z",
  "documents": [
    {
      "document_id": "doc-uuid-1",
      "original_name": "invoice.pdf",
      "document_type": "commercial_invoice",
      "status": "done",
      "error_message": null,
      "extraction_result": {
        "document_id": "doc-uuid-1",
        "document_type": "commercial_invoice",
        "classification_confidence": 0.97,
        "entities": [ "..." ],
        "raw_ocr": [ "..." ],
        "processing_time_ms": 3200,
        "errors": []
      }
    },
    {
      "document_id": "doc-uuid-2",
      "original_name": "packing_list.pdf",
      "document_type": "packing_list",
      "status": "done",
      "error_message": null,
      "extraction_result": { "..." }
    },
    {
      "document_id": "doc-uuid-3",
      "original_name": "awb.pdf",
      "document_type": "awb",
      "status": "processing",
      "error_message": null,
      "extraction_result": null
    }
  ]
}
```

---

## Full Updated Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│                    HTTP CLIENT / FRONTEND                       │
└────────────────────────────┬────────────────────────────────────┘
                             │  POST /api/upload
                             │  files=[invoice.pdf, packing.pdf, awb.pdf]
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│             FastAPI  upload_router.py                           │
│  • validate PDFs                                                │
│  • generate dossier_id (UUID)                                   │
│  • save to uploads/{dossier_id}/                                │
│  • INSERT → dossiers + dossier_documents (PostgreSQL)           │
│  • enqueue BackgroundTask → DossierManager.process_dossier()    │
│  • return 202 { dossier_id, status_url }                        │
└────────────────────────────┬────────────────────────────────────┘
                             │  background
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           DossierManager.process_dossier()                      │
│           (one iteration per PDF in the dossier)                │
└──────────────────┬──────────────────────────────────────────────┘
                   │  per document
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                 AIPipeline.process_document()                   │
│                                                                 │
│  Step 1  PaddleOCR ──────────────────────── bounding boxes      │
│  Step 2  DocumentClassifier ─────────────── doc_type + conf     │
│  Step 3  EntityExtractor (Gemini Vision) ── raw entity list     │
│  Step 4  EntityNormalizer ────────────────── normalized fields  │
│            ├─ Deterministic rules (weight/vol/date/id)          │
│            └─ Semantic: Tier1 key → PostgreSQL → Gemini         │
│  Step 5  ConfidenceScorer ────────────────── confidence scores  │
│                                                                 │
│  → ExtractionResult JSON                                        │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
      UPDATE dossier_documents
      SET extraction_json = ..., status = 'done'
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│        GET /api/upload/{dossier_id}/status                      │
│        Returns per-document status + ExtractionResult JSON      │
└──────────────────┬──────────────────────────────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
   Aloka / Graph       Kaveen / UI
   Cross-doc           PDF BBox
   comparison          Overlay
   Conflict det.       Entity display
```

---

## Multi-file Grouping Logic

All documents uploaded in a single `POST /api/upload` request are grouped under one `dossier_id`. This dossier represents one physical shipment.

```text
dossier_id: a1b2c3d4
  ├── doc-1: invoice.pdf      → commercial_invoice
  ├── doc-2: packing_list.pdf → packing_list
  ├── doc-3: awb.pdf          → awb
  └── doc-4: bl.pdf           → bl
```

Downstream, Aloka's discrepancy engine receives the entire dossier's `extraction_json` fields grouped by `dossier_id`. This is how cross-document comparison is scoped — only documents in the same dossier are compared against each other.

---

## Dossier Status State Machine

```text
         ┌──────────┐
         │ pending  │  (created, waiting for background task)
         └────┬─────┘
              │
              ▼
       ┌────────────┐
       │ processing │  (at least one document still running)
       └─────┬──────┘
             │
      ┌──────┴──────┐
      ▼             ▼
  ┌──────┐      ┌───────┐
  │ done │      │ error │  (at least one document failed)
  └──────┘      └───────┘
```

Document-level status follows the same states independently.

---

## Gemini Entity Extraction Integration

Phase 06's `EntityExtractor` uses **Gemini Vision** to extract raw entity strings from document images. Phase 09's `EntityNormalizer` then processes each raw string. The pipeline wires them together in Step 3 → Step 4.

The entity extractor already uses the updated `google-genai` SDK:

```python
# entity_extractor.py — Phase 06 (already implemented)
# Sends document image to Gemini Vision
# Returns raw entity dict {"GROSS_WEIGHT": "450.00 KG", ...}
```

Phase 09 receives these raw strings and applies the full three-tier normalization:

```text
Gemini Vision output:
  "GROSS_WEIGHT": "450.00 KG"

Phase 09 Deterministic Rule:
  normalized_value: 450.0
  unit: "kg"
  warn: false

Gemini Vision output:
  "PORT_LOADING": "Colombo Custom Port"

Phase 09 Semantic Tier:
  Tier 1 key: PORT_LOADING:colombo custom port
  Tier 2 DB:  HIT → "Colombo Port (LKCMB)"
  normalized_value: "Colombo Port (LKCMB)"
```

---

## Acceptance Criteria — Dossier Upload

- [ ] `POST /api/upload` accepts 1–N PDFs in one request
- [ ] Returns `dossier_id` and `status_url` immediately (202)
- [ ] Each file is saved to `uploads/{dossier_id}/{filename}`
- [ ] `dossiers` and `dossier_documents` rows are created before 202 response
- [ ] Background processing runs per document through the full AI pipeline
- [ ] `GET /api/upload/{dossier_id}/status` returns per-document status
- [ ] Status correctly transitions: `pending → processing → done | error`
- [ ] `extraction_json` is populated in DB when document is `done`
- [ ] Non-PDF uploads return `422 Unprocessable Entity`
- [ ] Unknown `dossier_id` returns `404 Not Found`
- [ ] DB unavailable degrades gracefully — pipeline still runs
- [ ] Concurrent uploads each get their own `dossier_id` and directory

---

## New Files to Create

```text
backend/
  api/
    __init__.py
    upload_router.py          ← POST /api/upload + GET status
  ai_pipeline/
    dossier_manager.py        ← DossierManager class
```

Update `backend/schema.sql` with the `dossiers` and `dossier_documents` tables.

Update `backend/main.py` (or equivalent FastAPI entrypoint) to include:

```python
from api.upload_router import router as upload_router
app.include_router(upload_router)
```

---

# Phase 09 + Dossier Definition of Done

```text
PDF files
    │
    ▼
POST /api/upload
    │
    ├─ dossier_id assigned
    ├─ Files saved
    ├─ DB rows created
    └─ Background processing started
              │
              ▼
    per document:
    PaddleOCR → Gemini Extraction → Normalization → Confidence Scoring
              │
              ▼
    extraction_json → DB
              │
              ▼
GET /api/upload/{dossier_id}/status → all done
              │
              ├──→ Aloka Knowledge Graph (cross-document comparison)
              └──→ Kaveen Frontend (PDF bbox overlay + entity display)
```

The core principle is:

> **Upload once, process asynchronously, poll for status. Each dossier groups one shipment's documents. Normalization runs inside the pipeline on every entity — deterministic rules first, PostgreSQL cache second, Gemini only as a last resort. Raw values are always preserved. No failure in upload, processing, DB, or LLM should crash the system.**
