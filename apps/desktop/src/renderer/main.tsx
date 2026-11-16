import React from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

function App(): React.JSX.Element {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">D</div>
          <div>
            <strong>DocuReady</strong>
            <span>DOCUMENT READINESS</span>
          </div>
        </div>

        <nav aria-label="Primary navigation">
          <button className="nav-item active" type="button">Overview</button>
          <button className="nav-item" type="button" disabled>New audit</button>
          <button className="nav-item" type="button" disabled>Recent audits</button>
        </nav>

        <div className="sidebar-footer">
          <span className="privacy-dot" />
          <div>
            <strong>Local workspace</strong>
            <span>Files stay on this device</span>
          </div>
        </div>
      </aside>

      <section className="main-panel">
        <header className="topbar">
          <span>WORKSPACE / OVERVIEW</span>
          <span className="version">DESKTOP PREVIEW · v{window.docureadyDesktop.version}</span>
        </header>

        <div className="content">
          <div className="eyebrow">DOCUMENT PREPARATION</div>
          <h1>Check your documents<br />before you submit.</h1>
          <p className="intro">
            Review a document packet for missing files, inconsistencies, and
            evidence that needs a closer look. Your documents are processed locally.
          </p>

          <section className="start-card" aria-labelledby="start-title">
            <div className="card-icon">+</div>
            <div className="card-copy">
              <h2 id="start-title">Start a new audit</h2>
              <p>Choose a scheme and add the documents you want to check.</p>
            </div>
            <span className="coming-soon">ENGINE CONNECTION IN PROGRESS</span>
          </section>

          <div className="notice">
            <strong>Advisory tool only</strong>
            <p>
              DocuReady checks the supplied evidence against configured rules.
              It does not determine eligibility or guarantee acceptance by any
              government scheme or portal.
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
