# DOCUREADY — COMPETITION SETUP & OPERATIONAL CHECKLIST

**Project:** DocuReady  
**Event:** HackNation 2026 Arena Demonstration  
**Platform:** Windows 10/11 x64  
**Release Version:** 0.1.0 (Loop 10 Qualified)  

---

## 1. PRE-DEMO ENVIRONMENT VERIFICATION (30 MINUTES PRIOR)

- [ ] **Hardware & Display:**
  - Connect laptop to competition projector or external monitor.
  - Set display resolution to standard **1920x1080 (1080p)** or **2560x1440 (1440p)**.
  - Set Windows display scaling to **100%** or **125%** (avoid 175%+ to prevent layout clipping).
  - Test external audio/microphone if recording or presenting with headset.

- [ ] **Offline Assurance & Airplane Mode:**
  - Turn **Wi-Fi OFF** or enable **Airplane Mode**.
  - Open terminal and confirm zero external internet connectivity:
    `ping 8.8.8.8` (must fail / unreachable).
  - Verify DocuReady executes and audits completely offline.

- [ ] **Clean Runtime Staging:**
  - Close background development IDEs (VS Code, heavy browser tabs) to maximize available CPU/RAM.
  - Confirm the packaged app folder `DocuReady-win32-x64` is located on the desktop or fast SSD.
  - Verify bundled Tesseract OCR directory contains trained models:
    `resources/docuready_sidecar/tesseract/tessdata/` (`eng.traineddata`, `hin.traineddata`, `ori.traineddata`, `osd.traineddata`).

- [ ] **Demo Fixtures Staging:**
  - Verify synthetic demo packets are organized and accessible in a dedicated desktop folder (e.g., `Desktop\Demo_Packets\`):
    - `01_Clean_Applicant/` (`pkt_01_clean`)
    - `02_Name_Mismatch_Conflict/` (`pkt_02_name_conflict`)
    - `03_Missing_Certificate/` (`pkt_05_missing_certificate`)
    - `04_Ambiguous_Evidence/` (`pkt_08_ambiguous_evidence`)
    - `05_Degraded_Scan_Abstention/` (`pkt_07_unreadable_doc`)

---

## 2. LAUNCH & SMOKE TEST (10 MINUTES PRIOR)

- [ ] Double-click `DocuReady.exe` to launch.
- [ ] Observe splash / initial load (< 2.0s cold start).
- [ ] Verify sidecar status indicator displays **Connected (PID: xxxx)** in green.
- [ ] Run a quick smoke test using `pkt_01_clean`:
  - Drag and drop documents.
  - Click **Start Audit**.
  - Confirm audit finishes in ~1.7s with **100 Readiness Score** and **NO_ISSUES_FOUND**.
- [ ] Click **Clear Session / New Applicant** to reset UI to clean state.

---

## 3. PRESENTATION FLOW & TIMING BUDGET (5-MINUTE DEMO)

| Time | Segment | Demonstration Action | Key Judge Takeaway |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:30** | The Problem | Explain scholarship application rejections due to clerical errors, 40-day review backlogs, and portal lockouts. | High social stakes & administrative burden. |
| **0:30 - 1:00** | DocuReady Intro | Point out offline badge, zero-cloud architecture, and privacy compliance. | Complete institutional data privacy; works in remote centers. |
| **1:00 - 2:00** | Clean Packet | Load `01_Clean_Applicant`. Audit runs in ~1.7s. 100/100 score. Click findings to view evidence boxes. | Fast, fully automated green-path verification. |
| **2:00 - 3:15** | Fatal Mismatch | Load `02_Name_Mismatch_Conflict`. Instant red alert (Score 75). Show side-by-side evidence on Marksheet vs Application Form. Highlight blocked submit button. | Proactive defect prevention before portal lockouts. |
| **3:15 - 4:15** | Missing & Ambiguous | Load `03_Missing_Certificate` (clean missing doc notice without fake boxes) and `04_Ambiguous_Evidence` (yellow review prompt). | Calibrated human-in-the-loop: assists without hallucinating. |
| **4:15 - 5:00** | Resilience & Trust | Showcase unreadable doc conservative abstention and session purge. | AI safety, zero hallucination, verifiable trust. |
| **5:00 - 5:30** | Q&A & Wrap-up | Answer judges' technical questions regarding OCR latency, accuracy, and deployment. | Enterprise readiness & immediate deployability. |

---

## 4. CONTINGENCY & GLITCH RECOVERY PLAYBOOK

- **Accidental Wrong File Selected:**
  - Click the remove icon on the file card, or click **Clear Session** and re-select the packet.
- **Audit Process Slowdown / System Pause:**
  - Click **Cancel Audit**; the desktop will immediately terminate the child task and return to IDLE in < 1.8s. Click **Start Audit** again.
- **Application Window Accidentally Closed:**
  - Double-click `DocuReady.exe` from desktop shortcut. Cold start is ~1.1s. Staging workspace is clean.
- **Judge Requests to See Installer / Clean Machine Deploy:**
  - Point to `DocuReady-0.1.0-Setup.exe` (Squirrel.Windows single-click installer) and `DocuReady-win32-x64-0.1.0.zip` (portable zero-install build).
