# DOCUREADY — LOOP 42 NATIVE VS. FALLBACK EQUIVALENCE

Tested all **6** language configurations comparing native `libtesseract-5.dll` (`TessBaseAPIGetUTF8Text` & `TessBaseAPIGetTsvText`) against subprocess `pytesseract` using identical images, grayscale inputs, PSM (`3`), and `tessdata`:

| Language Config | Fixture | `init_rc` | `UTF8Text` Exact Equal | CER Diff | `TSV` Words Equal | `TSV` Boxes Equal | Words (Nat / Sub) |
|---|---|---:|---|---|---|---:|---:|
| `eng` | `DOC_CTRL_01` | `0` | **Yes** | `0.0000` | **Yes** | **Yes** | `59 / 59` |
| `hin` | `DOC_HIN_01` | `0` | **Yes** | `0.0000` | **Yes** | **Yes** | `73 / 73` |
| `ori` | `DOC_EXT_06` | `0` | **Yes** | `0.0000` | **Yes** | **Yes** | `132 / 132` |
| `eng+hin` | `DOC_MIX_01` | `0` | **Yes** | `0.0000` | **Yes** | **Yes** | `53 / 53` |
| `eng+ori` | `DOC_MIX_02` | `0` | **Yes** | `0.0000` | **Yes** | **Yes** | `46 / 46` |
| `eng+hin+ori` | `DOC_EXT_06` | `0` | **Yes** | `0.0000` | **Yes** | **Yes** | `117 / 117` |

**100% word-for-word and bounding-box parity** across all 6 language configurations.
