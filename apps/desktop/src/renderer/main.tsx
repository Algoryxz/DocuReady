import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { normalizeFindingsAndEvidence } from "../shared/evidence.ts";
import type {
  AuditProgress,
  AuditStatusResponse,
  DocumentDescriptor,
  EngineHealth,
  NormalizedEvidenceItem,
  PacketDescriptor,
  RedactedAuditResult
} from "../shared/types.ts";
import { DocumentNav } from "./components/DocumentNav.tsx";
import { EvidenceViewer } from "./components/EvidenceViewer.tsx";
import { FindingPanel } from "./components/FindingPanel.tsx";
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

  // Evidence & Workspace inspection state
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const [activeDocumentBytes, setActiveDocumentBytes] = useState<Uint8Array | null>(null);
  const [selectedRuleId, setSelectedRuleId] = useState<string | null>(null);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [targetPage, setTargetPage] = useState<number>(1);
  const [bytesCache, setBytesCache] = useState<Record<string, Uint8Array>>({});

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

  // Compute normalized findings and evidence
  const normalizedData = useMemo(() => {
    return normalizeFindingsAndEvidence(auditResult, documents);
  }, [auditResult, documents]);

  // Compute finding counts per document
  const findingCountsByDocument = useMemo(() => {
    const counts: Record<string, { pass: number; fail: number; warn: number }> = {};
    for (const doc of documents) {
      counts[doc.name] = { pass: 0, fail: 0, warn: 0 };
    }

    if (auditResult && Array.isArray(auditResult.findings)) {
      for (const finding of auditResult.findings) {
        const involved = finding.documents_involved || [];
        const isFail = finding.status === "FAIL" || finding.status === "MISSING";
        const isWarn = finding.status === "WARN";
        const isPass = finding.status === "PASS";

        for (const doc of documents) {
          const matches =
            involved.includes(doc.name) ||
            involved.some((inv) => doc.name.toLowerCase().includes(inv.toLowerCase()));
          if (matches) {
            if (isFail) counts[doc.name].fail++;
            else if (isWarn) counts[doc.name].warn++;
            else if (isPass) counts[doc.name].pass++;
          }
        }
      }
    }
    return counts;
  }, [documents, auditResult]);

  // Get active document object
  const activeDocument = useMemo(() => {
    if (!activeDocumentId && documents.length > 0) {
      return documents[0];
    }
    return documents.find((d) => d.id === activeDocumentId) || null;
  }, [activeDocumentId, documents]);

  // Fetch binary bytes when active document changes
  useEffect(() => {
    let isCancelled = false;

    if (!activeDocument) {
      setActiveDocumentBytes(null);
      return;
    }

    if (bytesCache[activeDocument.id]) {
      setActiveDocumentBytes(bytesCache[activeDocument.id]);
      return;
    }

    if (window.docureadyDesktop) {
      window.docureadyDesktop
        .getDocumentBinary(activeDocument.id)
        .then((bytes) => {
          if (!isCancelled && bytes) {
            setBytesCache((prev) => ({ ...prev, [activeDocument.id]: bytes }));
            setActiveDocumentBytes(bytes);
          }
        })
        .catch((err) => {
          console.error(`Failed to load document binary for '${activeDocument.name}':`, err);
        });
    }

    return () => {
      isCancelled = true;
    };
  }, [activeDocument, bytesCache]);

  const handleSelectDocuments = async () => {
    try {
      setErrorMessage(null);
      const selected = await window.docureadyDesktop.selectDocuments();
      if (selected.length > 0) {
        setDocuments((prev) => {
          const existingIds = new Set(prev.map((d) => d.id));
          const additions = selected.filter((d) => !existingIds.has(d.id));
          const next = [...prev, ...additions];
          if (!activeDocumentId && next.length > 0) {
            setActiveDocumentId(next[0].id);
          }
          return next;
        });
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  };

  const handleDocumentSelect = (doc: DocumentDescriptor) => {
    setActiveDocumentId(doc.id);
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
        if (response.result.findings.length > 0) {
          setSelectedRuleId(response.result.findings[0].rule_id);
        }
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
      setActiveDocumentId(null);
      setActiveDocumentBytes(null);
      setSelectedRuleId(null);
      setSelectedEvidenceId(null);
      setBytesCache({});
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  };

  // Inspect evidence callback from FindingPanel
  const handleInspectEvidence = (evidence: NormalizedEvidenceItem) => {
    setSelectedEvidenceId(evidence.id);
    setSelectedRuleId(evidence.ruleId);

    // Find matching document by file name or document type
    const matchingDoc = documents.find(
      (d) =>
        d.name === evidence.fileName ||
        d.name.toLowerCase().includes(evidence.documentType.toLowerCase())
    );

    if (matchingDoc) {
      setActiveDocumentId(matchingDoc.id);
    }

    if (evidence.pageNumber > 0) {
      setTargetPage(evidence.pageNumber);
    }
  };

  // Select finding callback (sync selection from Bounding Box or list)
  const handleSelectFinding = (ruleId: string) => {
    setSelectedRuleId(ruleId);
    const element = document.getElementById(`finding-${ruleId}`);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };

  return (
    <main className="app-shell">
      {/* Sidebar Controls */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">D</div>
          <div>
            <strong>DocuReady</strong>
            <span>EVIDENCE WORKSPACE</span>
          </div>
        </div>

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
          >
          </input>
        </div>

        <div className="sidebar-actions">
          <button
            className="btn btn-primary btn-block"
            type="button"
            onClick={handleSelectDocuments}
            disabled={auditStatus === "running"}
          >
            + Add Documents
          </button>

          {auditStatus === "running" ? (
            <button
              className="btn btn-danger btn-block"
              type="button"
              onClick={handleCancelAudit}
            >
              Cancel Audit
            </button>
          ) : (
            <button
              className="btn btn-accent btn-block"
              type="button"
              onClick={handleRunAudit}
              disabled={documents.length === 0}
            >
              {auditStatus === "completed" ? "Re-Run Audit" : "Run Pre-Flight Audit"}
            </button>
          )}

          {auditResult && (
            <div className="export-sidebar-group">
              <span className="section-title">EXPORT REPORT</span>
              <div className="export-btn-row">
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={() => handleExport("json")}
                >
                  JSON
                </button>
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={() => handleExport("markdown")}
                >
                  Markdown
                </button>
              </div>
            </div>
          )}
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

      {/* Main Panel */}
      <section className="main-panel">
        <header className="topbar">
          <div className="topbar-left">
            <span className="topbar-breadcrumb">DOCUREADY DESKTOP / WORKSPACE</span>
            {auditResult && (
              <span className="packet-badge">Packet: {auditResult.packet_id}</span>
            )}
          </div>

          <div className="topbar-right">
            {auditResult && (
              <div className="readiness-header-pill">
                <span className="readiness-label">READINESS SCORE</span>
                <span className="readiness-score-val">
                  <strong>{auditResult.readiness_score}</strong>/100
                </span>
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
            )}

            <button
              className="btn-clear"
              type="button"
              onClick={handleClearSession}
              disabled={auditStatus === "running"}
            >
              Clear Session
            </button>
          </div>
        </header>

        {/* Global Alerts / Messages */}
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

        {/* Progress Bar when running */}
        {auditStatus === "running" && progress && (
          <div className="progress-banner">
            <div className="progress-label">
              <span>Audit in Progress — Stage: <strong>{progress.stage.toUpperCase()}</strong></span>
              <span>{progress.percent}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress.percent}%` }} />
            </div>
          </div>
        )}

        {/* Three-Panel Audit Workspace Layout */}
        <div className="audit-workspace-layout">
          {/* Panel 1: Document Navigation (Left) */}
          <DocumentNav
            documents={documents}
            activeDocumentId={activeDocument?.id || null}
            onSelectDocument={handleDocumentSelect}
            findingCountsByDocument={findingCountsByDocument}
            isAuditing={auditStatus === "running"}
          />

          {/* Panel 2: Central PDF Evidence Viewer */}
          <EvidenceViewer
            document={activeDocument}
            documentBytes={activeDocumentBytes}
            evidenceItems={normalizedData.evidenceItems}
            selectedEvidenceId={selectedEvidenceId}
            onSelectEvidence={(item) => setSelectedEvidenceId(item.id)}
            onSelectFinding={handleSelectFinding}
            targetPage={targetPage}
          />

          {/* Panel 3: Finding & Explainability Panel (Right) */}
          <FindingPanel
            findings={normalizedData.findings}
            evidenceItems={normalizedData.evidenceItems}
            selectedRuleId={selectedRuleId}
            onSelectFinding={handleSelectFinding}
            onInspectEvidence={handleInspectEvidence}
          />
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
