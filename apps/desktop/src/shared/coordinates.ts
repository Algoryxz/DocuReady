/**
 * Coordinate transformations between Python extraction engine (PyMuPDF)
 * and PDF.js rendered viewports.
 *
 * Python PyMuPDF coordinate contract:
 * - Origin: Top-Left (0, 0) of the unrotated page
 * - Units: PDF points (1/72 inch)
 * - Format: [x0, y0, x1, y1] where:
 *     x0: distance from left page edge in points
 *     y0: distance from top page edge in points
 *     x1: distance from left page edge in points (x1 >= x0)
 *     y1: distance from top page edge in points (y1 >= y0)
 *
 * PDF.js viewport contract:
 * - Origin: Top-Left (0, 0) of the rendered viewport
 * - Units: CSS pixels (scale factor applied)
 * - Supports rotation: 0°, 90°, 180°, 270° clockwise
 */

export interface ViewportTransformOptions {
  pageWidth: number; // in PDF points (unrotated width)
  pageHeight: number; // in PDF points (unrotated height)
  scale: number; // zoom factor (e.g. 1.0 = 100%)
  rotation?: number; // 0, 90, 180, 270 degrees
  offsetX?: number; // viewBox / cropBox X offset if applicable
  offsetY?: number; // viewBox / cropBox Y offset if applicable
}

export interface ViewportRect {
  left: number; // CSS pixels from viewport left
  top: number; // CSS pixels from viewport top
  width: number; // CSS pixels width
  height: number; // CSS pixels height
}

/**
 * Validates whether a raw coordinate value is a valid bounding box.
 */
export function isValidBoundingBox(
  bbox: unknown
): bbox is [number, number, number, number] {
  if (!Array.isArray(bbox) || bbox.length !== 4) {
    return false;
  }
  for (const n of bbox) {
    if (typeof n !== "number" || Number.isNaN(n) || !Number.isFinite(n)) {
      return false;
    }
  }
  return true;
}

/**
 * Sanitizes and normalizes a bounding box, ensuring x0 <= x1 and y0 <= y1.
 */
export function normalizeBoundingBox(
  bbox: [number, number, number, number],
  pageWidth?: number,
  pageHeight?: number
): [number, number, number, number] {
  let [x0, y0, x1, y1] = bbox;

  // Swap if inverted
  if (x0 > x1) {
    [x0, x1] = [x1, x0];
  }
  if (y0 > y1) {
    [y0, y1] = [y1, y0];
  }

  // Clamp to page boundaries if page dimensions are provided
  if (pageWidth !== undefined && pageWidth > 0) {
    x0 = Math.max(0, Math.min(x0, pageWidth));
    x1 = Math.max(0, Math.min(x1, pageWidth));
  }
  if (pageHeight !== undefined && pageHeight > 0) {
    y0 = Math.max(0, Math.min(y0, pageHeight));
    y1 = Math.max(0, Math.min(y1, pageHeight));
  }

  return [x0, y0, x1, y1];
}

/**
 * Transforms Python PyMuPDF bounding box coordinates (in PDF points, top-left origin)
 * into PDF.js viewport coordinates (in CSS pixels, top-left origin) accounting for
 * page dimensions, scale, and rotation.
 */
export function transformBBoxToViewport(
  rawBBox: [number, number, number, number],
  options: ViewportTransformOptions
): ViewportRect | null {
  if (!isValidBoundingBox(rawBBox)) {
    return null;
  }

  const { pageWidth, pageHeight, scale, offsetX = 0, offsetY = 0 } = options;
  if (pageWidth <= 0 || pageHeight <= 0 || scale <= 0) {
    return null;
  }

  // Normalize bounding box
  const [x0, y0, x1, y1] = normalizeBoundingBox(rawBBox, pageWidth, pageHeight);

  // Apply crop/viewbox offset if applicable
  const adjX0 = x0 - offsetX;
  const adjY0 = y0 - offsetY;
  const adjX1 = x1 - offsetX;
  const adjY1 = y1 - offsetY;

  const rot = (((options.rotation || 0) % 360) + 360) % 360;

  let left: number;
  let top: number;
  let width: number;
  let height: number;

  switch (rot) {
    case 90:
      // 90° clockwise:
      // - Page top edge becomes viewport right edge
      // - Page left edge becomes viewport top edge
      left = (pageHeight - adjY1) * scale;
      top = adjX0 * scale;
      width = (adjY1 - adjY0) * scale;
      height = (adjX1 - adjX0) * scale;
      break;

    case 180:
      // 180° rotation: inverted
      left = (pageWidth - adjX1) * scale;
      top = (pageHeight - adjY1) * scale;
      width = (adjX1 - adjX0) * scale;
      height = (adjY1 - adjY0) * scale;
      break;

    case 270:
      // 270° clockwise (90° counter-clockwise):
      // - Page top edge becomes viewport left edge
      // - Page left edge becomes viewport bottom edge
      left = adjY0 * scale;
      top = (pageWidth - adjX1) * scale;
      width = (adjY1 - adjY0) * scale;
      height = (adjX1 - adjX0) * scale;
      break;

    case 0:
    default:
      // Standard upright page
      left = adjX0 * scale;
      top = adjY0 * scale;
      width = (adjX1 - adjX0) * scale;
      height = (adjY1 - adjY0) * scale;
      break;
  }

  // Guard against negative dimensions
  width = Math.max(0, width);
  height = Math.max(0, height);

  return {
    left: Math.round(left * 10) / 10,
    top: Math.round(top * 10) / 10,
    width: Math.round(width * 10) / 10,
    height: Math.round(height * 10) / 10
  };
}
