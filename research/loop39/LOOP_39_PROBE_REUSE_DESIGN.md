# DOCUREADY — LOOP 39 PROBE REUSE DESIGN

**Decision: Do NOT substitute thumbnail probe text for full-resolution OCR evidence.**
- The probe crops only 30% of the page area (`0.15w..0.85w, 0.25h..0.55h`) and resizes to `<=450px`, discarding headers, footers, table margins, and high-DPI character geometry needed for `image_to_data` bounding boxes and critical fields.
- Retains full-resolution OCR for all evidentiary extraction.
