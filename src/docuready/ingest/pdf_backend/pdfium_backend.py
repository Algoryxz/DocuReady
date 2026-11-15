"""pypdfium2 prototype implementation of PDF backend interfaces."""

from __future__ import annotations

import io
from typing import List, Tuple

import PIL.Image

from docuready.ingest.pdf_backend.base import PDFDocumentBackend, PDFPageBackend

try:
    import pypdfium2 as pdfium

    _PYPDFIUM2_AVAILABLE = True
except ImportError:
    pdfium = None  # type: ignore
    _PYPDFIUM2_AVAILABLE = False


class PdfiumPageBackend(PDFPageBackend):
    """Wraps a pypdfium2 page object to implement PDFPageBackend."""

    def __init__(self, page, page_number: int):
        if not _PYPDFIUM2_AVAILABLE:
            raise ImportError(
                "pypdfium2 is not installed in the active environment. "
                "Install with optional extra or pip install pypdfium2"
            )
        self._page = page
        self._page_number = page_number
        width, height = self._page.get_size()
        self._rect = (0.0, 0.0, float(width), float(height))

    @property
    def page_number(self) -> int:
        return self._page_number

    @property
    def rect(self) -> Tuple[float, float, float, float]:
        return self._rect

    def get_text(self) -> str:
        textpage = self._page.get_textpage()
        return textpage.get_text_range()

    def search_for(self, needle: str) -> List[Tuple[float, float, float, float]]:
        textpage = self._page.get_textpage()
        searcher = textpage.search(needle)
        results: List[Tuple[float, float, float, float]] = []
        match = searcher.get_next()
        while match:
            # pdfium returns list of rects for the match; normalize to (x0, y0, x1, y1)
            rects = searcher.get_rectboxes()
            for r in rects:
                results.append((float(r[0]), float(r[1]), float(r[2]), float(r[3])))
            match = searcher.get_next()
        return results

    def get_words(self) -> List[Tuple[float, float, float, float, str, int, int, int]]:
        """Extract individual words and their bounding boxes.

        Raises NotImplementedError: word-level bounding box provenance with block/line
        structure is currently only supported by the PyMuPDF backend (PyMuPDFBackend).
        Returning fake or zero-coordinate bounding boxes is strictly prohibited to
        preserve provenance integrity.
        """
        raise NotImplementedError(
            "Word-level bounding box provenance (get_words) is not implemented for "
            "PdfiumPageBackend. Word-level coordinate extraction requires the PyMuPDF "
            "backend (pymupdf). Returning zero or synthetic bounding boxes is disallowed "
            "to prevent provenance corruption."
        )

    def render_to_image(self, dpi: int = 200) -> PIL.Image.Image:
        scale = dpi / 72.0
        pil_image = self._page.render(scale=scale).to_pil()
        return pil_image.convert("RGB")


class PdfiumDocumentBackend(PDFDocumentBackend):
    """Wraps a pypdfium2 PdfDocument object to implement PDFDocumentBackend."""

    def __init__(self, file_path: str):
        if not _PYPDFIUM2_AVAILABLE:
            raise ImportError(
                "pypdfium2 is not installed in the active environment. "
                "Install with optional extra or pip install pypdfium2"
            )
        super().__init__(file_path)
        self._doc = pdfium.PdfDocument(file_path)

    @property
    def page_count(self) -> int:
        return len(self._doc)

    def get_page(self, index: int) -> PDFPageBackend:
        if index < 0 or index >= len(self._doc):
            raise IndexError(f"Page index {index} out of range (0..{len(self._doc) - 1})")
        return PdfiumPageBackend(self._doc[index], index)

    def close(self) -> None:
        if self._doc is not None:
            self._doc.close()
