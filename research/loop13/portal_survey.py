"""
India Data Portals Investigation Script
DocuReady - Research Loop 13
Actively inspects the four mandatory Indian government and public data portals:
1. Portal A: data.gov.in
2. Portal B: NDAP (ndap.niti.gov.in)
3. Portal C: Microdata/NADA (microdata.gov.in/NADA)
4. Portal D: India Data Portal (indiadataportal.com)
"""

import json
import ssl
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_FILE = REPO_ROOT / "research" / "loop13" / "portal_survey_results.json"

PORTALS = [
    {
        "id": "PORTAL_A_DATA_GOV_IN",
        "name": "Open Government Data (OGD) Platform India",
        "base_url": "https://www.data.gov.in/",
        "search_url": "https://www.data.gov.in/search/site?keys={query}",
        "queries": ["scholarship", "gazette", "annual report"],
        "notes": "Primary repository of published datasets and administrative reports."
    },
    {
        "id": "PORTAL_B_NDAP",
        "name": "National Data & Analytics Platform (NITI Aayog)",
        "base_url": "https://ndap.niti.gov.in/",
        "search_url": "https://ndap.niti.gov.in/search?query={query}",
        "queries": ["education", "district", "welfare"],
        "notes": "Standardized cross-sectoral datasets and linked source publications."
    },
    {
        "id": "PORTAL_C_MICRODATA_NADA",
        "name": "National Data Archive (NADA) / MoSPI Microdata",
        "base_url": "https://microdata.gov.in/NADA/index.php/home",
        "search_url": "https://microdata.gov.in/NADA/index.php/catalog?query={query}",
        "queries": ["NSS", "schedule", "questionnaire", "manual"],
        "notes": "Survey questionnaires, survey schedules, field manuals, and codebooks."
    },
    {
        "id": "PORTAL_D_INDIA_DATA_PORTAL",
        "name": "India Data Portal (Bharti Institute / ISB)",
        "base_url": "https://indiadataportal.com/",
        "search_url": "https://indiadataportal.com/search?keyword={query}",
        "queries": ["agriculture", "rural development", "income"],
        "notes": "Socio-economic data publications, policy briefs, and district statistics."
    }
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

ctx = ssl.create_default_context()
# Note: Some government portal SSL chains may have local cert trust quirks on Windows
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

results = []

for p in PORTALS:
    print(f"\nProbing {p['name']} ({p['base_url']})...")
    portal_entry = {
        "id": p["id"],
        "name": p["name"],
        "base_url": p["base_url"],
        "accessible": False,
        "status_code": None,
        "latency_ms": None,
        "ssl_handshake": None,
        "search_tested": False,
        "queries_tested": [],
        "document_types_found": [],
        "usefulness_assessment": "",
        "detailed_observations": ""
    }

    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(p["base_url"], headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
            status = response.getcode()
            content = response.read(65536).decode("utf-8", errors="ignore")
            elapsed = (time.perf_counter() - t0) * 1000.0
            portal_entry["accessible"] = (status == 200)
            portal_entry["status_code"] = status
            portal_entry["latency_ms"] = round(elapsed, 1)
            portal_entry["ssl_handshake"] = "SUCCESS"
            print(f"  -> Base URL accessible: Status {status} in {elapsed:.1f}ms")

            # Test search query
            q = p["queries"][0]
            search_u = p["search_url"].format(query=urllib.parse.quote(q))
            print(f"  -> Testing search query '{q}' at {search_u}...")
            s_req = urllib.request.Request(search_u, headers=headers)
            try:
                with urllib.request.urlopen(s_req, timeout=15, context=ctx) as s_resp:
                    s_status = s_resp.getcode()
                    portal_entry["search_tested"] = True
                    portal_entry["queries_tested"].append({
                        "query": q,
                        "status": s_status,
                        "url": search_u
                    })
                    print(f"  -> Search query returned HTTP {s_status}")
            except Exception as e_s:
                portal_entry["queries_tested"].append({
                    "query": q,
                    "error": str(e_s),
                    "url": search_u
                })
                print(f"  -> Search query failed: {e_s}")

    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        portal_entry["accessible"] = False
        portal_entry["error"] = str(e)
        portal_entry["latency_ms"] = round(elapsed, 1)
        portal_entry["ssl_handshake"] = "FAILED" if "SSL" in str(e) else "TIMEOUT_OR_BLOCKED"
        print(f"  -> Connection failed: {e}")

    results.append(portal_entry)

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUT_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(f"\nSaved portal survey results to {OUT_FILE}")
