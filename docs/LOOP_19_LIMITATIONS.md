# LOOP 19: Operational Boundaries & Technical Limitations

## 1. Executive Summary

In adherence to the Loop 19 directive for honest, unvarnished reporting, this document specifies the technical boundaries and unsupported layout configurations of the table association subsystem.

---

## 2. Documented Technical Limitations

### 1. Compressed Tab Stops Without Visible Borders (`TAB_09`)
- **Limitation**: When adjacent columns in borderless tables have horizontal separation gaps under 20 pixels (e.g. tightly packed monospaced print), 1D projection profiling may group adjacent tokens into a single column.
- **Operational Boundary**: Reliable column separation requires a minimum horizontal gutter of $\ge 25$ pixels at 200 DPI.

### 2. Multi-Tier Nested Merged Headers (`TAB_07`)
- **Limitation**: `TableGrid` currently flattens multi-tier headers into leaf column representations. While leaf headers (`Property Cess`, `Water Cess`) are identified accurately, the overarching parent category (`ASSESSED TAX`) is not tracked as a formal tree node.
- **Operational Boundary**: Flat 1-tier and 2-tier simple headers are fully supported; 3+ tier complex nested headers are out of scope.

### 3. Rotational Skew Beyond 3.0 Degrees (`TAB_10`)
- **Limitation**: The 1D horizontal and vertical projection profiles rely on rectilinear alignment. When scan tilt exceeds 3.0°, horizontal valleys blur, reducing row clustering accuracy.
- **Operational Boundary**: Requires pre-OCR deskew normalization for scans with severe rotational tilt.

### 4. Freeform Handwritten or Unstructured Receipts
- **Limitation**: The geometric projection engine is optimized for printed administrative documents, forms, ledgers, and official schedules. Handwritten, non-aligned ledgers are unsupported.
