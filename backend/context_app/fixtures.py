"""Explicit synthetic fixtures; never a fallback for OCR failures."""
import hashlib
import uuid
from .config import DATA_ROOT


def write_pdf(path, lines):
    """Produce a small valid PDF with actual text that matches its fixture assertions."""
    escaped = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    stream = "BT /F1 14 Tf 50 790 Td " + " ".join(f"({line}) Tj 0 -24 Td" for line in escaped) + " ET"
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", f"<< /Length {len(stream.encode())} >>\nstream\n{stream}\nendstream"]
    data, offsets = b"%PDF-1.4\n", [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += f"{index} 0 obj\n{obj}\nendobj\n".encode()
    start = len(data)
    data += f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode()
    data += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    data += f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def fixture_document(kind, weight, package_count=None):
    did = str(uuid.uuid4())
    values = [("GROSS_WEIGHT", f"{weight} kg", weight, "kg")]
    if package_count is not None:
        values.append(("PACKAGE_COUNT", str(package_count), package_count, None))
    path = DATA_ROOT / "synthetic" / (did + ".pdf")
    title = kind.replace("_", " ").title()
    content_hash = write_pdf(path, ["SYNTHETIC DEMO - NOT A REAL SHIPMENT", title] + [f"{field}: {raw}" for field, raw, _, _ in values])
    return {"document_id": did, "document_type": kind, "source_filename": title + ".pdf", "source_label": title,
        "revision": 1, "fixture": True, "file_path": str(path), "content_hash": content_hash,
        "classification_confidence": 1.0, "warnings": ["Precomputed synthetic extraction; not live OCR."],
        "entities": [{"entity_type": field, "value": raw, "normalized_value": value, "unit": unit,
            "page": 1, "bbox": [], "extraction_confidence": 0.0, "classification_confidence": 1.0,
            "source_method": "synthetic_fixture", "confidence_status": "not_measured"}
            for field, raw, value, unit in values], "raw_ocr": [], "errors": []}


def hero_documents():
    return [fixture_document("commercial_invoice", 450, 12), fixture_document("packing_list", 450), fixture_document("awb", 440)]
