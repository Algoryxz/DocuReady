# DocuReady Loop 32 OCR & Extraction Audit

**Programme:** DocuReady Product Excellence  
**Focus:** Ingestion Pipeline, Tesseract OCR, PyMuPDF Vector Text, Table Association  
**Date:** 2026-11-25  

---

## 1. Subsystem Architecture

The extraction pipeline supports a dual-path architecture:
1. **Native Vector Path (Fast-path):** For born-digital PDFs, PyMuPDF (`fitz`) extracts text tokens, font properties, and vector bounding boxes in under 15 ms per page.
2. **Raster / Scanned OCR Path:** For scanned documents, images are preprocessed (grayscale, Otsu thresholding, skew correction), fed to bundled Tesseract OCR 5.3.3, and mapped to token bounding boxes.

---

## 2. Key Findings & Defect Analysis

- **Tuple Bounding Box Compatibility (BUG-032-001):** Fixed in `extractor.py` to allow pluggable backends returning 4-tuples without crashing.
- **Landscape Scaling Distortions (BUG-032-006):** In `region_ocr.py`, portrait width 595.0 pt was assumed; landscape bounding boxes need dynamic aspect ratio handling. Documented as Technical Debt.
- **Table Association Column Gutters (BUG-032-007):** In `table_association.py`, fixed 35 px threshold fails on narrow columns in dense schedules. Documented as Technical Debt.
