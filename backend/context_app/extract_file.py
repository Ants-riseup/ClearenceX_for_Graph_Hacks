"""Bounded subprocess entrypoint: optional local OCR only."""
import json
import os
import sys
from pathlib import Path

os.environ["CLEARANCEX_LOCAL_EXTRACTION"] = "true"
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""

if __name__ == "__main__":
    from ai_pipeline.pipeline import get_pipeline
    result = get_pipeline().process_document(sys.argv[1], sys.argv[2])
    Path(sys.argv[3]).write_text(json.dumps(result, allow_nan=False), encoding="utf-8")
