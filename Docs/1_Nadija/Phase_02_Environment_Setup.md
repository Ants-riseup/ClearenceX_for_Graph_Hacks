# Phase 01 — Environment Setup + PaddleOCR Installation

> **Priority:** MUST
> **Estimated Time:** 1–2 hours
> **Dependencies:** None
> **Blocks:** All subsequent phases

---

## Goal

Set up the Python AI/ML environment with all required dependencies so you can immediately start building the extraction pipeline.

## Why

Every other phase depends on PaddleOCR and the ML libraries being installed and working. Getting environment issues out of the way first prevents blocking later.

## Tasks

### 1.1 Create Python Virtual Environment

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 1.2 Install Core Dependencies

```bash
pip install paddlepaddle paddleocr
pip install torch torchvision
pip install transformers  # For LayoutLMv3
pip install Pillow pdf2image PyMuPDF
pip install google-generativeai  # Gemini Vision fallback
pip install networkx  # Aloka will use this, but install now
pip install python-dotenv
```

### 1.3 Install Project Dependencies

```bash
pip install fastapi uvicorn python-multipart pydantic sqlalchemy psycopg2-binary
```

### 1.4 Verify PaddleOCR Works

Create a quick test script:

```python
# backend/ai_pipeline/test_setup.py
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='en')
result = ocr.ocr('path/to/any/test.pdf', cls=True)

for page in result:
    for line in page:
        bbox = line[0]
        text = line[1][0]
        confidence = line[1][1]
        print(f"Text: {text}, Confidence: {confidence:.2f}, BBox: {bbox}")
```

### 1.5 Verify Gemini Vision API (Fallback)

```python
# backend/ai_pipeline/test_gemini.py
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# Test with a simple prompt
response = model.generate_content("Hello, test connection")
print(response.text)
```

### 1.6 Create .env File

```bash
# backend/.env
GEMINI_API_KEY=your_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/clearancex
```

### 1.7 Create Directory Structure

```
backend/ai_pipeline/
├── __init__.py
├── ocr_engine.py
├── classifier.py
├── entity_extractor.py
├── normalizer.py
├── confidence.py
├── pipeline.py
├── mock_pipeline.py
├── models/
│   └── .gitkeep
└── test_setup.py
```

## Acceptance Criteria

- [ ] PaddleOCR runs successfully on a sample PDF
- [ ] Bounding boxes are returned for each text region
- [ ] Gemini Vision API connects and responds
- [ ] All dependencies install without conflicts
- [ ] Directory structure created

## Outputs

- Working Python environment with all AI/ML dependencies
- Verified PaddleOCR and Gemini Vision connections

## Notes

- If PaddleOCR has GPU issues on Windows, use CPU mode: `PaddleOCR(use_gpu=False)`
- If `pdf2image` needs poppler, install it: `conda install -c conda-forge poppler` or download Windows binaries
