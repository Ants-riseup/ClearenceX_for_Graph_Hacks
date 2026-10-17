# Phase 04 — Upload Page (Drag & Drop Multi-PDF)

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phase 02 (upload API), Phase 03 (app shell)
> **Blocks:** Phase 06 (Review page needs a shipment to review)

---

## Goal

Build the upload page with drag-and-drop multi-PDF upload, file list management, and submission to the backend. After successful upload, navigate to the review page.

## Implementation

```tsx
// frontend/src/pages/UploadPage.tsx
import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadShipment } from '../utils/api';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setError(null);
    const pdfFiles = acceptedFiles.filter(f => f.name.toLowerCase().endsWith('.pdf'));
    if (pdfFiles.length !== acceptedFiles.length) {
      setError('Some files were skipped — only PDFs are accepted.');
    }
    setFiles(prev => [...prev, ...pdfFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
  });

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setError(null);

    try {
      const result = await uploadShipment(files);
      // Navigate to review page
      navigate(`/review/${result.shipment_id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Upload failed. Please try again.');
      setUploading(false);
    }
  };

  return (
    <div className="upload-page animate-fade-in">
      <div className="upload-header">
        <h1>Upload Shipping Dossier</h1>
        <p className="upload-subtitle">
          Upload your shipping documents (Commercial Invoice, Packing List, AWB, B/L, etc.)
          and ClearanceX will extract, reconcile, and explain every discrepancy.
        </p>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`dropzone glass-card ${isDragActive ? 'dropzone-active' : ''} ${files.length > 0 ? 'dropzone-has-files' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="dropzone-content">
          <div className={`dropzone-icon ${isDragActive ? 'dropzone-icon-active' : ''}`}>
            <Upload size={48} strokeWidth={1.5} />
          </div>
          <h3>{isDragActive ? 'Drop your PDFs here' : 'Drag & drop PDF documents'}</h3>
          <p>or click to browse files</p>
          <span className="dropzone-hint">
            Accepted: Commercial Invoice, Packing List, AWB, B/L, Freight Invoice, DO, LC
          </span>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="file-list glass-card">
          <div className="file-list-header">
            <h3>Selected Documents ({files.length})</h3>
          </div>
          <div className="file-list-items">
            {files.map((file, index) => (
              <div key={`${file.name}-${index}`} className="file-item animate-slide-in">
                <div className="file-item-info">
                  <FileText size={20} className="file-icon" />
                  <div>
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">{(file.size / 1024).toFixed(0)} KB</span>
                  </div>
                </div>
                <button
                  className="file-remove"
                  onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                  disabled={uploading}
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="upload-error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Submit Button */}
      {files.length > 0 && (
        <button
          className="btn btn-primary upload-submit"
          onClick={handleSubmit}
          disabled={uploading}
        >
          {uploading ? (
            <>
              <Loader2 size={18} className="spin" />
              Processing Dossier...
            </>
          ) : (
            <>
              <CheckCircle size={18} />
              Process {files.length} Document{files.length > 1 ? 's' : ''}
            </>
          )}
        </button>
      )}
    </div>
  );
};
```

### Upload Page CSS

```css
/* Add to index.css */

.upload-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 40px 0;
}

.upload-header {
  margin-bottom: 32px;
}

.upload-header h1 {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.upload-subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
  line-height: 1.6;
}

.dropzone {
  padding: 60px 40px;
  text-align: center;
  cursor: pointer;
  border: 2px dashed var(--border-medium);
  margin-bottom: 20px;
  transition: all var(--transition-normal);
}

.dropzone:hover,
.dropzone-active {
  border-color: var(--accent-primary);
  background: rgba(99, 102, 241, 0.05);
  box-shadow: var(--shadow-glow);
}

.dropzone-content h3 {
  font-size: 1.2rem;
  margin: 16px 0 4px;
}

.dropzone-content p {
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.dropzone-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.dropzone-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-elevated);
  border-radius: 50%;
  color: var(--accent-primary);
  transition: all var(--transition-normal);
}

.dropzone-icon-active {
  background: var(--accent-primary);
  color: white;
  transform: scale(1.1);
}

.file-list {
  padding: 16px;
  margin-bottom: 20px;
}

.file-list-header {
  padding: 0 8px 12px;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 8px;
}

.file-list-header h3 {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.file-item:hover {
  background: var(--bg-card-hover);
}

.file-item-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  color: var(--accent-primary);
}

.file-name {
  display: block;
  font-weight: 500;
  font-size: 0.9rem;
}

.file-size {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.file-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.file-remove:hover {
  color: var(--sev-high);
  background: rgba(239, 68, 68, 0.1);
}

.upload-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-md);
  color: var(--sev-high);
  font-size: 0.875rem;
  margin-bottom: 16px;
}

.upload-submit {
  width: 100%;
  justify-content: center;
  padding: 14px;
  font-size: 1rem;
}

.spin {
  animation: spin 1s linear infinite;
}
```

## Acceptance Criteria

- [ ] Drag-and-drop zone accepts multiple PDFs
- [ ] Rejects non-PDF files with error message
- [ ] File list shows name, size, remove button
- [ ] "Process" button sends files to upload API
- [ ] Loading state shows spinner during upload
- [ ] On success → navigates to `/review/:shipmentId`
- [ ] Error states display clearly
- [ ] Dropzone glows on drag-over
- [ ] Animations are smooth (fade-in, slide-in)
