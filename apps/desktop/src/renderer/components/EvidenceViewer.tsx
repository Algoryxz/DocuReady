import React, { useEffect, useRef, useState } from "react";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";
import pdfjsWorker from "pdfjs-dist/legacy/build/pdf.worker.mjs?url";
import {
  transformBBoxToViewport,
  type ViewportRect
} from "../../shared/coordinates.ts";
import type {
  DocumentDescriptor,
  NormalizedEvidenceItem
} from "../../shared/types.ts";

// Configure PDF.js worker
if (typeof window !== "undefined" && !pdfjsLib.GlobalWorkerOptions.workerSrc) {
  try {
    pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;
  } catch {
    // If worker URL setup fails, fallback to standard execution
  }
}

export interface EvidenceViewerProps {
  document: DocumentDescriptor | null;
  documentBytes: Uint8Array | null;
  evidenceItems: NormalizedEvidenceItem[];
  selectedEvidenceId: string | null;
  onSelectEvidence: (item: NormalizedEvidenceItem) => void;
  onSelectFinding: (ruleId: string) => void;
  targetPage?: number;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  document,
  documentBytes,
  evidenceItems,
  selectedEvidenceId,
  onSelectEvidence,
  onSelectFinding,
  targetPage
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const [numPages, setNumPages] = useState<number>(1);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);
  const [pageRotation, setPageRotation] = useState<number>(0);
  const [pageSize, setPageSize] = useState<{ width: number; height: number }>({
    width: 0,
    height: 0
  });
  const [viewportDims, setViewportDims] = useState<{ width: number; height: number }>({
    width: 0,
    height: 0
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  // Sync targetPage from external prop (e.g. user clicked finding evidence)
  useEffect(() => {
    if (targetPage && targetPage > 0 && targetPage <= numPages && targetPage !== currentPage) {
      setCurrentPage(targetPage);
    }
  }, [targetPage, numPages]);

  // Load document binary
  useEffect(() => {
    let cancelled = false;

    if (!document || !documentBytes) {
      setPdfDoc(null);
      setImageUrl(null);
      setNumPages(1);
      setCurrentPage(1);
      setLoadError(null);
      return;
    }

    if (document.fileType === "pdf") {
      setIsLoading(true);
      setLoadError(null);
      setImageUrl(null);

      // Pass typed byte copy
      const uint8Copy = new Uint8Array(documentBytes);

      const loadingTask = pdfjsLib.getDocument({
        data: uint8Copy,
        cMapUrl: undefined,
        cMapPacked: true
      });

      loadingTask.promise
        .then((doc) => {
          if (!cancelled) {
            setPdfDoc(doc);
            setNumPages(doc.numPages);
            setCurrentPage(targetPage && targetPage <= doc.numPages ? targetPage : 1);
            setIsLoading(false);
          }
        })
        .catch((err) => {
          if (!cancelled) {
            console.error("Failed to load PDF:", err);
            setLoadError(`Failed to load PDF: ${err.message || String(err)}`);
            setIsLoading(false);
          }
        });

      return () => {
        cancelled = true;
        try {
          loadingTask.destroy();
        } catch {
          // Ignore destruction error
        }
      };
    } else {
      // Image document
      setPdfDoc(null);
      setNumPages(1);
      setCurrentPage(1);
      setLoadError(null);

      const blob = new Blob([new Uint8Array(documentBytes) as unknown as BlobPart], {
        type: document.mimeType
      });
      const url = URL.createObjectURL(blob);
      setImageUrl(url);

      return () => {
        URL.revokeObjectURL(url);
      };
    }
  }, [document, documentBytes]);

  // Render PDF page to canvas
  useEffect(() => {
    let renderTask: any = null;
    let isCancelled = false;

    if (!pdfDoc || !canvasRef.current || document?.fileType !== "pdf") {
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    pdfDoc
      .getPage(currentPage)
      .then((page: any) => {
        if (isCancelled) return;

        const rotation = page.rotate || 0;
        setPageRotation(rotation);

        // Native unrotated page dimensions (in PDF points)
        const unrotated = page.getViewport({ scale: 1.0, rotation: 0 });
        setPageSize({ width: unrotated.width, height: unrotated.height });

        // Scaled viewport
        const viewport = page.getViewport({ scale, rotation });
        setViewportDims({ width: viewport.width, height: viewport.height });

        // Handle high DPI screens
        const outputScale = window.devicePixelRatio || 1;
        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);
        canvas.style.width = `${Math.floor(viewport.width)}px`;
        canvas.style.height = `${Math.floor(viewport.height)}px`;

        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.scale(outputScale, outputScale);

        const renderContext = {
          canvasContext: ctx,
          viewport
        };

        renderTask = page.render(renderContext);
        return renderTask.promise;
      })
      .catch((err: any) => {
        if (!isCancelled && err?.name !== "RenderingCancelledException") {
          console.error("Page render error:", err);
        }
      });

    return () => {
      isCancelled = true;
      if (renderTask) {
        try {
          renderTask.cancel();
        } catch {
          // Ignore render cancellation exception
        }
      }
    };
  }, [pdfDoc, currentPage, scale, document]);

  // Zoom helpers
  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.25, 3.0));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.25, 0.5));
  };

  const handleResetZoom = () => {
    setScale(1.0);
  };

  const handleFitToWidth = () => {
    if (!containerRef.current || viewportDims.width === 0) return;
    const containerWidth = containerRef.current.clientWidth - 48; // padding
    if (containerWidth > 0 && viewportDims.width > 0) {
      const currentNativeWidth = viewportDims.width / scale;
      const newScale = Math.max(0.5, Math.min(3.0, containerWidth / currentNativeWidth));
      setScale(parseFloat(newScale.toFixed(2)));
    }
  };

  // Filter evidence items for current document and page
  const pageEvidence = evidenceItems.filter((item) => {
    if (!document) return false;
    const matchesDoc =
      item.fileName === document.name ||
      item.documentType.toLowerCase() === document.name.toLowerCase();
    const matchesPage = item.pageNumber === currentPage;
    return matchesDoc && matchesPage && item.hasProvenance && item.boundingBox !== null;
  });

  return (
    <section className="evidence-viewer-panel" ref={containerRef}>
      {/* Viewer Toolbar */}
      <div className="viewer-toolbar">
        <div className="toolbar-group page-controls">
          <button
            type="button"
            className="toolbar-btn"
            onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
            disabled={currentPage <= 1 || isLoading}
            title="Previous Page"
          >
            ◀
          </button>
          <span className="page-indicator">
            Page <strong>{currentPage}</strong> of <strong>{numPages}</strong>
          </span>
          <button
            type="button"
            className="toolbar-btn"
            onClick={() => setCurrentPage((p) => Math.min(p + 1, numPages))}
            disabled={currentPage >= numPages || isLoading}
            title="Next Page"
          >
            ▶
          </button>
        </div>

        <div className="toolbar-group zoom-controls">
          <button
            type="button"
            className="toolbar-btn"
            onClick={handleZoomOut}
            disabled={scale <= 0.5 || isLoading}
            title="Zoom Out"
          >
            −
          </button>
          <button
            type="button"
            className="toolbar-btn zoom-level"
            onClick={handleResetZoom}
            title="Reset Zoom to 100%"
          >
            {Math.round(scale * 100)}%
          </button>
          <button
            type="button"
            className="toolbar-btn"
            onClick={handleZoomIn}
            disabled={scale >= 3.0 || isLoading}
            title="Zoom In"
          >
            +
          </button>
          <button
            type="button"
            className="toolbar-btn btn-secondary"
            onClick={handleFitToWidth}
            disabled={isLoading}
            title="Fit to Width"
          >
            Fit Width
          </button>
        </div>
      </div>

      {/* Main Canvas / Image Area */}
      <div className="viewer-stage">
        {!document ? (
          <div className="empty-stage-message">
            <p className="primary-text">Select a document from the left panel to inspect.</p>
            <p className="sub-text">
              Document text and exact evidence bounding boxes will render here.
            </p>
          </div>
        ) : isLoading ? (
          <div className="loading-stage">
            <div className="spinner"></div>
            <p>Rendering {document.name}...</p>
          </div>
        ) : loadError ? (
          <div className="error-stage">
            <p className="error-title">Unable to render document</p>
            <p className="error-desc">{loadError}</p>
          </div>
        ) : (
          <div
            className="page-viewport-container"
            style={{
              width: `${viewportDims.width}px`,
              height: `${viewportDims.height}px`
            }}
          >
            {document.fileType === "pdf" ? (
              <canvas ref={canvasRef} className="pdf-canvas" />
            ) : (
              imageUrl && (
                <img
                  src={imageUrl}
                  alt={document.name}
                  className="image-viewer-preview"
                  onLoad={(e) => {
                    const img = e.currentTarget;
                    setPageSize({ width: img.naturalWidth, height: img.naturalHeight });
                    setViewportDims({
                      width: img.naturalWidth * scale,
                      height: img.naturalHeight * scale
                    });
                  }}
                />
              )
            )}

            {/* Bounding-Box Overlay Layer */}
            <div className="evidence-overlay-layer">
              {pageEvidence.map((ev) => {
                if (!ev.boundingBox || pageSize.width === 0 || pageSize.height === 0) {
                  return null;
                }

                const box: ViewportRect | null = transformBBoxToViewport(
                  ev.boundingBox,
                  {
                    pageWidth: pageSize.width,
                    pageHeight: pageSize.height,
                    scale,
                    rotation: pageRotation
                  }
                );

                if (!box) return null;

                const isSelected = selectedEvidenceId === ev.id;
                const statusClass = ev.ruleStatus.toLowerCase();

                return (
                  <div
                    key={ev.id}
                    className={`evidence-bbox ${statusClass} ${isSelected ? "selected" : ""}`}
                    style={{
                      left: `${box.left}px`,
                      top: `${box.top}px`,
                      width: `${box.width}px`,
                      height: `${box.height}px`
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectEvidence(ev);
                      onSelectFinding(ev.ruleId);
                    }}
                    title={`${ev.field} (${ev.ruleId}): ${ev.ruleStatus} [${ev.extractionMethod}]`}
                  >
                    <div className="bbox-label">
                      <span className="bbox-field">{ev.field}</span>
                      {ev.matchGrade && (
                        <span className="bbox-grade">{ev.matchGrade}</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
