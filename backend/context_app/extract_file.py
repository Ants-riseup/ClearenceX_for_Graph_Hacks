"""Bounded subprocess entrypoint: optional local OCR only."""
import json
import os
import sys
from pathlib import Path

os.environ["CLEARANCEX_LOCAL_EXTRACTION"] = "true"
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""

if __name__ == "__main__":
    if sys.platform != 'win32':
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 ** 3, 2 * 1024 ** 3))
        resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    from .text_extract import extract
    result = extract(sys.argv[1], sys.argv[2])
    if result is None:
        from ai_pipeline.pipeline import get_pipeline
        result = get_pipeline().process_document(sys.argv[1], sys.argv[2])
    Path(sys.argv[3]).write_text(json.dumps(result, allow_nan=False), encoding="utf-8")
