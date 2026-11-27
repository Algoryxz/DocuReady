import React from "react";
import type { DocumentDescriptor } from "../../shared/types.ts";

export interface DocumentNavProps {
  documents: DocumentDescriptor[];
  activeDocumentId: string | null;
  onSelectDocument: (doc: DocumentDescriptor) => void;
  findingCountsByDocument?: Record<
    string,
    { pass: number; fail: number; warn: number }
  >;
  isAuditing?: boolean;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export const DocumentNav: React.FC<DocumentNavProps> = ({
  documents,
  activeDocumentId,
  onSelectDocument,
  findingCountsByDocument = {},
  isAuditing = false
}) => {
  return (
    <aside className="document-nav-panel" aria-label="Audit documents navigation">
      <div className="panel-header">
        <h3 className="panel-title">Audit Documents</h3>
        <span className="badge count-badge">{documents.length}</span>
      </div>

      <div className="document-list">
        {documents.length === 0 ? (
          <div className="empty-state">
            <p>No documents staged in current session.</p>
          </div>
        ) : (
          documents.map((doc) => {
            const isActive = doc.id === activeDocumentId;
            const counts = findingCountsByDocument[doc.name] || {
              pass: 0,
              fail: 0,
              warn: 0
            };

            return (
              <button
                key={doc.id}
                type="button"
                className={`document-card ${isActive ? "active" : ""}`}
                onClick={() => onSelectDocument(doc)}
                disabled={isAuditing}
                aria-current={isActive ? "true" : undefined}
                aria-label={`${doc.name}, ${doc.fileType.toUpperCase()}, ${counts.fail} issues, ${counts.warn} warnings, ${counts.pass} passes`}
              >
                <div className="document-card-header">
                  <span className="doc-icon">
                    {doc.fileType === "pdf" ? "📄" : "🖼️"}
                  </span>
                  <span className="doc-name" title={doc.name}>
                    {doc.name}
                  </span>
                </div>

                <div className="document-card-meta">
                  <span className="doc-type-badge">{doc.fileType.toUpperCase()}</span>
                  <span className="doc-size">{formatBytes(doc.size)}</span>
                </div>

                {(counts.fail > 0 || counts.warn > 0 || counts.pass > 0) && (
                  <div className="document-finding-indicators">
                    {counts.fail > 0 && (
                      <span className="badge badge-fail" title={`${counts.fail} issue(s)`}>
                        ❌ {counts.fail} FAIL
                      </span>
                    )}
                    {counts.warn > 0 && (
                      <span className="badge badge-warn" title={`${counts.warn} warning(s)`}>
                        ⚠️ {counts.warn} WARN
                      </span>
                    )}
                    {counts.pass > 0 && (
                      <span className="badge badge-pass" title={`${counts.pass} passed`}>
                        ✅ {counts.pass} PASS
                      </span>
                    )}
                  </div>
                )}
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
};
