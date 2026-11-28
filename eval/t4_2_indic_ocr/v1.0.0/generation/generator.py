"""Deterministic Generator & Validator for DocuReady T4.2 Indic OCR Evaluation Corpus (v1.0.0).

Generates 24 held-out rasterized PNG documents (12 Odia, 12 Hindi/Devanagari) with:
- HarfBuzz-shaped Unicode text via PyMuPDF HTML/CSS rendering -> 200 DPI PNG rasterization
- Zero native vector text layer (pure raster PNGs exercising LOCAL_OCR)
- Separate raw Unicode and canonical normalized ground-truth files
- Complete manifest, SHA-256 inventory, font provenance, and validation reports

All personal/document data is 100% synthetic.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import PIL
import pymupdf
from PIL import Image, ImageEnhance, ImageFilter

# Ensure repo root is importable when executed as a standalone script
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from docuready.normalize.normalizer import (  # noqa: E402
    normalize_cert_number,
    normalize_income,
    normalize_indic_digits,
    parse_and_normalize_date,
)

CORPUS_NAME = "docuready-t4-2-indic-ocr"
CORPUS_VERSION = "1.0.0"
GENERATOR_VERSION = "1.0.0"
GENERATOR_SEED = 20261128
CREATED_DATE = "2026-11-28"
DPI = 200
PAGE_WIDTH_PT = 595
PAGE_HEIGHT_PT = 842
SYNTHETIC_WATERMARK = "SYNTHETIC DOCUMENT — NOT FOR OFFICIAL USE"

_FONT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "NirmalaUI": {
        "family": "Nirmala UI",
        "filename": "Nirmala.ttc",
        "path": Path(r"C:\Windows\Fonts\Nirmala.ttc"),
        "source": "Microsoft Windows System Font (C:\\Windows\\Fonts\\Nirmala.ttc)",
        "license_note": "Microsoft Windows proprietary system font; not redistributed in repository.",
        "scripts_supported": ["ODIA", "DEVANAGARI", "LATIN"],
    },
    "Kalinga": {
        "family": "Kalinga",
        "filename": "kalinga.ttf",
        "path": Path(r"C:\Windows\Fonts\kalinga.ttf"),
        "source": "Microsoft Windows System Font (C:\\Windows\\Fonts\\kalinga.ttf)",
        "license_note": "Microsoft Windows proprietary system font; not redistributed in repository.",
        "scripts_supported": ["ODIA", "LATIN"],
    },
    "Mangal": {
        "family": "Mangal",
        "filename": "mangal.ttf",
        "path": Path(r"C:\Windows\Fonts\mangal.ttf"),
        "source": "Microsoft Windows System Font (C:\\Windows\\Fonts\\mangal.ttf)",
        "license_note": "Microsoft Windows proprietary system font; not redistributed in repository.",
        "scripts_supported": ["DEVANAGARI", "LATIN"],
    },
}

_ODIA_TRANS = str.maketrans("0123456789", "୦୧୨୩୪୫୬୭୮୯")
_DEVA_TRANS = str.maketrans("0123456789", "०१२३४५६७८९")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _to_odia_digits(text: str) -> str:
    return text.translate(_ODIA_TRANS)


def _to_deva_digits(text: str) -> str:
    return text.translate(_DEVA_TRANS)


def _canonicalize_field(field_name: str, raw_value: str) -> Tuple[Any, str]:
    """Compute canonical normalized value using DocuReady's production normalizer."""
    if field_name in ("dob", "issue_date"):
        parsed, status, is_ambiguous = parse_and_normalize_date(raw_value)
        if status != "VALID" or parsed is None:
            raise ValueError(f"Date normalization failed for {field_name}={raw_value!r}: {status}")
        return {
            "iso_date": parsed.isoformat(),
            "parse_status": status,
            "is_ambiguous": is_ambiguous,
            "ascii_digits": normalize_indic_digits(raw_value),
        }, "normalize_indic_digits + parse_and_normalize_date"
    if field_name == "annual_income":
        amount = normalize_income(raw_value)
        if amount is None:
            raise ValueError(f"Income normalization failed for {raw_value!r}")
        return {
            "amount_inr": amount,
            "ascii_digits": normalize_indic_digits(raw_value),
        }, "normalize_indic_digits + normalize_income"
    if field_name == "certificate_number":
        cert = normalize_cert_number(raw_value)
        if not cert:
            raise ValueError(f"Certificate normalization failed for {raw_value!r}")
        return {
            "canonical_cert": cert,
            "ascii_digits": normalize_indic_digits(raw_value),
        }, "normalize_indic_digits + normalize_cert_number"
    raise ValueError(f"Unknown field_name: {field_name}")


def _build_corpus_specs() -> List[Dict[str, Any]]:
    """Deterministic 24-document specification (12 Odia, 12 Hindi/Devanagari)."""
    specs: List[Dict[str, Any]] = []

    odia_cases = [
        ("T42_ORI_001", "INCOME_CERTIFICATE_PORTRAIT", "Kalinga", "ଅନନ୍ୟା ସାହୁ", "15/08/1995", "14/11/2026", "₹ 85,000/-", "OD/INC/2026/104928", "all_odia_digits", False),
        ("T42_ORI_002", "BILINGUAL_TWO_COLUMN_TABLE", "NirmalaUI", "ପ୍ରଭାସିନୀ ଦାସ", "22-03-1991", "10-10-2026", "₹ 1,20,000/-", "OD/INC/2026/208741", "all_odia_digits", False),
        ("T42_ORI_003", "COMPACT_BOXED_REGISTER", "Kalinga", "ମିନତୀ ପାତ୍ର", "09.12.1988", "05.09.2026", "Rs. 95,500/-", "OD-INC-2026-319042", "mixed_digits", False),
        ("T42_ORI_004", "SUBHADRA_STYLE_WELFARE_SLIP", "NirmalaUI", "ସସ୍ମିତା ବେହେରା", "18/07/1998", "19/11/2026", "₹ 1,45,000/-", "OD/SUB/2026/410256", "all_odia_digits", True),
        ("T42_ORI_005", "INCOME_CERTIFICATE_PORTRAIT", "NirmalaUI", "ଲକ୍ଷ୍ମୀପ୍ରିୟା ମହାନ୍ତି", "27/01/1993", "02/11/2026", "1.8 LPA", "OD/INC/2026/512839", "mixed_digits", False),
        ("T42_ORI_006", "BILINGUAL_TWO_COLUMN_TABLE", "Kalinga", "ଶୁଭଶ୍ରୀ ନାୟକ", "14-05-1996", "21-10-2026", "₹ 72,000/-", "OD/INC/2026/623914", "all_odia_digits", False),
        ("T42_ORI_007", "COMPACT_BOXED_REGISTER", "NirmalaUI", "ମଧୁସ୍ମିତା ପଣ୍ଡା", "03/11/1989", "12/08/2026", "Rs. 2,10,000/-", "OD-RES-2026-734125", "ascii_digits_with_odia_labels", False),
        ("T42_ORI_008", "SUBHADRA_STYLE_WELFARE_SLIP", "Kalinga", "ସ୍ନିଗ୍ଧା ଜେନା", "29-06-1994", "17/11/2026", "₹ 64,000/-", "OD/SUB/2026/845236", "all_odia_digits", True),
        ("T42_ORI_009", "INCOME_CERTIFICATE_PORTRAIT", "Kalinga", "ପ୍ରିୟଙ୍କା ସ୍ୱାଇଁ", "11.04.1997", "25.10.2026", "2.4 Lakh", "OD/INC/2026/956347", "mixed_digits", False),
        ("T42_ORI_010", "BILINGUAL_TWO_COLUMN_TABLE", "NirmalaUI", "ରଶ୍ମିତା ରାଉତ", "08/09/1990", "01/11/2026", "₹ 1,65,000/-", "OD/INC/2026/167458", "all_odia_digits", False),
        ("T42_ORI_011", "COMPACT_BOXED_REGISTER", "Kalinga", "ସୁନୀତା ବାରିକ", "20-12-1986", "15-09-2026", "₹ 1,10,000/-", "OD-INC-2026-278569", "all_odia_digits", False),
        ("T42_ORI_012", "SUBHADRA_STYLE_WELFARE_SLIP", "NirmalaUI", "ଅର୍ଚ୍ଚନା ମିଶ୍ର", "05/02/1999", "23/11/2026", "Rs. 90,000/-", "OD/SUB/2026/389670", "mixed_digits", True),
    ]

    for doc_id, layout, font_key, name, dob, issue, income, cert, digit_mode, mild_degrad in odia_cases:
        if digit_mode == "all_odia_digits":
            r_dob, r_issue, r_inc, r_cert = _to_odia_digits(dob), _to_odia_digits(issue), _to_odia_digits(income), _to_odia_digits(cert)
        elif digit_mode == "mixed_digits":
            r_dob, r_issue, r_inc, r_cert = _to_odia_digits(dob), issue, _to_odia_digits(income), cert[:8] + _to_odia_digits(cert[8:])
        else:
            r_dob, r_issue, r_inc, r_cert = dob, issue, income, cert

        specs.append({
            "document_id": doc_id,
            "language": "ori",
            "script": "ODIA",
            "rel_path": f"documents/odia/{doc_id}.png",
            "layout": layout,
            "font_key": font_key,
            "digit_mode": digit_mode,
            "mild_degradation": mild_degrad,
            "applicant_name": name,
            "labels": {
                "header": "ଓଡ଼ିଶା ସରକାର — ଆୟ ଓ ଯୋଗ୍ୟତା ପ୍ରମାଣପତ୍ର",
                "subheader": "Government of Odisha (Synthetic Evaluation Specimen)",
                "applicant": "ଆବେଦନକାରୀଙ୍କ ନାମ / Applicant",
                "dob": "ଜନ୍ମ ତାରିଖ / Date of Birth",
                "issue_date": "ଜାରି ତାରିଖ / Issue Date",
                "annual_income": "ବାର୍ଷିକ ଆୟ / Annual Income",
                "certificate_number": "ପ୍ରମାଣପତ୍ର ନଂ / Certificate No.",
            },
            "fields": {
                "dob": r_dob,
                "issue_date": r_issue,
                "annual_income": r_inc,
                "certificate_number": r_cert,
            },
        })

    hindi_cases = [
        ("T42_HIN_001", "INCOME_CERTIFICATE_PORTRAIT", "Mangal", "अनीता शर्मा", "15/08/1995", "14/11/2026", "₹ 85,000/-", "MH/INC/2026/104928", "all_deva_digits", False),
        ("T42_HIN_002", "BILINGUAL_TWO_COLUMN_TABLE", "NirmalaUI", "सुनीता वर्मा", "22-03-1991", "10-10-2026", "₹ 1,20,000/-", "UP/INC/2026/208741", "all_deva_digits", False),
        ("T42_HIN_003", "COMPACT_BOXED_REGISTER", "Mangal", "कविता गुप्ता", "09.12.1988", "05.09.2026", "Rs. 95,500/-", "RJ-INC-2026-319042", "mixed_digits", False),
        ("T42_HIN_004", "SUBHADRA_STYLE_WELFARE_SLIP", "NirmalaUI", "मीना कुमारी", "18/07/1998", "19/11/2026", "₹ 1,45,000/-", "MP/WEL/2026/410256", "all_deva_digits", True),
        ("T42_HIN_005", "INCOME_CERTIFICATE_PORTRAIT", "NirmalaUI", "रेखा देवी", "27/01/1993", "02/11/2026", "1.8 LPA", "BR/INC/2026/512839", "mixed_digits", False),
        ("T42_HIN_006", "BILINGUAL_TWO_COLUMN_TABLE", "Mangal", "पूजा तिवारी", "14-05-1996", "21-10-2026", "₹ 72,000/-", "CG/INC/2026/623914", "all_deva_digits", False),
        ("T42_HIN_007", "COMPACT_BOXED_REGISTER", "NirmalaUI", "सपना यादव", "03/11/1989", "12/08/2026", "Rs. 2,10,000/-", "JH-RES-2026-734125", "ascii_digits_with_deva_labels", False),
        ("T42_HIN_008", "SUBHADRA_STYLE_WELFARE_SLIP", "Mangal", "अंजलि मिश्रा", "29-06-1994", "17/11/2026", "₹ 64,000/-", "UP/WEL/2026/845236", "all_deva_digits", True),
        ("T42_HIN_009", "INCOME_CERTIFICATE_PORTRAIT", "Mangal", "निशा चौहान", "11.04.1997", "25.10.2026", "2.4 Lakh", "HR/INC/2026/956347", "mixed_digits", False),
        ("T42_HIN_010", "BILINGUAL_TWO_COLUMN_TABLE", "NirmalaUI", "ममता जोशी", "08/09/1990", "01/11/2026", "₹ 1,65,000/-", "UK/INC/2026/167458", "all_deva_digits", False),
        ("T42_HIN_011", "COMPACT_BOXED_REGISTER", "Mangal", "प्रियंका सिंह", "20-12-1986", "15-09-2026", "₹ 1,10,000/-", "DL-INC-2026-278569", "all_deva_digits", False),
        ("T42_HIN_012", "SUBHADRA_STYLE_WELFARE_SLIP", "NirmalaUI", "आरती पटेल", "05/02/1999", "23/11/2026", "Rs. 90,000/-", "MP/WEL/2026/389670", "mixed_digits", True),
    ]

    for doc_id, layout, font_key, name, dob, issue, income, cert, digit_mode, mild_degrad in hindi_cases:
        if digit_mode == "all_deva_digits":
            r_dob, r_issue, r_inc, r_cert = _to_deva_digits(dob), _to_deva_digits(issue), _to_deva_digits(income), _to_deva_digits(cert)
        elif digit_mode == "mixed_digits":
            r_dob, r_issue, r_inc, r_cert = _to_deva_digits(dob), issue, _to_deva_digits(income), cert[:8] + _to_deva_digits(cert[8:])
        else:
            r_dob, r_issue, r_inc, r_cert = dob, issue, income, cert

        specs.append({
            "document_id": doc_id,
            "language": "hin",
            "script": "DEVANAGARI",
            "rel_path": f"documents/hindi/{doc_id}.png",
            "layout": layout,
            "font_key": font_key,
            "digit_mode": digit_mode,
            "mild_degradation": mild_degrad,
            "applicant_name": name,
            "labels": {
                "header": "भारत सरकार — आय एवं पात्रता प्रमाणपत्र",
                "subheader": "Government of India (Synthetic Evaluation Specimen)",
                "applicant": "आवेदक का नाम / Applicant",
                "dob": "जन्म तिथि / Date of Birth",
                "issue_date": "जारी करने की तिथि / Issue Date",
                "annual_income": "वार्षिक आय / Annual Income",
                "certificate_number": "प्रमाणपत्र संख्या / Certificate No.",
            },
            "fields": {
                "dob": r_dob,
                "issue_date": r_issue,
                "annual_income": r_inc,
                "certificate_number": r_cert,
            },
        })

    return specs


def _render_html_for_spec(spec: Dict[str, Any]) -> Tuple[str, str]:
    font_info = _FONT_REGISTRY[spec["font_key"]]
    font_filename = font_info["filename"]
    font_name = spec["font_key"]
    lbl = spec["labels"]
    fld = spec["fields"]
    e = html.escape

    css = f"""
    @font-face {{
        font-family: '{font_name}';
        src: url('{font_filename}');
    }}
    body {{
        font-family: '{font_name}', sans-serif;
        color: #111111;
        margin: 0;
        padding: 0;
        line-height: 1.5;
    }}
    .wm {{
        text-align: center;
        font-size: 9pt;
        color: #777777;
        border-bottom: 1px solid #cccccc;
        padding-bottom: 4px;
        margin-bottom: 12px;
    }}
    .hdr {{
        text-align: center;
        margin-bottom: 16px;
    }}
    .hdr h2 {{
        font-size: 16pt;
        margin: 0 0 4px 0;
    }}
    .hdr p {{
        font-size: 10pt;
        color: #444444;
        margin: 0;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 12px;
    }}
    td, th {{
        border: 1px solid #444444;
        padding: 8px 10px;
        font-size: 12pt;
        vertical-align: top;
    }}
    th {{
        background-color: #f2f2f2;
        text-align: left;
        width: 44%;
    }}
    .box {{
        border: 2px solid #222222;
        padding: 14px;
        margin-top: 10px;
    }}
    .row {{
        margin: 8px 0;
        font-size: 12.5pt;
    }}
    .lbl {{
        font-weight: bold;
        color: #222222;
    }}
    .footer {{
        margin-top: 24px;
        font-size: 9pt;
        color: #666666;
        border-top: 1px dashed #aaaaaa;
        padding-top: 6px;
    }}
    """

    layout = spec["layout"]
    if layout == "INCOME_CERTIFICATE_PORTRAIT":
        body = f"""
        <div class="wm">{e(SYNTHETIC_WATERMARK)} | ID: {e(spec['document_id'])}</div>
        <div class="hdr">
            <h2>{e(lbl['header'])}</h2>
            <p>{e(lbl['subheader'])}</p>
        </div>
        <div class="box">
            <div class="row"><span class="lbl">{e(lbl['applicant'])}:</span> {e(spec['applicant_name'])}</div>
            <div class="row"><span class="lbl">{e(lbl['dob'])}:</span> {e(fld['dob'])}</div>
            <div class="row"><span class="lbl">{e(lbl['certificate_number'])}:</span> {e(fld['certificate_number'])}</div>
            <div class="row"><span class="lbl">{e(lbl['issue_date'])}:</span> {e(fld['issue_date'])}</div>
            <div class="row"><span class="lbl">{e(lbl['annual_income'])}:</span> {e(fld['annual_income'])}</div>
        </div>
        <div class="footer">{e(SYNTHETIC_WATERMARK)}</div>
        """
    elif layout == "BILINGUAL_TWO_COLUMN_TABLE":
        body = f"""
        <div class="wm">{e(SYNTHETIC_WATERMARK)} | ID: {e(spec['document_id'])}</div>
        <div class="hdr">
            <h2>{e(lbl['header'])}</h2>
            <p>{e(lbl['subheader'])}</p>
        </div>
        <table>
            <tr><th>{e(lbl['certificate_number'])}</th><td>{e(fld['certificate_number'])}</td></tr>
            <tr><th>{e(lbl['applicant'])}</th><td>{e(spec['applicant_name'])}</td></tr>
            <tr><th>{e(lbl['dob'])}</th><td>{e(fld['dob'])}</td></tr>
            <tr><th>{e(lbl['annual_income'])}</th><td>{e(fld['annual_income'])}</td></tr>
            <tr><th>{e(lbl['issue_date'])}</th><td>{e(fld['issue_date'])}</td></tr>
        </table>
        <div class="footer">{e(SYNTHETIC_WATERMARK)}</div>
        """
    elif layout == "COMPACT_BOXED_REGISTER":
        body = f"""
        <div class="wm">{e(SYNTHETIC_WATERMARK)} | ID: {e(spec['document_id'])}</div>
        <div class="hdr">
            <h2>{e(lbl['header'])}</h2>
            <p>{e(lbl['subheader'])}</p>
        </div>
        <table>
            <tr><td><span class="lbl">{e(lbl['applicant'])}</span><br/>{e(spec['applicant_name'])}</td>
                <td><span class="lbl">{e(lbl['dob'])}</span><br/>{e(fld['dob'])}</td></tr>
            <tr><td><span class="lbl">{e(lbl['certificate_number'])}</span><br/>{e(fld['certificate_number'])}</td>
                <td><span class="lbl">{e(lbl['issue_date'])}</span><br/>{e(fld['issue_date'])}</td></tr>
            <tr><td colspan="2"><span class="lbl">{e(lbl['annual_income'])}:</span> {e(fld['annual_income'])}</td></tr>
        </table>
        <div class="footer">{e(SYNTHETIC_WATERMARK)}</div>
        """
    else:  # SUBHADRA_STYLE_WELFARE_SLIP
        body = f"""
        <div class="wm">{e(SYNTHETIC_WATERMARK)} | ID: {e(spec['document_id'])}</div>
        <div class="hdr">
            <h2>{e(lbl['header'])}</h2>
            <p>{e(lbl['subheader'])}</p>
        </div>
        <div class="box">
            <div class="row"><span class="lbl">{e(lbl['certificate_number'])}:</span> {e(fld['certificate_number'])}</div>
            <div class="row"><span class="lbl">{e(lbl['applicant'])}:</span> {e(spec['applicant_name'])}</div>
            <div class="row"><span class="lbl">{e(lbl['dob'])}:</span> {e(fld['dob'])} &nbsp;|&nbsp; <span class="lbl">{e(lbl['issue_date'])}:</span> {e(fld['issue_date'])}</div>
            <div class="row"><span class="lbl">{e(lbl['annual_income'])}:</span> {e(fld['annual_income'])}</div>
        </div>
        <div class="footer">{e(SYNTHETIC_WATERMARK)}</div>
        """

    return body, css


def render_document_png(spec: Dict[str, Any]) -> Tuple[bytes, Tuple[int, int]]:
    """Render a spec into a deterministic, pure-raster PNG with zero native text layer."""
    body_html, css = _render_html_for_spec(spec)
    font_dir = str(_FONT_REGISTRY[spec["font_key"]]["path"].parent)
    doc = pymupdf.open()
    page = doc.new_page(width=PAGE_WIDTH_PT, height=PAGE_HEIGHT_PT)
    page.insert_htmlbox(
        (42, 42, PAGE_WIDTH_PT - 42, PAGE_HEIGHT_PT - 42),
        body_html,
        css=css,
        archive=pymupdf.Archive(font_dir),
    )
    pix = page.get_pixmap(dpi=DPI, alpha=False)
    raw_png = pix.tobytes("png")
    doc.close()

    img = Image.open(io.BytesIO(raw_png)).convert("RGB")
    if spec.get("mild_degradation"):
        img = img.rotate(1.2, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))
        img = ImageEnhance.Contrast(img).enhance(0.92)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.35))

    out_buf = io.BytesIO()
    img.save(out_buf, format="PNG", compress_level=6)
    return out_buf.getvalue(), img.size


def _collect_font_provenance() -> Dict[str, Any]:
    fonts_out: Dict[str, Any] = {}
    all_chars_by_script = {
        "ODIA": "୦୧୨୩୪୫୬୭୮୯ଅଆଇଈଉଊଋଏଐଓଔକଖଗଘଙଚଛଜଝଞଟଠଡଢଣତଥଦଧନପଫବଭମଯରଲଳଵଶଷସହ₹/-.,:",
        "DEVANAGARI": "०१२३४५६७८९अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह₹/-.,:",
    }
    for key, meta in _FONT_REGISTRY.items():
        fpath: Path = meta["path"]
        exists = fpath.is_file()
        f_sha = _sha256_file(fpath) if exists else None
        glyph_checks: Dict[str, bool] = {}
        if exists:
            pf = pymupdf.Font(fontfile=str(fpath))
            for script_name in meta["scripts_supported"]:
                if script_name in all_chars_by_script:
                    chars = all_chars_by_script[script_name]
                    glyph_checks[script_name] = all(pf.has_glyph(ord(ch)) > 0 for ch in chars)
        fonts_out[key] = {
            "family": meta["family"],
            "filename": meta["filename"],
            "host_path": str(fpath),
            "sha256": f_sha,
            "source": meta["source"],
            "license_note": meta["license_note"],
            "scripts_supported": meta["scripts_supported"],
            "glyph_coverage_verified": glyph_checks,
        }
    return {
        "corpus_version": CORPUS_VERSION,
        "rendering_engine": f"PyMuPDF {pymupdf.__version__} (HarfBuzz HTML/CSS shaping -> {DPI} DPI PNG)",
        "pillow_version": PIL.__version__,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "fonts": fonts_out,
    }


def generate_corpus(output_dir: Path) -> Dict[str, Any]:
    """Generate the complete T4.2 Indic OCR corpus, ground truth, manifests, and hashes."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "documents" / "odia").mkdir(parents=True, exist_ok=True)
    (output_dir / "documents" / "hindi").mkdir(parents=True, exist_ok=True)
    (output_dir / "ground_truth").mkdir(parents=True, exist_ok=True)
    (output_dir / "generation").mkdir(parents=True, exist_ok=True)
    (output_dir / "reports").mkdir(parents=True, exist_ok=True)

    font_prov = _collect_font_provenance()
    (output_dir / "generation" / "font_provenance.json").write_text(
        json.dumps(font_prov, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    specs = _build_corpus_specs()
    raw_records: List[Dict[str, Any]] = []
    norm_records: List[Dict[str, Any]] = []
    manifest_docs: List[Dict[str, Any]] = []
    doc_hashes: Dict[str, Dict[str, Any]] = {}

    for spec in specs:
        png_bytes, (width, height) = render_document_png(spec)
        doc_path = output_dir / spec["rel_path"]
        doc_path.write_bytes(png_bytes)
        doc_sha = _sha256_bytes(png_bytes)

        doc_hashes[spec["rel_path"]] = {
            "document_id": spec["document_id"],
            "language": spec["language"],
            "script": spec["script"],
            "sha256": doc_sha,
            "size_bytes": len(png_bytes),
        }

        font_meta = _FONT_REGISTRY[spec["font_key"]]
        manifest_docs.append({
            "document_id": spec["document_id"],
            "path": spec["rel_path"],
            "format": "PNG",
            "dimensions_px": {"width": width, "height": height},
            "dpi": DPI,
            "language": spec["language"],
            "script": spec["script"],
            "layout": spec["layout"],
            "digit_mode": spec["digit_mode"],
            "mild_degradation": spec["mild_degradation"],
            "font_key": spec["font_key"],
            "font_family": font_meta["family"],
            "font_filename": font_meta["filename"],
            "fields": sorted(spec["fields"].keys()),
            "sha256": doc_sha,
            "native_text_layer": False,
            "extraction_mode": "LOCAL_OCR",
            "evaluation_role": "held_out",
            "training_eligible": False,
        })

        for field_name, raw_val in spec["fields"].items():
            norm_val, norm_rule = _canonicalize_field(field_name, raw_val)
            prov = {
                "generator_version": GENERATOR_VERSION,
                "generator_seed": GENERATOR_SEED,
                "document_sha256": doc_sha,
                "layout": spec["layout"],
                "font_key": spec["font_key"],
                "digit_mode": spec["digit_mode"],
            }
            raw_records.append({
                "document_id": spec["document_id"],
                "language": spec["language"],
                "script": spec["script"],
                "field_name": field_name,
                "raw_value": raw_val,
                "normalization_rule": norm_rule,
                "provenance": prov,
            })
            norm_records.append({
                "document_id": spec["document_id"],
                "language": spec["language"],
                "script": spec["script"],
                "field_name": field_name,
                "raw_value": raw_val,
                "normalized_value": norm_val,
                "normalization_rule": norm_rule,
                "provenance": prov,
            })

    raw_gt = {
        "corpus_name": CORPUS_NAME,
        "corpus_version": CORPUS_VERSION,
        "evaluation_role": "held_out",
        "training_eligible": False,
        "record_count": len(raw_records),
        "records": raw_records,
    }
    norm_gt = {
        "corpus_name": CORPUS_NAME,
        "corpus_version": CORPUS_VERSION,
        "evaluation_role": "held_out",
        "training_eligible": False,
        "record_count": len(norm_records),
        "records": norm_records,
    }

    raw_path = output_dir / "ground_truth" / "raw.json"
    norm_path = output_dir / "ground_truth" / "normalized.json"
    raw_path.write_text(json.dumps(raw_gt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    norm_path.write_text(json.dumps(norm_gt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    artifact_hashes = {
        "ground_truth/raw.json": _sha256_file(raw_path),
        "ground_truth/normalized.json": _sha256_file(norm_path),
        "generation/font_provenance.json": _sha256_file(output_dir / "generation" / "font_provenance.json"),
    }

    hashes_payload = {
        "corpus_name": CORPUS_NAME,
        "corpus_version": CORPUS_VERSION,
        "document_count": len(doc_hashes),
        "documents": doc_hashes,
        "artifacts": artifact_hashes,
    }
    (output_dir / "document_hashes.json").write_text(
        json.dumps(hashes_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    manifest = {
        "corpus_name": CORPUS_NAME,
        "corpus_version": CORPUS_VERSION,
        "created_date": CREATED_DATE,
        "evaluation_purpose": "Paired baseline ('eng') vs Indic ('eng+ori' / 'eng+hin') LOCAL_OCR evaluation on held-out synthetic Odia and Hindi documents.",
        "evaluation_role": "held_out",
        "training_eligible": False,
        "extraction_mode": "LOCAL_OCR",
        "native_text_layer": False,
        "generator_version": GENERATOR_VERSION,
        "generator_seed": GENERATOR_SEED,
        "languages": ["ori", "hin"],
        "scripts": ["ODIA", "DEVANAGARI"],
        "sample_counts": {"ori": 12, "hin": 12, "total": len(manifest_docs)},
        "paired_evaluation_matrix": [
            {"language": "ori", "script": "ODIA", "baseline_ocr_lang": "eng", "indic_ocr_lang": "eng+ori"},
            {"language": "hin", "script": "DEVANAGARI", "baseline_ocr_lang": "eng", "indic_ocr_lang": "eng+hin"},
        ],
        "ground_truth_files": {
            "raw": "ground_truth/raw.json",
            "normalized": "ground_truth/normalized.json",
            "raw_sha256": artifact_hashes["ground_truth/raw.json"],
            "normalized_sha256": artifact_hashes["ground_truth/normalized.json"],
        },
        "font_provenance_file": "generation/font_provenance.json",
        "document_hashes_file": "document_hashes.json",
        "documents": manifest_docs,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def verify_hashes(output_dir: Path) -> Dict[str, Any]:
    """Recompute SHA-256 hashes for all corpus documents and artifacts against document_hashes.json."""
    hashes_data = json.loads((output_dir / "document_hashes.json").read_text(encoding="utf-8"))
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    mismatches: List[str] = []
    checked = 0

    for rel_path, entry in hashes_data["documents"].items():
        target = output_dir / rel_path
        if not target.is_file():
            mismatches.append(f"MISSING:{rel_path}")
            continue
        actual = _sha256_file(target)
        checked += 1
        if actual != entry["sha256"]:
            mismatches.append(f"HASH_MISMATCH:{rel_path}")

    for rel_path, expected_sha in hashes_data["artifacts"].items():
        target = output_dir / rel_path
        if not target.is_file():
            mismatches.append(f"MISSING:{rel_path}")
            continue
        actual = _sha256_file(target)
        checked += 1
        if actual != expected_sha:
            mismatches.append(f"HASH_MISMATCH:{rel_path}")

    # Check manifest doc hashes agree with document_hashes.json
    for doc in manifest["documents"]:
        rel_path = doc["path"]
        if doc["sha256"] != hashes_data["documents"][rel_path]["sha256"]:
            mismatches.append(f"MANIFEST_MISMATCH:{rel_path}")

    return {
        "verified": len(mismatches) == 0,
        "files_checked": checked,
        "mismatches": mismatches,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or verify DocuReady T4.2 Indic OCR corpus.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Target corpus version directory (default: eval/t4_2_indic_ocr/v1.0.0)",
    )
    parser.add_argument("--verify-hashes", action="store_true", help="Only verify hashes against document_hashes.json")
    args = parser.parse_args(argv)

    if args.verify_hashes:
        res = verify_hashes(args.output_dir)
        print(json.dumps(res, indent=2))
        return 0 if res["verified"] else 1

    manifest = generate_corpus(args.output_dir)
    res = verify_hashes(args.output_dir)
    print(json.dumps({"generated_docs": manifest["sample_counts"], "hash_verification": res}, indent=2))
    return 0 if res["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
