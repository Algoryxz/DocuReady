# DocuReady — Mobile Web MVP Run & Testing Guide

**Version:** 1.0.0  
**Authority:** Deeptiman (Product Owner & Architecture Lead)  
**Track:** Track B — Mobile Web MVP  
**Branch:** `feature/mobile-web-mvp`  
**Date:** 2026-11-15  

---

## 1. Executive Summary

DocuReady Mobile Web MVP delivers a fully responsive, touch-friendly mobile browser experience for citizen welfare applicants, field workers, and Common Service Centre (CSC) operators. 

The application runs locally on the host machine and serves an optimized mobile web interface accessible from smartphones and tablets connected to the same local Wi-Fi or local area network (LAN).

---

## 2. Privacy & Architecture Disclosures

> [!IMPORTANT]
> **Host Processing Disclosure:** Document ingestion, vector extraction, OCR processing, and statutory cross-verification execute **entirely on the host PC**. The mobile device acts strictly as a lightweight presentation and upload client over the local Wi-Fi network. No processing occurs on phone hardware, and **zero document data or telemetry leaves the local LAN**.

1. **Local-Only Boundary:** The server binds strictly to the host machine's local network interface (`0.0.0.0:8501`) over trusted Wi-Fi. Outbound internet connectivity is never required or initiated.
2. **Ephemeral File Lifecycles:** Files uploaded from mobile devices (via camera or photo library) are processed inside isolated, secure temporary directories (`tempfile.mkdtemp`) with restricted permissions and purged from disk immediately upon completion.
3. **Synthetic Demonstration Corpus:** For testing and demonstration, use the preloaded synthetic test packets (`pkt_01_clean` through `pkt_08_ambiguous_evidence`). Do NOT upload live citizen identification or Aadhaar cards.

---

## 3. Step-by-Step Setup & LAN Connection

### Step 1: Identify Host IP Address

On the host machine running DocuReady:

- **Windows:**
  ```powershell
  ipconfig
  ```
  Locate your active Wi-Fi or Ethernet adapter and note the **IPv4 Address** (e.g. `192.168.1.15`).

- **Linux:**
  ```bash
  hostname -I
  # or: ip addr show
  ```

- **macOS:**
  ```bash
  ipconfig getifaddr en0
  ```

### Step 2: Start the LAN-Accessible Streamlit Server

From the repository root (`DocuReady-canonical`), execute:

```bash
# Activate your virtual environment
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# Launch Streamlit bound to all local network interfaces
streamlit run src/docuready/interfaces/ui/app.py --server.address=0.0.0.0 --server.port=8501
```

Streamlit will display the Network URL:
```text
  Local URL:   http://localhost:8501
  Network URL: http://192.168.1.15:8501
```

### Step 3: Connect from Mobile Device

1. Connect your smartphone or tablet to the **same Wi-Fi network** as the host PC.
2. Open Chrome, Safari, or Firefox on the phone.
3. Navigate to: `http://<HOST-IP>:8501` (e.g. `http://192.168.1.15:8501`).

### Step 4: Teardown & Stopping Server

When testing is complete:
1. In the host terminal running Streamlit, press `Ctrl+C` to terminate the server.
2. Verify the server process has exited. Do not leave the LAN server running unattended on untrusted networks.

---

## 4. Mobile UX & Responsive Feature Matrix

| Feature | Desktop Implementation | Mobile Web Adaptation ($\le 768\text{px}$) | Design Standard |
| :--- | :--- | :--- | :--- |
| **Grid Layout** | Multi-column grid (3–4 columns) | Vertically stacked single column (`flex: 1 1 100%`) | Mobile-first responsiveness |
| **Touch Targets** | Standard desktop cursor targets | Min $44 \times 44\text{px}$ touch targets for all buttons/inputs | WCAG 2.5.5 / 2.5.8 |
| **Readiness Banner** | Inline metric card | Top sticky status bar showing score and pre-check status | Viewport persistence |
| **Table Display** | Wide full-width tables | Horizontal-scrollable containers (`overflow-x: auto`) | Zero horizontal page clipping |
| **Findings & Citations** | Standard cards with expanders | Collapsible accordions with touch-friendly toggles | Avoid endless vertical scroll |
| **Document Upload** | Drag-and-drop file upload | Native mobile file picker (supports camera capture & photo library) | Mobile OS input standards |
| **In-Memory Remediation**| Interactive document replacement | Single-touch synthetic re-audit with instant feedback | Sub-second recalculation |

---

## 5. Supported Mobile Viewport Profiles

The Mobile Web MVP is verified across the following standard viewport dimensions:

1. **360 × 800 px:** Budget Android devices (e.g., Samsung Galaxy A-series, Redmi).
2. **390 × 844 px:** Standard iOS devices (iPhone 12 / 13 / 14 / 15).
3. **430 × 932 px:** Flagship large-screen devices (iPhone 14/15 Pro Max, Galaxy S23/S24 Ultra).
4. **Desktop / Tablet ($\ge 1024\text{px}$):** Preserves full multi-column dashboard layout without regressions.

---

## 6. End-to-End Mobile Testing Workflow (Synthetic Packets)

1. **Open Navigation:** Tap the hamburger menu in the top left to expand navigation.
2. **Select Upload Documents (Screen 2):**
   - Tap **Choose Synthetic Test Case** dropdown.
   - Select `PKT_02_NAME_CONFLICT` (demonstrates marksheet name spelling variation).
   - Tap **Load & Audit Selected Packet** (touch target $\ge 44\text{px}$).
3. **Inspect Audit Findings (Screen 5):**
   - View top sticky score banner showing the penalized readiness score.
   - Scroll through vertically stacked finding cards.
   - Tap **View Original Evidence** accordion to inspect bounding box snippets.
4. **Remediate Document (Screen 6):**
   - Select `MARKSHEET` to remediate.
   - Choose **Auto-Generate Standard Corrected Version**.
   - Tap **Generate & Re-Run Audit**.
   - Verify score instantaneously restores to **100/100 (READY TO SUBMIT)**.
