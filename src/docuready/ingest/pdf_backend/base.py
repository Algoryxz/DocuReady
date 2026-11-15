"""Abstract base interface for PDF parsing, text extraction, and page rendering.

Provides a pluggable abstraction layer over PDF processing engines (e.g. PyMuPDF, pypdfium2),
allowing DocuReady to decouple document processing from specific underlying rendering libraries.
"""

from __future__ import annotations

import abc
from typing import Iterator, List, Optional, Tuple

import PIL.Image


class PDFPageBackend(abc.ABC):
    """Abstract interface representing a single page within a PDF document."""

    @property
    @abc.abstractmethod
    def page_number(self) -> int:
        """Zero-indexed page number."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def rect(self) -> Tuple[float, float, float, float]:
        """Page bounding rectangle in points as (x0, y0, x1, y1)."""
        raise NotImplementedError

    @property
    def width(self) -> float:
        """Page width in points."""
        r = self.rect
        return r[2] - r[0]

    @property
    def height(self) -> float:
        """Page height in points."""
        r = self.rect
        return r[3] - r[1]

    @abc.abstractmethod
    def get_text(self) -> str:
        """Extract all plain vector text from the page."""
        raise NotImplementedError

    @abc.abstractmethod
    def search_for(self, needle: str) -> List[Tuple[float, float, float, float]]:
        """Search for exact text occurrences and return their bounding boxes (x0, y0, x1, y1)."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_words(self) -> List[Tuple[float, float, float, float, str, int, int, int]]:
        """
        Extract individual words and their bounding boxes.
        Each entry is (x0, y0, x1, y1, word_text, block_no, line_no, word_no).
        """
        raise NotImplementedError

    @abc.abstractmethod
    def render_to_image(self, dpi: int = 200) -> PIL.Image.Image:
        """Render the page to a PIL RGB image at the specified resolution (DPI)."""
        raise NotImplementedError


class PDFDocumentBackend(abc.ABC):
    """Abstract interface representing an open PDF document."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    @property
    @abc.abstractmethod
    def page_count(self) -> int:
        """Total number of pages in the document."""
        raise NotImplementedError

    def __len__(self) -> int:
        return self.page_count

    @abc.abstractmethod
    def get_page(self, index: int) -> PDFPageBackend:
        """Retrieve a specific page by zero-based index."""
        raise NotImplementedError

    def __getitem__(self, index: int) -> PDFPageBackend:
        if index < 0 or index >= self.page_count:
            raise IndexError(f"Page index {index} out of range (0..{self.page_count - 1})")
        return self.get_page(index)

    def __iter__(self) -> Iterator[PDFPageBackend]:
        for i in range(self.page_count):
            yield self.get_page(i)

    @abc.abstractmethod
    def close(self) -> None:
        """Release underlying document handles and native resources."""
        raise NotImplementedError

    def __enter__(self) -> PDFDocumentBackend:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
