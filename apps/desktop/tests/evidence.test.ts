import assert from "node:assert";
import test from "node:test";
import {
  filterFindings,
  normalizeFindingsAndEvidence
} from "../src/shared/evidence.ts";
import type {
  DocumentDescriptor,
  RedactedAuditResult,
  RedactedFinding
} from "../src/shared/types.ts";

test("normalizeFindingsAndEvidence parses findings with full provenance and maps to documents", () => {
  const documents: DocumentDescriptor[] = [
    {
      id: "doc-1",
      name: "application_form.pdf",
      size: 1024,
      mimeType: "application/pdf",
      fileType: "pdf"
    },
    {
      id: "doc-2",
      name: "income_cert.pdf",
      size: 2048,
      mimeType: "application/pdf",
      fileType: "pdf"
    }
  ];

  const mockResult: RedactedAuditResult = {
    packet_id: "pkt-test-01",
    scheme_name: "Test Scheme",
    readiness_score: 95,
    overall_status: "PASSED",
    summary_counts: { PASS: 1 },
    findings: [
      {
        rule_id: "RULE-NAME-PASS",
        rule_name: "Name Consistency",
        status: "PASS",
        severity: "INFO",
        penalty: 0,
        field: "APPLICANT_NAME",
        documents_involved: ["APPLICATION_FORM", "INCOME_CERT"],
        message: "Names match perfectly.",
        evidence: [
          {
            document_type: "APPLICATION_FORM",
            file_name: "application_form.pdf",
            page_number: 1,
            bounding_box: [100, 120, 250, 140],
            raw_snippet: "[REDACTED EVIDENCE SNIPPET]",
            extracted_field: "applicant_name",
            extraction_method: "NATIVE_VECTOR",
            ocr_confidence: null
          },
          {
            document_type: "INCOME_CERT",
            file_name: "income_cert.pdf",
            page_number: 1,
            bounding_box: [80, 200, 220, 220],
            raw_snippet: "[REDACTED EVIDENCE SNIPPET]",
            extracted_field: "applicant_name",
            extraction_method: "NATIVE_VECTOR",
            ocr_confidence: null
          }
        ]
      }
    ]
  };

  const normalized = normalizeFindingsAndEvidence(mockResult, documents);

  assert.strictEqual(normalized.findings.length, 1);
  assert.strictEqual(normalized.evidenceItems.length, 2);

  // Check document map
  assert.strictEqual(normalized.documentNameMap["application_form.pdf"], "doc-1");
  assert.strictEqual(normalized.documentNameMap["income_cert.pdf"], "doc-2");

  // Check item 1
  const item1 = normalized.evidenceItems[0];
  assert.strictEqual(item1.ruleId, "RULE-NAME-PASS");
  assert.strictEqual(item1.fileName, "application_form.pdf");
  assert.strictEqual(item1.pageNumber, 1);
  assert.strictEqual(item1.hasProvenance, true);
  assert.deepStrictEqual(item1.boundingBox, [100, 120, 250, 140]);

  // Check lookup by document and page
  const page1Items = normalized.evidenceByDocumentAndPage["application_form.pdf"][1];
  assert.strictEqual(page1Items.length, 1);
  assert.strictEqual(page1Items[0].extractedField, "applicant_name");
});

test("normalizeFindingsAndEvidence handles missing evidence without inventing coordinates", () => {
  const mockResult: RedactedAuditResult = {
    packet_id: "pkt-missing-01",
    scheme_name: "Test Scheme",
    readiness_score: 65,
    overall_status: "DEFECTS_FOUND",
    summary_counts: { FAIL: 1 },
    findings: [
      {
        rule_id: "RULE-DOC-01",
        rule_name: "Mandatory Document Completeness",
        status: "MISSING",
        severity: "FATAL",
        penalty: 35,
        field: "MANDATORY_DOCUMENT",
        documents_involved: ["INCOME_CERT"],
        message: "Mandatory document 'INCOME_CERT' is missing.",
        evidence: [],
        remediation: "Upload a valid income certificate."
      }
    ]
  };

  const normalized = normalizeFindingsAndEvidence(mockResult, []);

  assert.strictEqual(normalized.findings.length, 1);
  assert.strictEqual(normalized.evidenceItems.length, 1);

  const item = normalized.evidenceItems[0];
  assert.strictEqual(item.ruleId, "RULE-DOC-01");
  assert.strictEqual(item.hasProvenance, false);
  assert.strictEqual(item.boundingBox, null);
  assert.strictEqual(item.extractionMethod, "NONE");
  assert.strictEqual(item.documentType, "INCOME_CERT");
});

test("filterFindings filters by status, search term, and sorts properly", () => {
  const sampleFindings: RedactedFinding[] = [
    {
      rule_id: "RULE-DOC-01",
      rule_name: "Mandatory Document Completeness",
      status: "MISSING",
      severity: "FATAL",
      penalty: 35,
      field: "MANDATORY_DOCUMENT",
      documents_involved: ["INCOME_CERT"]
    },
    {
      rule_id: "RULE-NAME-WARN",
      rule_name: "Name Initial Mismatch",
      status: "WARN",
      severity: "WARNING",
      penalty: 10,
      field: "APPLICANT_NAME",
      documents_involved: ["APPLICATION_FORM"]
    },
    {
      rule_id: "RULE-DOB-PASS",
      rule_name: "Date of Birth Verification",
      status: "PASS",
      severity: "INFO",
      penalty: 0,
      field: "DOB",
      documents_involved: ["APPLICATION_FORM"]
    }
  ];

  // Filter FAIL (includes MISSING)
  const fails = filterFindings(sampleFindings, { status: "FAIL" });
  assert.strictEqual(fails.length, 1);
  assert.strictEqual(fails[0].rule_id, "RULE-DOC-01");

  // Filter WARN
  const warns = filterFindings(sampleFindings, { status: "WARN" });
  assert.strictEqual(warns.length, 1);
  assert.strictEqual(warns[0].rule_id, "RULE-NAME-WARN");

  // Filter REVIEW / MANUAL_REVIEW
  const reviewFindings: RedactedFinding[] = [
    {
      rule_id: "RULE-NAME-UNCERTAIN",
      rule_name: "Name Uncertain OCR",
      status: "REVIEW",
      severity: "REVIEW",
      penalty: 10,
      field: "APPLICANT_NAME_UNCERTAIN",
      documents_involved: ["APPLICATION_FORM", "INCOME_CERT"]
    }
  ];
  assert.strictEqual(filterFindings(reviewFindings, { status: "REVIEW" }).length, 1);
  assert.strictEqual(filterFindings(reviewFindings, { status: "MANUAL_REVIEW" }).length, 1);

  // Search by field "DOB"
  const dobSearch = filterFindings(sampleFindings, { searchQuery: "dob" });
  assert.strictEqual(dobSearch.length, 1);
  assert.strictEqual(dobSearch[0].rule_id, "RULE-DOB-PASS");

  // Sort by Rule ID
  const sortedById = filterFindings(sampleFindings, { sortBy: "rule_id" });
  assert.strictEqual(sortedById[0].rule_id, "RULE-DOB-PASS");
  assert.strictEqual(sortedById[1].rule_id, "RULE-DOC-01");
  assert.strictEqual(sortedById[2].rule_id, "RULE-NAME-WARN");

  // Default sort by Severity (FATAL > WARNING > INFO)
  const sortedBySeverity = filterFindings(sampleFindings, {});
  assert.strictEqual(sortedBySeverity[0].rule_id, "RULE-DOC-01");
  assert.strictEqual(sortedBySeverity[1].rule_id, "RULE-NAME-WARN");
  assert.strictEqual(sortedBySeverity[2].rule_id, "RULE-DOB-PASS");
});
