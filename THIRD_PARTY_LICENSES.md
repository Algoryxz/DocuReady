# DOCUREADY — THIRD-PARTY LICENSES & ATTRIBUTION

**Milestone:** Loop 6 — Release Integrity, Claims Audit & Independent Reproducibility  
**Date:** 2026-11-16  
**Repository:** `Algoryxz/DocuReady`  

---

## 1. Overview of License Categories

The third-party components included in DocuReady or its binary distribution fall into three primary licensing categories:

1. **Permissive Open Source (Permits redistribution without source disclosure):**
   - **Apache License 2.0:** DocuReady Core, Tesseract OCR, PDF.js (`pdfjs-dist`), TypeScript.
   - **MIT License:** Electron, React, React-DOM, Vite, Lucide React, Pydantic, Squirrel.Windows.
   - **BSD 2-Clause / 3-Clause:** Leptonica, NumPy, libwebp.
   - **zlib / Libpng / IJG:** zlib1, libpng16, libjpeg-62, libtiff-5.

2. **Copyleft Open Source (Requires source code disclosure of combined work under reciprocal terms):**
   - **GNU Affero General Public License v3 (AGPLv3):** PyMuPDF (`fitz`) and underlying MuPDF C library.

3. **Special Exception Copyleft:**
   - **GPLv2 with Bootloader Exception:** PyInstaller bootloader (`docuready_sidecar.exe`).

---

## 2. Copyleft Component: PyMuPDF / MuPDF (AGPLv3)

### Details
- **Component:** PyMuPDF (`fitz`)
- **Copyright:** © 2015–2024 Artifex Software, Inc.
- **License:** GNU Affero General Public License v3.0 (AGPLv3)
- **URL:** https://www.artifex.com / https://github.com/pymupdf/PyMuPDF

### Licensing Terms & Copyleft Implications
Under Section 5 and 6 of AGPLv3, if an application links or combines with PyMuPDF and conveys the resulting work to third parties, the entire combined work must generally be licensed under AGPLv3, and source code must be made available to all recipients (and network users under Section 13).

### DocuReady Compliance Status:
1. **Source Code Availability:** DocuReady is completely open-source and hosted publicly on GitHub at `https://github.com/Algoryxz/DocuReady` under Apache 2.0.
2. **Process Boundary Isolation:** In the desktop architecture, PyMuPDF runs inside the independent `docuready_sidecar.exe` process, communicating with the Electron desktop shell exclusively over stdio JSON-RPC.
3. **Enterprise Copyleft Consideration:** While DocuReady's own source code is open, downstream corporate users who embed DocuReady into proprietary systems may face copyleft obligations under AGPLv3. See `LICENSING_DECISION.md` for a complete evaluation of the PDFium alternative.

---

## 3. Tesseract OCR Engine (Apache 2.0) & Leptonica (BSD 2-Clause)

### Tesseract OCR
- **Copyright:** © 2018 Google LLC and contributors.
- **License:** Apache License, Version 2.0.
- **Notice Requirements:** Preserved in `resources/docuready_sidecar/tesseract/LICENSE` and `AUTHORS`.

### Leptonica Image Processing Library
- **Copyright:** © 2001–2024 Dan Bloomberg and contributors.
- **License:** 2-Clause BSD License.
```text
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice...
2. Redistributions in binary form must reproduce the above copyright notice...
```
- **Notice Requirements:** Included in the distribution `NOTICE` file.

### Traineddata Models (`eng.traineddata`, `osd.traineddata`)
- **Copyright:** © Google LLC.
- **Source:** `tesseract-ocr/tessdata_fast` repository.
- **License:** Apache License, Version 2.0.

---

## 4. PDF.js (`pdfjs-dist`) (Apache 2.0)

- **Copyright:** © 2012–2024 Mozilla Foundation and individual contributors.
- **License:** Apache License, Version 2.0.
- **Role:** Client-side vector canvas renderer in React renderer (`apps/desktop`).

---

## 5. Electron Shell & Frontend Stack (MIT License)

- **Electron:** Copyright © OpenJS Foundation and Electron contributors.
- **React & React-DOM:** Copyright © Meta Platforms, Inc. and affiliates.
- **Vite:** Copyright © 2019-present Evan You & Vite Contributors.
- **Pydantic:** Copyright © 2019 Samuel Colvin.

```text
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```
