# Phase 02 — FastAPI Skeleton + Upload Endpoint

> **Priority:** MUST
> **Estimated Time:** 1 hour
> **Dependencies:** None
> **Blocks:** Phase 04 (upload UI needs this endpoint)

---

## Goal

Create the FastAPI backend application shell with CORS configuration and the file upload endpoint. **Coordinate with Aloka** — he creates the mock data endpoints in his Phase 02. You own `main.py` and the upload route.

## Why

The upload endpoint is the first API the frontend calls. Without it, the upload page can't function. CORS must be configured or every API call from the React dev server will be blocked.

## Implementation

### 2.1 Create `backend/main.py`

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="ClearanceX API",
    description="6-Layer Explainable AI Copilot for Customs Declaration Compliance",
    version="0.1.0"
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Fallback
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files statically (for PDF viewer)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "service": "clearancex", "version": "0.1.0"}

# Import routes from Aloka's api module
# from api.routes import router
# app.include_router(router)
```

### 2.2 Create Upload Endpoint

```python
# backend/api/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
import os
import shutil

router = APIRouter(prefix="/api")

UPLOAD_DIR = "uploads"

@router.post("/shipments/upload")
async def upload_shipment(files: List[UploadFile] = File(...)):
    """
    Upload a shipping dossier (multiple PDF files).
    Returns shipment_id and document list.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate all files are PDFs
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files accepted. '{file.filename}' is not a PDF."
            )
    
    shipment_id = str(uuid.uuid4())
    shipment_dir = os.path.join(UPLOAD_DIR, shipment_id)
    os.makedirs(shipment_dir, exist_ok=True)
    
    documents = []
    for file in files:
        doc_id = str(uuid.uuid4())
        safe_filename = f"{doc_id}_{file.filename}"
        file_path = os.path.join(shipment_dir, safe_filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        documents.append({
            "document_id": doc_id,
            "filename": file.filename,
            "file_path": file_path,
            "status": "uploaded"
        })
    
    # TODO: Trigger AI pipeline processing asynchronously (Phase 14 integration)
    # For now, return immediately
    
    return {
        "shipment_id": shipment_id,
        "status": "processing",
        "document_count": len(documents),
        "documents": documents
    }
```

### 2.3 Create `.env` and Requirements

```bash
# backend/.env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/clearancex
GEMINI_API_KEY=your_key_here
UPLOAD_DIR=uploads
```

```
# backend/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-dotenv==1.0.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.2
```

### 2.4 Run the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` → Swagger UI should show all endpoints.

### 2.5 Test Upload from Frontend

```bash
# Quick test with curl
curl -X POST http://localhost:8000/api/shipments/upload \
  -F "files=@sample_invoice.pdf" \
  -F "files=@sample_packing_list.pdf"
```

## Acceptance Criteria

- [ ] `uvicorn main:app --reload` starts on port 8000
- [ ] `/health` returns `{"status": "ok"}`
- [ ] `/docs` shows Swagger UI
- [ ] CORS allows requests from `localhost:5173`
- [ ] Upload endpoint accepts multiple PDFs
- [ ] Upload endpoint rejects non-PDF files
- [ ] Files are saved to `uploads/{shipment_id}/` directory
- [ ] Returns `shipment_id` + document list

## Outputs

- `backend/main.py` — FastAPI app
- `backend/api/upload.py` — upload endpoint
- `backend/requirements.txt`
- Working backend serving uploaded files statically
