"""PyMuPDF (fitz) implementation of PDF backend interfaces."""

from __future__ import annotations

import io
from typing import List, Tuple

import PIL.Image
import pymupdf

from docuready.ingest.pdf_backend.base import PDFDocumentBackend, PDFPageBackend


class PyMuPDFPageBackend(PDFPageBackend):
    """Wraps a pymupdf.Page object to implement PDFPageBackend."""

    def __init__(self, page: pymupdf.Page, page_number: int):
        self._page = page
        self._page_number = page_number

    @property
    def page_number(self) -> int:
        return self._page_number

    @property
    def rect(self) -> Tuple[float, float, float, float]:
        r = self._page.rect
        return (float(r.x0), float(r.y0), float(r.x1), float(r.y1))

    def get_text(self) -> str:
        return self._page.get_text()

    def search_for(self, needle: str) -> List[Tuple[float, float, float, float]]:
        rects = self._page.search_for(needle)
        return [(float(r.x0), float(r.y0), float(r.x1), float(r.y1)) for r in rects]

    def get_words(self) -> List[Tuple[float, float, float, float, str, int, int, int]]:
        raw_words = self._page.get_text("words")
        return [
            (
                float(w[0]),
                float(w[1]),
                float(w[2]),
                float(w[3]),
                str(w[4]),
                int(w[5]),
                int(w[6]),
                int(w[7]),
            )
            for w in raw_words
        ]

    def render_to_image(self, dpi: int = 200) -> PIL.Image.Image:
        # Enforce decompression bomb prevention: limit DPI if page is huge
        r = self.rect
        area = (r[2] - r[0]) * (r[3] - r[1])
        effective_dpi = 72 if area > 2000 * 2000 else dpi
        pix = self._page.get_pixmap(dpi=effective_dpi)
        try:
            img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        except Exception:
            img = PIL.Image.open(io.BytesIO(pix.tobytes())).convert("RGB")
        finally:
            pix = None
        return img

    @property
    def raw_page(self) -> pymupdf.Page:
        """Access underlying pymupdf Page for low-level compatibility."""
        return self._page


class PyMuPDFDocumentBackend(PDFDocumentBackend):
    """Wraps a pymupdf.Document object to implement PDFDocumentBackend."""

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self._doc = pymupdf.open(file_path)

    @property
    def page_count(self) -> int:
        return len(self._doc)

    def get_page(self, index: int) -> PDFPageBackend:
        if index < 0 or index >= len(self._doc):
            raise IndexError(f"Page index {index} out of range (0..{len(self._doc) - 1})")
        return PyMuPDFPageBackend(self._doc[index], index)

    def close(self) -> None:
        if self._doc is not None and not self._doc.is_closed:
            self._doc.close()

    @property
    def raw_doc(self) -> pymupdf.Document:
        """Access underlying pymupdf Document for low-level compatibility."""
        return self._doc
