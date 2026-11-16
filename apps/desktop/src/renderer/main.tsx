import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AuditProgress,
  AuditStatusResponse,
  DocumentDescriptor,
  EngineHealth,
  PacketDescriptor,
  RedactedAuditResult
} from "../shared/types";
import "./styles.css";

function App(): React.JSX.Element {
  const [health, setHealth] = useState<EngineHealth | null>(null);
  const [documents, setDocuments] = useState<DocumentDescriptor[]>([]);
  const [schemeId, setSchemeId] = useState<string>("odisha_post_matric");
  const [asOfDate, setAsOfDate] = useState<string>("2026-11-16");
  const [currentPacket, setCurrentPacket] = useState<PacketDescriptor | null>(null);
  const [auditStatus, setAuditStatus] = useState<string>("idle");
  const [progress, setProgress] = useState<AuditProgress | null>(null);
  const [auditResult, setAuditResult] = useState<RedactedAuditResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);

  useEffect(() => {
    // Initial health check
    if (window.docureadyDesktop) {
      window.docureadyDesktop
        .getEngineHealth()
        .then(setHealth)
        .catch((err) => {
          setHealth({
            ok: false,
            sidecar: "error",
            protocol: 1,
            engineVersion: "unknown",
            pythonVersion: "unknown",
            pdfBackend: "unknown",
            ocrAvailable: false,
            status: "error",
            error: String(err)
          });
        });

      // Subscribe to progress events
      const unsubscribe = window.docureadyDesktop.onAuditProgress((p) => {
        setProgress(p);
      });

      return () => {
        unsubscribe();
      };
    }
  }, []);

  const handleSelectDocuments = async () => {
    try {
      setErrorMessage(null);
      const selected = await window.docureadyDesktop.selectDocuments();
      if (selected.length > 0) {
        setDocuments((prev) => {
          const existingIds = new Set(prev.map((d) => d.id));
          const additions = selected.filter((d) => !existingIds.has(d.id));
          return [...prev, ...additions];
        });
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  };

  const handleRemoveDocument = (id: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  };

  const handleRunAudit = async () => {
    if (documents.length === 0) {
      setErrorMessage("Please select at least one document to audit.");
      return;
    }

    try {
      setErrorMessage(null);
      setExportMessage(null);
      setAuditStatus("running");
      setProgress({
        jobId: "init",
        stage: "staging",
        completed: 0,
        total: 5,
        percent: 0
      });

      // 1. Create packet in isolated workspace
      const packet = await window.docureadyDesktop.createPacket({
        documentIds: documents.map((d) => d.id),
        schemeId,
        asOf: asOfDate
      });
      setCurrentPacket(packet);

      // 2. Start audit
      const response: AuditStatusResponse = await window.docureadyDesktop.startAudit(
        packet.packetId
      );

      if (response.status === "completed" && response.result) {
        setAuditStatus("completed");
        setAuditResult(response.result);
      } else if (response.status === "failed") {
        setAuditStatus("failed");
        setErrorMessage(response.error?.message || "Audit execution failed.");
      } else if (response.status === "cancelled") {
        setAuditStatus("cancelled");
      }
    } catch (err) {
      setAuditStatus("failed");
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  };

  const handleCancelAudit = async () => {
    if (!currentPacket) return;
    try {
      await window.docureadyDesktop.cancelAudit(currentPacket.packetId);
      setAuditStatus("cancelled");
      setProgress(null);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  };

  const handleExport = async (format: "json" | "markdown") => {
    if (!currentPacket) return;
    try {
      setExportMessage(null);
      const res = await window.docureadyDesktop.exportReport({
        packetId: currentPacket.packetId,
        format
      });
      if (res.ok && res.filePath) {
        setExportMessage(`Report exported successfully to: ${res.filePath}`);
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  };

  const handleClearSession = async () => {
    try {
      await window.docureadyDesktop.clearSession();
      setDocuments([]);
      setCurrentPacket(null);
      setAuditStatus("idle");
      setProgress(null);
      setAuditResult(null);
      setErrorMessage(null);
      setExportMessage(null);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">D</div>
          <div>
            <strong>DocuReady</strong>
            <span>PRE-FLIGHT AUDIT</span>
          </div>
        </div>

        <nav aria-label="Primary navigation">
          <button className="nav-item active" type="button">
            Packet Workspace
          </button>
        </nav>

        <div className="sidebar-section">
          <label className="section-title" htmlFor="scheme-select">SCHEME PACK</label>
          <select
            id="scheme-select"
            className="scheme-dropdown"
            value={schemeId}
            onChange={(e) => setSchemeId(e.target.value)}
            disabled={auditStatus === "running"}
          >
            <option value="odisha_post_matric">Odisha Post-Matric Scholarship</option>
            <option value="general_scholarship">General Scheme Baseline</option>
          </select>
        </div>

        <div className="sidebar-section">
          <label className="section-title" htmlFor="asof-input">EVALUATION DATE (AS-OF)</label>
          <input
            id="asof-input"
            type="date"
            className="date-input"
            value={asOfDate}
            onChange={(e) => setAsOfDate(e.target.value)}
            disabled={auditStatus === "running"}
          />
        </div>

        <div className="sidebar-footer">
          <div className="engine-status">
            <span
              className={`status-dot ${
                health?.status === "healthy"
                  ? "dot-green"
                  : health?.status === "error"
                  ? "dot-red"
                  : "dot-yellow"
              }`}
            />
            <div className="engine-details">
              <strong>
                {health?.status === "healthy"
                  ? "Python Engine Online"
                  : "Engine Connecting..."}
              </strong>
              <span>
                v{health?.engineVersion || "0.1.0"} · Python {health?.pythonVersion || ""} ·{" "}
                {health?.pdfBackend || "pymupdf"}
              </span>
            </div>
          </div>
          <div className="privacy-badge">
            <span className="privacy-icon">🔒</span>
            <span>100% Offline · Local Workspace</span>
          </div>
        </div>
      </aside>

      <section className="main-panel">
        <header className="topbar">
          <span>DOCUREADY DESKTOP / WORKSPACE</span>
          <div className="topbar-right">
            <button
              className="btn-clear"
              type="button"
              onClick={handleClearSession}
              disabled={auditStatus === "running"}
            >
              Clear Session
            </button>
            <span className="version">
              APP v{window.docureadyDesktop?.version || "0.1.0"}
            </span>
          </div>
        </header>

        <div className="content">
          <div className="eyebrow">STATUTORY DOCUMENT PREPARATION</div>
          <h1>Pre-Flight Readiness Audit</h1>
          <p className="intro">
            Check your scholarship document packet for clerical discrepancies, missing
            certificates, and name/DOB/income inconsistencies before portal submission.
          </p>

          {errorMessage && (
            <div className="alert alert-error" role="alert">
              <strong>Error:</strong> {errorMessage}
            </div>
          )}

          {exportMessage && (
            <div className="alert alert-success" role="status">
              <strong>Success:</strong> {exportMessage}
            </div>
          )}

          {/* Section 1: Document Selection */}
          <section className="card document-selection-card">
            <div className="card-header">
              <div>
                <h2>Document Intake</h2>
                <p>
                  Select PDF or image documents from your computer. Files are staged in an
                  isolated local workspace.
                </p>
              </div>
              <button
                className="btn btn-primary"
                type="button"
                onClick={handleSelectDocuments}
                disabled={auditStatus === "running"}
              >
                + Add Documents
              </button>
            </div>

            {documents.length === 0 ? (
              <div className="empty-dropzone" onClick={handleSelectDocuments}>
                <span className="empty-icon">📄</span>
                <p>No documents selected yet.</p>
                <small>Click to choose PDFs or images from your computer</small>
              </div>
            ) : (
              <ul className="doc-list" aria-label="Selected documents">
                {documents.map((doc) => (
                  <li key={doc.id} className="doc-item">
                    <span className="doc-badge">{doc.fileType.toUpperCase()}</span>
                    <span className="doc-name">{doc.name}</span>
                    <span className="doc-size">
                      {(doc.size / 1024).toFixed(1)} KB
                    </span>
                    <button
                      className="btn-remove"
                      type="button"
                      aria-label={`Remove ${doc.name}`}
                      onClick={() => handleRemoveDocument(doc.id)}
                      disabled={auditStatus === "running"}
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Section 2: Audit Actions & Progress */}
          <section className="card audit-action-card">
            <div className="action-row">
              <div>
                <h2>Run Audit Pipeline</h2>
                <p>
                  Executes the Python audit engine with 10 deterministic statutory rules.
                </p>
              </div>
              <div className="action-buttons">
                {auditStatus === "running" ? (
                  <button
                    className="btn btn-danger"
                    type="button"
                    onClick={handleCancelAudit}
                  >
                    Cancel Audit
                  </button>
                ) : (
                  <button
                    className="btn btn-accent"
                    type="button"
                    onClick={handleRunAudit}
                    disabled={documents.length === 0}
                  >
                    Run Pre-Flight Audit
                  </button>
                )}
              </div>
            </div>

            {auditStatus === "running" && progress && (
              <div className="progress-container">
                <div className="progress-label">
                  <span>Stage: <strong>{progress.stage.toUpperCase()}</strong></span>
                  <span>{progress.percent}%</span>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${progress.percent}%` }}
                  />
                </div>
              </div>
            )}
          </section>

          {/* Section 3: Audit Results */}
          {auditStatus === "completed" && auditResult && (
            <section className="card results-card" aria-labelledby="results-title">
              <div className="results-header">
                <div>
                  <h2 id="results-title">Audit Results</h2>
                  <span className="packet-id-tag">Packet: {auditResult.packet_id}</span>
                </div>
                <div className="score-badge-group">
                  <div className="score-pill">
                    <span className="score-number">{auditResult.readiness_score}</span>
                    <span className="score-denom">/100</span>
                  </div>
                  <span
                    className={`status-pill ${
                      auditResult.overall_status === "NO_ISSUES_FOUND"
                        ? "pill-green"
                        : "pill-orange"
                    }`}
                  >
                    {auditResult.overall_status}
                  </span>
                </div>
              </div>

              {/* Summary Counter Grid */}
              <div className="summary-grid">
                <div className="summary-card">
                  <span className="summary-num">{auditResult.findings.length}</span>
                  <span className="summary-lbl">Rules Evaluated</span>
                </div>
                <div className="summary-card">
                  <span className="summary-num summary-green">
                    {auditResult.summary_counts?.PASS || 0}
                  </span>
                  <span className="summary-lbl">Passed</span>
                </div>
                <div className="summary-card">
                  <span className="summary-num summary-yellow">
                    {auditResult.summary_counts?.WARN || 0}
                  </span>
                  <span className="summary-lbl">Warnings</span>
                </div>
                <div className="summary-card">
                  <span className="summary-num summary-red">
                    {auditResult.summary_counts?.FAIL || 0}
                  </span>
                  <span className="summary-lbl">Action Required</span>
                </div>
              </div>

              {/* Findings Table */}
              <div className="findings-section">
                <h3>Evaluated Rules & Findings</h3>
                <div className="findings-table-wrapper">
                  <table className="findings-table">
                    <thead>
                      <tr>
                        <th>Rule ID</th>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Field</th>
                        <th>Severity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditResult.findings.map((f, i) => (
                        <tr key={`${f.rule_id}-${i}`}>
                          <td><code>{f.rule_id}</code></td>
                          <td>{f.rule_name}</td>
                          <td>
                            <span
                              className={`finding-status ${
                                f.status === "PASS"
                                  ? "badge-pass"
                                  : f.status === "FAIL"
                                  ? "badge-fail"
                                  : "badge-warn"
                              }`}
                            >
                              {f.status}
                            </span>
                          </td>
                          <td>{f.field}</td>
                          <td>{f.severity}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Export Controls */}
              <div className="export-bar">
                <span>Export Redacted Audit Report:</span>
                <button
                  className="btn btn-outline"
                  type="button"
                  onClick={() => handleExport("json")}
                >
                  Export JSON
                </button>
                <button
                  className="btn btn-outline"
                  type="button"
                  onClick={() => handleExport("markdown")}
                >
                  Export Markdown
                </button>
              </div>
            </section>
          )}

          <div className="notice">
            <strong>Advisory tool only</strong>
            <p>
              DocuReady checks the supplied evidence against configured statutory
              rules. It does not determine legal eligibility or guarantee acceptance
              by any government portal or authority.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
