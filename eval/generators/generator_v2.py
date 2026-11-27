"""Synthetic Document Generator v2 (T4.3) for DocuReady Evaluation Harness v2.

Builds on `docuready.generator` infrastructure with:
- 5 distinct document layouts (>= 3 reserved exclusively for the `test` split)
- Bilingual / Indic-script evaluation material (Odia & Devanagari digits/labels)
- Varied typography (Helvetica, Times-Roman, Courier), alignments, and field boxes
- Controlled scan degradation (rotation, blur, JPEG quality, low DPI, low contrast,
  overlapping synthetic stamps)
- Negative controls (same_name_different_person, near_identical_numbers,
  common_name_collision, wrong_doc_in_slot)
- Deterministic seeded generation, ground-truth manifests, dataset SHA-256 hashes,
  and mandatory "SYNTHETIC DOCUMENT — NOT FOR OFFICIAL USE" watermarks.
"""

from __future__ import annotations

import hashlib
import io
import json
import random
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas as rl_canvas

from docuready.domain.enums import EvidenceState, ExtractionMethod, Readiness
from docuready.domain.models import DocumentType, EvidenceProvenance, ExtractedDocument, ExtractedField
from docuready.generator import generate_income_certificate


DEV_CALIB_LAYOUTS: Tuple[str, ...] = (
    "L1_STANDARD_PORTRAIT",
    "L2_COMPACT_GRID",
)

TEST_ONLY_LAYOUTS: Tuple[str, ...] = (
    "L3_BILINGUAL_HEADER",
    "L4_TWO_COLUMN_SEAL",
    "L5_BOXED_DECLARATION",
)

ALL_LAYOUTS: Tuple[str, ...] = DEV_CALIB_LAYOUTS + TEST_ONLY_LAYOUTS

PERTURBATIONS: Tuple[str, ...] = (
    "unperturbed",
    "rotation",
    "blur",
    "jpeg_low_quality",
    "low_dpi",
    "low_contrast",
    "overlapping_stamp",
    "bilingual_indic",
)

NEGATIVE_CONTROLS: Tuple[str, ...] = (
    "none",
    "same_name_different_person",
    "near_identical_numbers",
    "common_name_collision",
    "wrong_doc_in_slot",
)

SYNTHETIC_WATERMARK = "SYNTHETIC DOCUMENT — NOT FOR OFFICIAL USE"

_FIRST_NAMES = (
    "Pravasini", "Minati", "Sasmita", "Subhashree", "Laxmipriya",
    "Aarav", "Rohan", "Ananya", "Sita", "Bikash",
)
_LAST_NAMES = ("Sahoo", "Das", "Patra", "Behera", "Mohanty", "Nayak", "Panda", "Devi")


def _to_odia_digits(s: str) -> str:
    trans = str.maketrans("0123456789", "୦୧୨୩୪୫୬୭୮୯")
    return s.translate(trans)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


@dataclass
class GeneratedSampleRecord:
    """Ground-truth manifest record for one synthetic evaluation packet."""

    packet_id: str
    split: str
    layout_id: str
    perturbation: str
    negative_control: str
    seed: int
    is_defective: bool
    expected_readiness: str
    ground_truth_fields: Dict[str, str]
    document_paths: Dict[str, str]
    document_sha256s: Dict[str, str]
    synthetic_label: str = "synthetic"
    # Serialized field metadata for deterministic harness evaluation
    ocr_sim_params: Dict[str, Any] = field(default_factory=dict)


class SyntheticGeneratorV2:
    """Deterministic, seeded synthetic document & packet generator for T4.3."""

    def __init__(self, seed: int = 42):
        self.seed = int(seed)

    def render_pdf_with_layout(
        self,
        pdf_path: Path,
        *,
        layout_id: str,
        applicant_name: str,
        dob: str,
        annual_income: str,
        issue_date: str,
        certificate_no: str,
        perturbation: str = "unperturbed",
    ) -> str:
        """Render a synthetic PDF document with the specified layout and perturbation."""
        if layout_id not in ALL_LAYOUTS:
            raise ValueError(f"Unknown layout_id: {layout_id}")
        import reportlab.rl_config
        reportlab.rl_config.invariant = 1
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        # L1_STANDARD_PORTRAIT reuses existing docuready.generator base when unperturbed
        if layout_id == "L1_STANDARD_PORTRAIT" and perturbation == "unperturbed":
            generate_income_certificate(
                str(pdf_path),
                applicant_name=applicant_name,
                father_name="Ramesh " + applicant_name.split()[-1],
                annual_income=annual_income,
                issue_date=issue_date,
                certificate_no=certificate_no,
            )
            return _sha256_file(pdf_path)

        # Render layout-specific PDF via ReportLab
        font_map = {
            "L1_STANDARD_PORTRAIT": "Helvetica",
            "L2_COMPACT_GRID": "Courier",
            "L3_BILINGUAL_HEADER": "Times-Roman",
            "L4_TWO_COLUMN_SEAL": "Helvetica",
            "L5_BOXED_DECLARATION": "Times-Roman",
        }
        font_name = font_map[layout_id]

        styles = getSampleStyleSheet()
        body_style = ParagraphStyle(
            f"Body_{layout_id}",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=10 if layout_id != "L2_COMPACT_GRID" else 9,
        )
        header_style = ParagraphStyle(
            f"Header_{layout_id}",
            parent=styles["Heading2"],
            fontName=font_name,
            fontSize=13,
            alignment=1 if layout_id != "L3_BILINGUAL_HEADER" else 2,
            textColor=colors.HexColor("#1A365D"),
        )

        story: List[Any] = []
        story.append(
            Paragraph(
                f"<font size=8 color='#B91C1C'><b>{SYNTHETIC_WATERMARK}</b></font>",
                body_style,
            )
        )
        story.append(Spacer(1, 6))

        if layout_id == "L3_BILINGUAL_HEADER" or perturbation == "bilingual_indic":
            story.append(Paragraph("ODISHA / ଓଡିଶା — SYNTHETIC CERTIFICATE", header_style))
            disp_income = _to_odia_digits(annual_income) if perturbation == "bilingual_indic" else annual_income
            disp_dob = _to_odia_digits(dob) if perturbation == "bilingual_indic" else dob
        else:
            story.append(Paragraph(f"SYNTHETIC RECORD ({layout_id})", header_style))
            disp_income = annual_income
            disp_dob = dob

        story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor("#4A5568")))
        story.append(Spacer(1, 8))

        if layout_id in ("L2_COMPACT_GRID", "L4_TWO_COLUMN_SEAL", "L5_BOXED_DECLARATION"):
            rows = [
                [Paragraph("<b>Applicant Name</b>", body_style), Paragraph(applicant_name, body_style)],
                [Paragraph("<b>Date of Birth</b>", body_style), Paragraph(disp_dob, body_style)],
                [Paragraph("<b>Certificate No</b>", body_style), Paragraph(certificate_no, body_style)],
                [Paragraph("<b>Issue Date</b>", body_style), Paragraph(issue_date, body_style)],
                [Paragraph("<b>Annual Income</b>", body_style), Paragraph(disp_income, body_style)],
            ]
            tbl = Table(rows, colWidths=[180, 320])
            tbl.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#718096")),
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EDF2F7")),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(tbl)
        else:
            story.append(Paragraph(f"Applicant Name: <b>{applicant_name}</b>", body_style))
            story.append(Paragraph(f"Date of Birth: {disp_dob}", body_style))
            story.append(Paragraph(f"Certificate No: {certificate_no}", body_style))
            story.append(Paragraph(f"Issue Date: {issue_date}", body_style))
            story.append(Paragraph(f"Annual Income: {disp_income}", body_style))

        if layout_id == "L4_TWO_COLUMN_SEAL" or perturbation == "overlapping_stamp":
            story.append(Spacer(1, 10))
            story.append(
                Paragraph(
                    "<font color='#9B2C2C'><b>[SYNTHETIC SEAL: VERIFIED SPECIMEN]</b></font>",
                    body_style,
                )
            )

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
            invariant=1,
        )
        doc.build(story)

        # Apply controlled image-level scan degradation to the actual rendered layout PDF
        if perturbation in ("rotation", "blur", "jpeg_low_quality", "low_dpi", "low_contrast"):
            self._apply_scan_degradation(pdf_path, perturbation=perturbation)

        return _sha256_file(pdf_path)

    def _apply_scan_degradation(
        self,
        pdf_path: Path,
        *,
        perturbation: str,
    ) -> None:
        """Rasterize the actual layout PDF via PyMuPDF and apply controlled scan degradation."""
        import pymupdf

        with pymupdf.open(str(pdf_path)) as doc_pdf:
            pix = doc_pdf[0].get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        if perturbation == "rotation":
            img = img.rotate(7.5, expand=False, fillcolor=(248, 248, 245))
        elif perturbation == "blur":
            img = img.filter(ImageFilter.GaussianBlur(radius=2.2))
        elif perturbation == "low_contrast":
            img = ImageEnhance.Contrast(img).enhance(0.45)
        elif perturbation == "low_dpi":
            w, h = img.size
            img = img.resize((max(1, w // 2), max(1, h // 2))).resize((w, h))
        elif perturbation == "jpeg_low_quality":
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=20)
            buf.seek(0)
            img = Image.open(buf).convert("RGB")

        # Wrap degraded raster image back into PDF bytes deterministically via ReportLab (invariant=1)
        from reportlab.lib.utils import ImageReader
        png_buf = io.BytesIO()
        img.save(png_buf, format="PNG")
        png_buf.seek(0)

        out_buf = io.BytesIO()
        c = rl_canvas.Canvas(out_buf, pagesize=A4, invariant=1)
        c.drawImage(ImageReader(png_buf), 0, 0, width=A4[0], height=A4[1])
        c.showPage()
        c.save()
        pdf_path.write_bytes(out_buf.getvalue())

    def build_extracted_packet(self, record: GeneratedSampleRecord) -> Dict[DocumentType, ExtractedDocument]:
        """Construct deterministic ExtractedDocument packet matching the sample's ground truth & perturbation."""
        rng = random.Random(record.seed)
        gt = record.ground_truth_fields
        pert = record.perturbation
        neg = record.negative_control

        # Simulate realistic OCR feature degradation under perturbations
        token_conf = 0.94
        label_dist = 12.0
        label_match_conf = 0.96
        layout_cons = 0.94
        rot_deg = 0.0
        is_uncertain = False
        method = ExtractionMethod.NATIVE_VECTOR if pert == "unperturbed" else ExtractionMethod.LOCAL_OCR

        if pert == "rotation":
            token_conf = 0.78
            rot_deg = 8.5
            layout_cons = 0.72
        elif pert == "blur":
            token_conf = 0.42
            layout_cons = 0.65
            is_uncertain = True
        elif pert == "jpeg_low_quality":
            token_conf = 0.54
            layout_cons = 0.70
            is_uncertain = True
        elif pert == "low_dpi":
            token_conf = 0.50
            layout_cons = 0.68
            is_uncertain = True
        elif pert == "low_contrast":
            token_conf = 0.48
            is_uncertain = True
        elif pert == "overlapping_stamp":
            token_conf = 0.66
            label_match_conf = 0.70
            layout_cons = 0.74
        elif pert == "bilingual_indic":
            token_conf = 0.85
            label_match_conf = 0.88
            layout_cons = 0.86

        aadhaar_name = gt["applicant_name"]
        passbook_name = gt["passbook_name"]
        dob_val = gt["dob"]

        # Negative controls
        if neg == "same_name_different_person":
            # Same name, but DOB indicates underage/different person
            dob_val = "10/10/2010"
        elif neg == "near_identical_numbers":
            # Off-by-one digit in DOB year (underage 2004 vs 2003)
            dob_val = "01/07/2004"
        elif neg == "common_name_collision":
            aadhaar_name = "Sita Devi"
            passbook_name = "Sita Devi"
            dob_val = "01/07/1960"  # Age >= 60 defect

        def _make_field(doc_lbl: str, fname: str, raw: str, norm: Any, f_unc: bool = False) -> ExtractedField:
            return ExtractedField(
                field_name=fname,
                raw_value=raw,
                normalized_value=norm,
                confidence=token_conf,
                extraction_method=method.value,
                evidence_state=EvidenceState.UNCERTAIN if (is_uncertain or f_unc) else (
                    EvidenceState.VERIFIED if method == ExtractionMethod.NATIVE_VECTOR else EvidenceState.PROVISIONAL
                ),
                calibrated_confidence=round(token_conf - 0.05 * rng.random(), 3),
                raw_ocr_token_confidence=token_conf if method == ExtractionMethod.LOCAL_OCR else None,
                supporting_tokens_count=len(str(raw).split()),
                label_detected=True,
                label_distance_pt=label_dist,
                format_valid=True,
                is_uncertain=is_uncertain or f_unc,
                provenance=EvidenceProvenance(
                    document_type=doc_lbl,
                    file_name=Path(record.document_paths["aadhaar_card"]).name,
                    page_number=1,
                    bounding_box=[40.0, 100.0, 280.0, 118.0],
                    raw_snippet=f"{fname}: {raw}",
                    extracted_field=fname,
                    extraction_method=method.value,
                    ocr_confidence=token_conf if method == ExtractionMethod.LOCAL_OCR else None,
                ),
            )

        aadhaar_doc = ExtractedDocument(
            doc_type=DocumentType.AADHAAR,
            file_path=record.document_paths["aadhaar_card"],
            status="UNREADABLE" if pert in ("blur", "low_contrast") and record.is_defective else "VALID",
            page_count=1,
            mean_ocr_confidence=token_conf,
            fields={
                "applicant_name": _make_field("AADHAAR", "applicant_name", aadhaar_name, aadhaar_name),
                "dob": _make_field("AADHAAR", "dob", dob_val, dob_val),
            },
        )
        passbook_doc = ExtractedDocument(
            doc_type=DocumentType.BANK_PASSBOOK,
            file_path=record.document_paths["bank_passbook"],
            status="VALID",
            page_count=1,
            mean_ocr_confidence=token_conf,
            fields={
                "applicant_name": _make_field("BANK_PASSBOOK", "applicant_name", passbook_name, passbook_name),
            },
        )

        # Wrong document in slot negative control
        if neg == "wrong_doc_in_slot":
            aadhaar_doc.status = "UNREADABLE"

        record.ocr_sim_params = {
            "token_confidence": token_conf,
            "label_distance_pt": label_dist,
            "label_match_confidence": label_match_conf,
            "layout_consistency": layout_cons,
            "rotation_deg": rot_deg,
            "extraction_method": method.value,
        }
        return {
            DocumentType.AADHAAR: aadhaar_doc,
            DocumentType.BANK_PASSBOOK: passbook_doc,
        }


def generate_split_dataset(
    output_dir: Path,
    *,
    split: str,
    seed: int,
    n_samples: int = 24,
    render_pdfs: bool = True,
) -> Dict[str, Any]:
    """Generate a deterministic, seeded evaluation split (`dev`, `calib`, or `test`).

    Enforces layout separation:
    - `dev` and `calib` use ONLY `DEV_CALIB_LAYOUTS` (2 layouts).
    - `test` uses ONLY `TEST_ONLY_LAYOUTS` (3 unseen layouts).
    """
    if split not in ("dev", "calib", "test"):
        raise ValueError(f"Unsupported split: {split}")

    allowed_layouts = TEST_ONLY_LAYOUTS if split == "test" else DEV_CALIB_LAYOUTS
    gen = SyntheticGeneratorV2(seed=seed)
    rng = random.Random(seed)
    split_dir = output_dir / split
    split_dir.mkdir(parents=True, exist_ok=True)

    records: List[GeneratedSampleRecord] = []
    for idx in range(n_samples):
        layout_id = allowed_layouts[idx % len(allowed_layouts)]
        perturbation = PERTURBATIONS[idx % len(PERTURBATIONS)]
        neg_ctrl = "none"
        if idx % 6 == 5:
            neg_ctrl = NEGATIVE_CONTROLS[1 + ((idx // 6) % (len(NEGATIVE_CONTROLS) - 1))]

        first = _FIRST_NAMES[(idx + rng.randint(0, 9)) % len(_FIRST_NAMES)]
        last = _LAST_NAMES[(idx + rng.randint(0, 7)) % len(_LAST_NAMES)]
        full_name = f"{first} {last}"

        # Half clean-age (born 1990), half defective-age (born 2006 -> underage < 21 on 2024-07-01)
        is_defective = (idx % 3 == 1) or (neg_ctrl != "none")
        dob = "10/08/2006" if (idx % 3 == 1) else "15/05/1990"
        expected_readiness = Readiness.NOT_READY.value if is_defective else Readiness.NO_ISSUES_FOUND.value
        if perturbation in ("blur", "jpeg_low_quality", "low_dpi", "low_contrast") and not is_defective:
            expected_readiness = Readiness.NEEDS_CHECKS.value

        pkt_id = f"SYN_{split.upper()}_{idx:03d}"
        aadhaar_pdf = split_dir / f"{pkt_id}_aadhaar.pdf"
        passbook_pdf = split_dir / f"{pkt_id}_passbook.pdf"

        if render_pdfs:
            sha_a = gen.render_pdf_with_layout(
                aadhaar_pdf,
                layout_id=layout_id,
                applicant_name=full_name,
                dob=dob,
                annual_income="180000",
                issue_date="01/01/2024",
                certificate_no=f"SYN/{split.upper()}/{idx:04d}",
                perturbation=perturbation,
            )
            sha_b = gen.render_pdf_with_layout(
                passbook_pdf,
                layout_id=layout_id,
                applicant_name=full_name,
                dob=dob,
                annual_income="180000",
                issue_date="01/01/2024",
                certificate_no=f"BNK/{split.upper()}/{idx:04d}",
                perturbation="unperturbed",
            )
        else:
            sha_a = _sha256_bytes(f"{pkt_id}_a_{seed}".encode("utf-8"))
            sha_b = _sha256_bytes(f"{pkt_id}_b_{seed}".encode("utf-8"))

        rec = GeneratedSampleRecord(
            packet_id=pkt_id,
            split=split,
            layout_id=layout_id,
            perturbation=perturbation,
            negative_control=neg_ctrl,
            seed=seed + idx,
            is_defective=is_defective,
            expected_readiness=expected_readiness,
            ground_truth_fields={
                "applicant_name": full_name,
                "passbook_name": full_name,
                "dob": dob,
            },
            document_paths={
                "aadhaar_card": str(aadhaar_pdf),
                "bank_passbook": str(passbook_pdf),
            },
            document_sha256s={
                "aadhaar_card": sha_a,
                "bank_passbook": sha_b,
            },
        )
        gen.build_extracted_packet(rec)
        records.append(rec)

    manifest_payload = {
        "split": split,
        "seed": seed,
        "synthetic_label": "synthetic",
        "watermark": SYNTHETIC_WATERMARK,
        "layouts_used": sorted({r.layout_id for r in records}),
        "n_samples": len(records),
        "samples": [asdict(r) for r in records],
    }
    manifest_bytes = json.dumps(manifest_payload, indent=2, sort_keys=True).encode("utf-8")
    manifest_payload["dataset_sha256"] = _sha256_bytes(manifest_bytes)

    manifest_path = split_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_payload
