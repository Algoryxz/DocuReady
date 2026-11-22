import React, { useState } from "react";
import { filterFindings } from "../../shared/evidence.ts";
import type {
  NormalizedEvidenceItem,
  RedactedFinding
} from "../../shared/types.ts";

export interface FindingPanelProps {
  findings: RedactedFinding[];
  evidenceItems: NormalizedEvidenceItem[];
  selectedRuleId: string | null;
  onSelectFinding: (ruleId: string) => void;
  onInspectEvidence: (evidence: NormalizedEvidenceItem) => void;
}

function getStatusPresentation(status: string): { label: string; icon: string; className: string } {
  switch (status.toUpperCase()) {
    case "PASS":
      return { label: "PASS", icon: "✅", className: "pass" };
    case "WARN":
      return { label: "WARN", icon: "⚠️", className: "warn" };
    case "REVIEW":
    case "MANUAL_REVIEW":
      return { label: "REVIEW", icon: "🔍", className: "review" };
    case "MISSING":
      return { label: "MISSING", icon: "🚫", className: "fail" };
    case "FAIL":
    default:
      return { label: "FAIL", icon: "❌", className: "fail" };
  }
}

function getReviewGuidance(reasonCode?: string): string {
  if (!reasonCode) {
    return "Automated pre-flight check conservatively abstained from auto-approval. Please inspect the original document to verify compliance.";
  }
  const code = reasonCode.toUpperCase();
  if (code.includes("POOR_SCAN") || code.includes("UNREADABLE") || code.includes("CONFIDENCE")) {
    return "Scan resolution, contrast, or orientation degraded OCR legibility below safe certainty thresholds. Inspect the original physical document.";
  }
  if (code.includes("AMBIGUOUS") || code.includes("MULTIPLE") || code.includes("CONFLICT")) {
    return "Multiple candidate values or dates detected on the page. Human clerical judgment is required to verify the statutory value.";
  }
  if (code.includes("NAME") || code.includes("VARIATION") || code.includes("INITIAL")) {
    return "Minor name variation detected across records (e.g. abbreviations or spelling variation). Verify applicant identity manually.";
  }
  if (code.includes("EXPIRED") || code.includes("VALIDITY") || code.includes("GRACE")) {
    return "Document validity is nearing boundary conditions or requires renewal verification. Verify active validity status.";
  }
  return `Conservative pre-flight check triggered under reason '${reasonCode}'. Verify evidence details manually before portal submission.`;
}

export const FindingPanel: React.FC<FindingPanelProps> = ({
  findings,
  evidenceItems,
  selectedRuleId,
  onSelectFinding,
  onInspectEvidence
}) => {
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortBy, setSortBy] = useState<"severity" | "rule_id" | "status">("severity");

  // Summary counts
  const counts = {
    all: findings.length,
    fail: findings.filter((f) => f.status === "FAIL" || f.status === "MISSING").length,
    warn: findings.filter((f) => f.status === "WARN").length,
    review: findings.filter((f) => f.status === "REVIEW" || f.status === "MANUAL_REVIEW").length,
    pass: findings.filter((f) => f.status === "PASS").length
  };

  const filteredFindings = filterFindings(findings, {
    status: statusFilter,
    searchQuery,
    sortBy
  });

  return (
    <section className="finding-panel" role="region" aria-label="Audit findings and explainability">
      <div className="panel-header">
        <h3 className="panel-title">Findings & Explainability</h3>
        <span className="badge count-badge">{findings.length} Total</span>
      </div>

      {/* Filter and Search Controls */}
      <div className="finding-controls">
        <div className="filter-pills" role="tablist" aria-label="Filter findings by status">
          <button
            type="button"
            role="tab"
            aria-selected={statusFilter === "ALL"}
            className={`filter-pill ${statusFilter === "ALL" ? "active" : ""}`}
            onClick={() => setStatusFilter("ALL")}
          >
            ALL ({counts.all})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={statusFilter === "FAIL"}
            className={`filter-pill fail ${statusFilter === "FAIL" ? "active" : ""}`}
            onClick={() => setStatusFilter("FAIL")}
          >
            ❌ FAIL ({counts.fail})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={statusFilter === "WARN"}
            className={`filter-pill warn ${statusFilter === "WARN" ? "active" : ""}`}
            onClick={() => setStatusFilter("WARN")}
          >
            ⚠️ WARN ({counts.warn})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={statusFilter === "REVIEW" || statusFilter === "MANUAL_REVIEW"}
            className={`filter-pill review ${statusFilter === "REVIEW" || statusFilter === "MANUAL_REVIEW" ? "active" : ""}`}
            onClick={() => setStatusFilter("REVIEW")}
          >
            🔍 REVIEW ({counts.review})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={statusFilter === "PASS"}
            className={`filter-pill pass ${statusFilter === "PASS" ? "active" : ""}`}
            onClick={() => setStatusFilter("PASS")}
          >
            ✅ PASS ({counts.pass})
          </button>
        </div>

        <div className="search-sort-bar">
          <input
            type="text"
            className="search-input"
            placeholder="Search rule ID, field, message..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Search audit findings"
          />
          <select
            className="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            title="Sort findings"
            aria-label="Sort findings order"
          >
            <option value="severity">Sort: Severity</option>
            <option value="rule_id">Sort: Rule ID</option>
            <option value="status">Sort: Status</option>
          </select>
        </div>
      </div>

      {/* Findings List */}
      <div className="findings-list" id="findings-list">
        {filteredFindings.length === 0 ? (
          <div className="empty-state">
            <p>No findings match the selected filter criteria.</p>
          </div>
        ) : (
          filteredFindings.map((finding) => {
            const isSelected = selectedRuleId === finding.rule_id;
            const findingEvidence = evidenceItems.filter(
              (ev) => ev.ruleId === finding.rule_id && ev.hasProvenance
            );

            const pres = getStatusPresentation(finding.status);
            const isReview = finding.status === "REVIEW" || finding.status === "MANUAL_REVIEW";
            const isMissing = finding.status === "MISSING" || finding.rule_id.startsWith("RULE-DOC");

            return (
              <div
                key={finding.rule_id}
                id={`finding-${finding.rule_id}`}
                className={`finding-card ${pres.className} ${isSelected ? "selected" : ""}`}
                role="button"
                tabIndex={0}
                aria-expanded={isSelected}
                aria-label={`${finding.rule_name}, Status: ${finding.status}, Severity: ${finding.severity}`}
                onClick={() => onSelectFinding(finding.rule_id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onSelectFinding(finding.rule_id);
                  }
                }}
              >
                <div className="finding-header">
                  <div className="finding-badges">
                    <span className={`status-badge status-${pres.className}`}>
                      {pres.icon} {pres.label}
                    </span>
                    <span className={`severity-badge severity-${finding.severity?.toLowerCase() || "info"}`}>
                      {finding.severity}
                    </span>
                    {finding.penalty > 0 && (
                      <span className="penalty-badge">-{finding.penalty} pts</span>
                    )}
                  </div>
                  <span className="rule-id-label">{finding.rule_id}</span>
                </div>

                <h4 className="rule-title">{finding.rule_name}</h4>

                <div className="finding-meta-grid">
                  <div className="meta-item">
                    <span className="meta-key">Field</span>
                    <span className="meta-val">{finding.field}</span>
                  </div>
                  {finding.match_grade && (
                    <div className="meta-item">
                      <span className="meta-key">Match Grade</span>
                      <span className="meta-val">{finding.match_grade}</span>
                    </div>
                  )}
                  {finding.reason_code && (
                    <div className="meta-item">
                      <span className="meta-key">Reason Code</span>
                      <span className="meta-val code-text">{finding.reason_code}</span>
                    </div>
                  )}
                </div>

                {finding.message && (
                  <p className="finding-message">{finding.message}</p>
                )}

                {/* Dedicated Review Callout */}
                {isReview && (
                  <div className="review-guidance-callout" role="alert">
                    <div className="callout-header">
                      <span className="callout-icon">🔍</span>
                      <strong>Human Review Required (Conservative Abstention)</strong>
                    </div>
                    <p className="callout-body">{getReviewGuidance(finding.reason_code)}</p>
                  </div>
                )}

                {/* Dedicated Missing Document Callout */}
                {isMissing && finding.status === "MISSING" && (
                  <div className="missing-doc-callout" role="alert">
                    <div className="callout-header">
                      <span className="callout-icon">🚫</span>
                      <strong>Statutory Document Missing</strong>
                    </div>
                    <p className="callout-body">
                      This required document is missing from the staged session. Upload it to complete pre-flight validation.
                    </p>
                  </div>
                )}

                {finding.statutory_reference && (
                  <div className="statutory-reference">
                    <span className="ref-icon">📜</span>
                    <span className="ref-text">{finding.statutory_reference}</span>
                  </div>
                )}

                {finding.remediation && (
                  <div className="remediation-block">
                    <strong className="remediation-label">Remediation Action:</strong>
                    <p className="remediation-text">{finding.remediation}</p>
                  </div>
                )}

                {/* Evidence Provenance Section */}
                <div className="evidence-section">
                  <div className="evidence-section-header">
                    <span className="evidence-title">Document Evidence</span>
                    <span className="evidence-count">
                      {findingEvidence.length} source reference(s)
                    </span>
                  </div>

                  {findingEvidence.length === 0 ? (
                    <div className="unlocated-evidence-notice">
                      <span className="notice-icon">ℹ️</span>
                      <span className="notice-text">
                        No visual evidence provenance available for this finding (e.g. absent document or non-extracted field).
                      </span>
                    </div>
                  ) : (
                    <div className="evidence-card-list">
                      {findingEvidence.map((ev) => (
                        <div key={ev.id} className="evidence-item-card">
                          <div className="evidence-item-header">
                            <span className="evidence-doc-name">
                              📄 {ev.fileName || ev.documentType} (Page {ev.pageNumber})
                            </span>
                            <span className="extraction-method-tag">
                              {ev.extractionMethod}
                            </span>
                          </div>

                          {ev.rawSnippet && (
                            <div className="evidence-snippet">
                              <code>{ev.rawSnippet}</code>
                            </div>
                          )}

                          <button
                            type="button"
                            className="inspect-evidence-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectFinding(finding.rule_id);
                              onInspectEvidence(ev);
                            }}
                          >
                            Inspect in Viewer ↗
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
};
                <div className="evidence-section">
                  <div className="evidence-section-header">
                    <span className="evidence-title">Document Evidence</span>
                    <span className="evidence-count">
                      {findingEvidence.length} source reference(s)
                    </span>
                  </div>

                  {findingEvidence.length === 0 ? (
                    <div className="unlocated-evidence-notice">
                      <span className="notice-icon">ℹ️</span>
                      <span className="notice-text">
                        No visual evidence provenance available for this finding (e.g. absent document or non-extracted field).
                      </span>
                    </div>
                  ) : (
                    <div className="evidence-card-list">
                      {findingEvidence.map((ev) => (
                        <div key={ev.id} className="evidence-item-card">
                          <div className="evidence-item-header">
                            <span className="evidence-doc-name">
                              📄 {ev.fileName || ev.documentType} (Page {ev.pageNumber})
                            </span>
                            <span className="extraction-method-tag">
                              {ev.extractionMethod}
                            </span>
                          </div>

                          {ev.rawSnippet && (
                            <div className="evidence-snippet">
                              <code>{ev.rawSnippet}</code>
                            </div>
                          )}

                          <button
                            type="button"
                            className="inspect-evidence-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectFinding(finding.rule_id);
                              onInspectEvidence(ev);
                            }}
                          >
                            Inspect in Viewer ↗
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
};
