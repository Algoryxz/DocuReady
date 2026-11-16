import type {
  DocumentDescriptor,
  NormalizedEvidenceItem,
  RedactedAuditResult,
  RedactedFinding
} from "./types.ts";

export interface NormalizedAuditEvidence {
  findings: RedactedFinding[];
  evidenceItems: NormalizedEvidenceItem[];
  evidenceByDocumentAndPage: Record<string, Record<number, NormalizedEvidenceItem[]>>;
  documentNameMap: Record<string, string>; // maps file_name -> documentId
}

/**
 * Normalizes all findings and evidence from a RedactedAuditResult into a stable, typed structure.
 * Never invents coordinates or marks unlocated evidence as having provenance.
 */
export function normalizeFindingsAndEvidence(
  result: RedactedAuditResult | null | undefined,
  documents: DocumentDescriptor[] = []
): NormalizedAuditEvidence {
  if (!result || !Array.isArray(result.findings)) {
    return {
      findings: [],
      evidenceItems: [],
      evidenceByDocumentAndPage: {},
      documentNameMap: {}
    };
  }

  const documentNameMap: Record<string, string> = {};
  for (const doc of documents) {
    documentNameMap[doc.name] = doc.id;
  }

  const evidenceItems: NormalizedEvidenceItem[] = [];
  const evidenceByDocumentAndPage: Record<string, Record<number, NormalizedEvidenceItem[]>> = {};

  for (let fIdx = 0; fIdx < result.findings.length; fIdx++) {
    const finding = result.findings[fIdx];
    const findingEvidenceList = finding.evidence || [];

    if (findingEvidenceList.length > 0) {
      for (let eIdx = 0; eIdx < findingEvidenceList.length; eIdx++) {
        const ev = findingEvidenceList[eIdx];
        const pageNum = typeof ev.page_number === "number" && ev.page_number > 0 ? ev.page_number : 1;
        const validBBox =
          Array.isArray(ev.bounding_box) &&
          ev.bounding_box.length === 4 &&
          ev.bounding_box.every((n) => typeof n === "number" && !isNaN(n));

        const item: NormalizedEvidenceItem = {
          id: `ev-${finding.rule_id}-${fIdx}-${eIdx}`,
          ruleId: finding.rule_id,
          ruleName: finding.rule_name,
          ruleStatus: finding.status,
          severity: finding.severity,
          field: finding.field,
          documentType: ev.document_type || "UNKNOWN",
          fileName: ev.file_name || "",
          pageNumber: pageNum,
          boundingBox: validBBox ? (ev.bounding_box as [number, number, number, number]) : null,
          rawSnippet: ev.raw_snippet || "[REDACTED EVIDENCE SNIPPET]",
          extractedField: ev.extracted_field || finding.field,
          extractionMethod: ev.extraction_method || "NATIVE_VECTOR",
          ocrConfidence: typeof ev.ocr_confidence === "number" ? ev.ocr_confidence : null,
          hasProvenance: Boolean(validBBox),
          matchGrade: finding.match_grade,
          reasonCode: finding.reason_code,
          remediation: finding.remediation,
          statutoryReference: finding.statutory_reference
        };

        evidenceItems.push(item);

        if (item.fileName) {
          if (!evidenceByDocumentAndPage[item.fileName]) {
            evidenceByDocumentAndPage[item.fileName] = {};
          }
          if (!evidenceByDocumentAndPage[item.fileName][pageNum]) {
            evidenceByDocumentAndPage[item.fileName][pageNum] = [];
          }
          evidenceByDocumentAndPage[item.fileName][pageNum].push(item);
        }
      }
    } else {
      // Finding has no evidence items (e.g. missing document, missing field, or engine rule failure)
      // Do NOT invent coordinates. Explicitly record an unlocated evidence representation.
      const docName =
        finding.documents_involved && finding.documents_involved.length > 0
          ? finding.documents_involved[0]
          : "";

      const item: NormalizedEvidenceItem = {
        id: `ev-${finding.rule_id}-${fIdx}-none`,
        ruleId: finding.rule_id,
        ruleName: finding.rule_name,
        ruleStatus: finding.status,
        severity: finding.severity,
        field: finding.field,
        documentType: docName || "UNKNOWN",
        fileName: "",
        pageNumber: 1,
        boundingBox: null,
        rawSnippet: "",
        extractedField: finding.field,
        extractionMethod: "NONE",
        ocrConfidence: null,
        hasProvenance: false,
        matchGrade: finding.match_grade,
        reasonCode: finding.reason_code,
        remediation: finding.remediation,
        statutoryReference: finding.statutory_reference
      };

      evidenceItems.push(item);
    }
  }

  return {
    findings: result.findings,
    evidenceItems,
    evidenceByDocumentAndPage,
    documentNameMap
  };
}

export interface FindingFilterCriteria {
  status?: string; // "ALL" | "FAIL" | "WARN" | "PASS" | "MANUAL_REVIEW" | "MISSING"
  searchQuery?: string;
  sortBy?: "severity" | "rule_id" | "status";
}

const SEVERITY_WEIGHTS: Record<string, number> = {
  FATAL: 4,
  MAJOR: 3,
  WARNING: 2,
  INFO: 1
};

const STATUS_WEIGHTS: Record<string, number> = {
  FAIL: 5,
  MISSING: 4,
  WARN: 3,
  MANUAL_REVIEW: 2,
  PASS: 1
};

export function filterFindings(
  findings: RedactedFinding[],
  criteria: FindingFilterCriteria
): RedactedFinding[] {
  let list = [...findings];

  // 1. Filter by status
  if (criteria.status && criteria.status !== "ALL") {
    const targetStatus = criteria.status.toUpperCase();
    list = list.filter((f) => {
      if (targetStatus === "FAIL") {
        return f.status === "FAIL" || f.status === "MISSING";
      }
      return f.status.toUpperCase() === targetStatus;
    });
  }

  // 2. Filter by search query
  if (criteria.searchQuery && criteria.searchQuery.trim()) {
    const q = criteria.searchQuery.trim().toLowerCase();
    list = list.filter((f) => {
      const matchRuleId = f.rule_id?.toLowerCase().includes(q);
      const matchRuleName = f.rule_name?.toLowerCase().includes(q);
      const matchField = f.field?.toLowerCase().includes(q);
      const matchDocs = (f.documents_involved || []).some((d) => d.toLowerCase().includes(q));
      const matchReason = f.reason_code?.toLowerCase().includes(q);
      return matchRuleId || matchRuleName || matchField || matchDocs || matchReason;
    });
  }

  // 3. Sorting
  if (criteria.sortBy === "rule_id") {
    list.sort((a, b) => a.rule_id.localeCompare(b.rule_id));
  } else if (criteria.sortBy === "status") {
    list.sort((a, b) => (STATUS_WEIGHTS[b.status] || 0) - (STATUS_WEIGHTS[a.status] || 0));
  } else {
    // Default: Sort by severity descending, then penalty descending
    list.sort((a, b) => {
      const weightA = SEVERITY_WEIGHTS[a.severity] || 0;
      const weightB = SEVERITY_WEIGHTS[b.severity] || 0;
      if (weightB !== weightA) {
        return weightB - weightA;
      }
      return (b.penalty || 0) - (a.penalty || 0);
    });
  }

  return list;
}
