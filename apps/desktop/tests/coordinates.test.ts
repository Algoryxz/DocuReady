import assert from "node:assert";
import test from "node:test";
import {
  isValidBoundingBox,
  normalizeBoundingBox,
  transformBBoxToViewport
} from "../src/shared/coordinates.ts";

test("isValidBoundingBox identifies valid and invalid coordinates", () => {
  // Valid
  assert.strictEqual(isValidBoundingBox([0, 0, 100, 100]), true);
  assert.strictEqual(isValidBoundingBox([123.4, 56.7, 234.5, 345.6]), true);

  // Invalid length
  assert.strictEqual(isValidBoundingBox([0, 0, 100]), false);
  assert.strictEqual(isValidBoundingBox([0, 0, 100, 100, 200]), false);

  // Non-numbers, NaN, infinity
  assert.strictEqual(isValidBoundingBox(["0", 0, 100, 100] as any), false);
  assert.strictEqual(isValidBoundingBox([0, NaN, 100, 100]), false);
  assert.strictEqual(isValidBoundingBox([0, 0, Infinity, 100]), false);
  assert.strictEqual(isValidBoundingBox(null), false);
  assert.strictEqual(isValidBoundingBox(undefined), false);
  assert.strictEqual(isValidBoundingBox({}), false);
});

test("normalizeBoundingBox inverts backwards coords and clamps within bounds", () => {
  const pageWidth = 600;
  const pageHeight = 800;

  // Normal coordinates
  const norm1 = normalizeBoundingBox([50, 60, 150, 160], pageWidth, pageHeight);
  assert.deepStrictEqual(norm1, [50, 60, 150, 160]);

  // Inverted coordinates (x1 < x0, y1 < y0)
  const norm2 = normalizeBoundingBox([150, 160, 50, 60], pageWidth, pageHeight);
  assert.deepStrictEqual(norm2, [50, 60, 150, 160]);

  // Out of bounds coordinates (negative and exceeding max)
  const norm3 = normalizeBoundingBox([-20, -10, 700, 900], pageWidth, pageHeight);
  assert.deepStrictEqual(norm3, [0, 0, 600, 800]);
});

test("transformBBoxToViewport correctly transforms across 0, 90, 180, and 270 rotations", () => {
  // Page size: 600 x 800 pt
  const pageWidth = 600;
  const pageHeight = 800;
  const rawBBox: [number, number, number, number] = [100, 150, 300, 250];
  // Box has width 200 pt, height 100 pt

  // 1. Upright (0 degrees), scale = 1.0
  const box0 = transformBBoxToViewport(rawBBox, {
    pageWidth,
    pageHeight,
    scale: 1.0,
    rotation: 0
  });
  assert.ok(box0);
  assert.strictEqual(box0.left, 100);
  assert.strictEqual(box0.top, 150);
  assert.strictEqual(box0.width, 200);
  assert.strictEqual(box0.height, 100);

  // 2. Upright with 1.5x zoom
  const box0Scaled = transformBBoxToViewport(rawBBox, {
    pageWidth,
    pageHeight,
    scale: 1.5,
    rotation: 0
  });
  assert.ok(box0Scaled);
  assert.strictEqual(box0Scaled.left, 150);
  assert.strictEqual(box0Scaled.top, 225);
  assert.strictEqual(box0Scaled.width, 300);
  assert.strictEqual(box0Scaled.height, 150);

  // 3. 90 degrees clockwise rotation:
  // left = (pageHeight - y1) * scale = (800 - 250) * 1.0 = 550
  // top = x0 * scale = 100
  // width = (y1 - y0) * scale = 100
  // height = (x1 - x0) * scale = 200
  const box90 = transformBBoxToViewport(rawBBox, {
    pageWidth,
    pageHeight,
    scale: 1.0,
    rotation: 90
  });
  assert.ok(box90);
  assert.strictEqual(box90.left, 550);
  assert.strictEqual(box90.top, 100);
  assert.strictEqual(box90.width, 100);
  assert.strictEqual(box90.height, 200);

  // 4. 180 degrees rotation:
  // left = (pageWidth - x1) * scale = (600 - 300) * 1.0 = 300
  // top = (pageHeight - y1) * scale = (800 - 250) * 1.0 = 550
  // width = 200
  // height = 100
  const box180 = transformBBoxToViewport(rawBBox, {
    pageWidth,
    pageHeight,
    scale: 1.0,
    rotation: 180
  });
  assert.ok(box180);
  assert.strictEqual(box180.left, 300);
  assert.strictEqual(box180.top, 550);
  assert.strictEqual(box180.width, 200);
  assert.strictEqual(box180.height, 100);

  // 5. 270 degrees clockwise rotation:
  // left = y0 * scale = 150
  // top = (pageWidth - x1) * scale = (600 - 300) * 1.0 = 300
  // width = 100
  // height = 200
  const box270 = transformBBoxToViewport(rawBBox, {
    pageWidth,
    pageHeight,
    scale: 1.0,
    rotation: 270
  });
  assert.ok(box270);
  assert.strictEqual(box270.left, 150);
  assert.strictEqual(box270.top, 300);
  assert.strictEqual(box270.width, 100);
  assert.strictEqual(box270.height, 200);
});

test("transformBBoxToViewport rejects invalid dimensions and handles viewbox offsets", () => {
  // Invalid page dims
  assert.strictEqual(
    transformBBoxToViewport([0, 0, 10, 10], {
      pageWidth: 0,
      pageHeight: 500,
      scale: 1.0
    }),
    null
  );

  // Invalid scale
  assert.strictEqual(
    transformBBoxToViewport([0, 0, 10, 10], {
      pageWidth: 500,
      pageHeight: 500,
      scale: -1
    }),
    null
  );

  // Crop / Viewbox offset
  const boxWithOffset = transformBBoxToViewport([100, 150, 300, 250], {
    pageWidth: 600,
    pageHeight: 800,
    scale: 1.0,
    rotation: 0,
    offsetX: 50,
    offsetY: 50
  });
  assert.ok(boxWithOffset);
  assert.strictEqual(boxWithOffset.left, 50); // 100 - 50
  assert.strictEqual(boxWithOffset.top, 100); // 150 - 50
  assert.strictEqual(boxWithOffset.width, 200);
  assert.strictEqual(boxWithOffset.height, 100);
});
