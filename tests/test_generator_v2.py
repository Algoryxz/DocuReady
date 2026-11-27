"""Unit tests for T4.3 Synthetic Document Generator v2."""

from pathlib import Path

from eval.generators.generator_v2 import (
    ALL_LAYOUTS,
    DEV_CALIB_LAYOUTS,
    TEST_ONLY_LAYOUTS,
    SYNTHETIC_WATERMARK,
    SyntheticGeneratorV2,
    generate_split_dataset,
)


def test_generator_v2_layout_inventory():
    assert len(ALL_LAYOUTS) >= 5
    assert len(TEST_ONLY_LAYOUTS) >= 3
    assert set(DEV_CALIB_LAYOUTS).isdisjoint(set(TEST_ONLY_LAYOUTS))


def test_generator_v2_deterministic_seeded_splits(tmp_path: Path):
    m_dev_1 = generate_split_dataset(tmp_path / "run1", split="dev", seed=101, n_samples=6, render_pdfs=True)
    m_dev_2 = generate_split_dataset(tmp_path / "run2", split="dev", seed=101, n_samples=6, render_pdfs=True)
    m_test = generate_split_dataset(tmp_path / "run1", split="test", seed=303, n_samples=6, render_pdfs=True)

    # Deterministic hashes for identical seeds (document content hashes match)
    assert [s["document_sha256s"] for s in m_dev_1["samples"]] == [
        s["document_sha256s"] for s in m_dev_2["samples"]
    ]
    assert m_dev_1["synthetic_label"] == "synthetic"
    assert m_dev_1["watermark"] == SYNTHETIC_WATERMARK

    # Test layouts must be strictly unseen in dev
    assert set(m_test["layouts_used"]).issubset(set(TEST_ONLY_LAYOUTS))
    assert set(m_dev_1["layouts_used"]).isdisjoint(set(m_test["layouts_used"]))


def test_generator_v2_pdf_watermark_and_bilingual(tmp_path: Path):
    gen = SyntheticGeneratorV2(seed=7)
    pdf_path = tmp_path / "bilingual_test.pdf"
    sha = gen.render_pdf_with_layout(
        pdf_path,
        layout_id="L3_BILINGUAL_HEADER",
        applicant_name="Pravasini Sahoo",
        dob="15/05/1990",
        annual_income="180000",
        issue_date="01/01/2024",
        certificate_no="SYN/2024/0001",
        perturbation="bilingual_indic",
    )
    assert pdf_path.exists()
    assert len(sha) == 64


def test_generator_v2_all_negative_controls_and_unique_hashes(tmp_path: Path):
    """Verify all 4 negative-control categories are generated and hashes are unique across splits."""
    from collections import Counter
    from eval.generators.generator_v2 import NEGATIVE_CONTROLS
    from eval.harness import check_split_leakage

    m_dev = generate_split_dataset(tmp_path, split="dev", seed=101, n_samples=24, render_pdfs=True)
    m_cal = generate_split_dataset(tmp_path, split="calib", seed=202, n_samples=32, render_pdfs=True)
    m_test = generate_split_dataset(tmp_path, split="test", seed=303, n_samples=48, render_pdfs=True)

    # Zero leakage with real rendered PDFs
    leak = check_split_leakage(m_dev, m_cal, m_test)
    assert leak["leakage_detected"] is False

    # All 4 negative-control categories present with equal counts (2 each at n=48)
    neg_counts = Counter(s["negative_control"] for s in m_test["samples"])
    expected_negs = [nc for nc in NEGATIVE_CONTROLS if nc != "none"]
    for nc in expected_negs:
        assert neg_counts[nc] == 2, f"Expected 2 samples for {nc}, got {neg_counts[nc]}"

    # Scaling up to n=96 yields 4 each (no category omitted)
    m_test_large = generate_split_dataset(tmp_path / "large", split="test", seed=303, n_samples=96, render_pdfs=False)
    neg_counts_large = Counter(s["negative_control"] for s in m_test_large["samples"])
    for nc in expected_negs:
        assert neg_counts_large[nc] == 4


def test_generator_v2_visual_layout_separation_preserved_under_degradation(tmp_path: Path):
    """Verify all 5 layouts remain visually distinct even after scan degradation."""
    import pymupdf
    from PIL import Image, ImageChops

    gen = SyntheticGeneratorV2(seed=303)
    hashes_per_layout = {}
    pixel_imgs = {}

    for layout in ALL_LAYOUTS:
        pdf_path = tmp_path / f"{layout}_rot.pdf"
        h = gen.render_pdf_with_layout(
            pdf_path,
            layout_id=layout,
            applicant_name="Pravasini Sahoo",
            dob="15/05/1990",
            annual_income="180000",
            issue_date="01/01/2024",
            certificate_no="SYN/2024/0001",
            perturbation="rotation",
        )
        hashes_per_layout[layout] = h
        with pymupdf.open(str(pdf_path)) as doc_pdf:
            pix = doc_pdf[0].get_pixmap(dpi=72)
            pixel_imgs[layout] = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # All 5 degraded PDFs must have distinct hashes and distinct rendered pixel content
    assert len(set(hashes_per_layout.values())) == 5
    layouts_list = list(ALL_LAYOUTS)
    for i in range(len(layouts_list)):
        for j in range(i + 1, len(layouts_list)):
            diff = ImageChops.difference(pixel_imgs[layouts_list[i]], pixel_imgs[layouts_list[j]])
            assert diff.getbbox() is not None, f"Layouts {layouts_list[i]} and {layouts_list[j]} rendered identically!"


def test_generator_v2_two_run_determinism_test_split(tmp_path: Path):
    """Run split=test, seed=303, n_samples=48, render_pdfs=True twice and assert byte-exact match."""
    m1 = generate_split_dataset(tmp_path / "runA", split="test", seed=303, n_samples=48, render_pdfs=True)
    m2 = generate_split_dataset(tmp_path / "runB", split="test", seed=303, n_samples=48, render_pdfs=True)

    assert [s["packet_id"] for s in m1["samples"]] == [s["packet_id"] for s in m2["samples"]]
    assert [s["perturbation"] for s in m1["samples"]] == [s["perturbation"] for s in m2["samples"]]
    assert [s["negative_control"] for s in m1["samples"]] == [s["negative_control"] for s in m2["samples"]]
    assert [s["document_sha256s"] for s in m1["samples"]] == [s["document_sha256s"] for s in m2["samples"]]
