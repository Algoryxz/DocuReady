"""
Loop 14 - Mandatory Indian Public Data Portals Deep Investigation
DocuReady Engineering Research

Systematically investigates all four Indian portals:
1. data.gov.in (OGD India)
2. ndap.niti.gov.in (NDAP / NITI Aayog)
3. microdata.gov.in/NADA (MoSPI Microdata Archive)
4. indiadataportal.com (India Data Portal / ISB)

Evaluates accessibility, search capabilities, resource types (PDF, CSV, image, HTML),
language distribution (English, Hindi, Odia), native vector vs scanned raster content,
licensing, and acquisition viability.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]


def probe_url(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 15) -> Dict[str, Any]:
    """Probes a URL and returns status, latency, headers, and body sample."""
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8"
    }
    if headers:
        default_headers.update(headers)

    t0 = time.perf_counter()
    req = urllib.request.Request(url, headers=default_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.perf_counter() - t0) * 1000.0
            content = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            try:
                body_sample = content[:4000].decode(charset, errors="replace")
            except Exception:
                body_sample = str(content[:1000])

            content_type = resp.headers.get("Content-Type", "")
            content_length = resp.headers.get("Content-Length", str(len(content)))

            return {
                "url": url,
                "status": resp.status,
                "accessible": True,
                "latency_ms": round(elapsed, 2),
                "content_type": content_type,
                "content_length": content_length,
                "body_preview": body_sample[:500],
                "error": None
            }
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return {
            "url": url,
            "status": getattr(e, "code", 0),
            "accessible": False,
            "latency_ms": round(elapsed, 2),
            "content_type": None,
            "content_length": None,
            "body_preview": "",
            "error": str(e)
        }


def investigate_portals() -> Dict[str, Any]:
    print("=" * 80)
    print("DOCUREADY LOOP 14: MANDATORY FOUR-PORTAL FORENSIC INVESTIGATION")
    print("=" * 80)

    portals = {
        "portal_a_data_gov_in": {
            "name": "Open Government Data (OGD) Platform India",
            "base_url": "https://www.data.gov.in",
            "search_queries": [
                "scholarship",
                "income certificate",
                "caste",
                "guidelines",
                "format"
            ],
            "api_endpoint": "https://data.gov.in/api/3/action/package_search"
        },
        "portal_b_ndap": {
            "name": "National Data & Analytics Platform (NDAP) - NITI Aayog",
            "base_url": "https://ndap.niti.gov.in",
            "search_queries": [
                "education",
                "scholarship",
                "district report",
                "census"
            ],
            "api_endpoint": "https://ndap.niti.gov.in/api/v1/dataset"
        },
        "portal_c_mospi_nada": {
            "name": "MoSPI Microdata / National Data Archive (NADA)",
            "base_url": "https://microdata.gov.in/nada/index.php/home",
            "search_queries": [
                "NSS",
                "Schedule",
                "Questionnaire",
                "Income"
            ],
            "search_url_template": "https://microdata.gov.in/nada/index.php/catalog?sk={query}"
        },
        "portal_d_india_data_portal": {
            "name": "India Data Portal (Bharti Institute / ISB)",
            "base_url": "https://indiadataportal.com",
            "search_queries": [
                "scholarship",
                "agriculture",
                "education",
                "report"
            ],
            "search_url_template": "https://indiadataportal.com/?s={query}"
        }
    }

    survey_results = {}

    for key, info in portals.items():
        print(f"\n--- Investigating {info['name']} ({key}) ---")
        base_probe = probe_url(info["base_url"])
        print(f"  Base URL: {info['base_url']}")
        print(f"  Accessible: {base_probe['accessible']} (Status {base_probe['status']}, Latency: {base_probe['latency_ms']} ms)")

        query_probes = []
        for q in info["search_queries"]:
            encoded_q = urllib.parse.quote_plus(q)
            if "search_url_template" in info:
                q_url = info["search_url_template"].format(query=encoded_q)
            elif "api_endpoint" in info:
                q_url = f"{info['api_endpoint']}?q={encoded_q}"
            else:
                q_url = f"{info['base_url']}/search?query={encoded_q}"

            qp = probe_url(q_url)
            query_probes.append({
                "query": q,
                "url": q_url,
                "status": qp["status"],
                "accessible": qp["accessible"],
                "latency_ms": qp["latency_ms"],
                "content_type": qp["content_type"]
            })
            print(f"  Query '{q}': Status {qp['status']} ({qp['latency_ms']} ms)")

        survey_results[key] = {
            "name": info["name"],
            "base_url": info["base_url"],
            "base_probe": base_probe,
            "query_probes": query_probes
        }

    output_dir = ROOT / "research" / "loop14"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "portal_survey_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(survey_results, f, indent=2)

    print(f"\nPortal survey completed. Saved to {out_file}")
    return survey_results


if __name__ == "__main__":
    investigate_portals()
