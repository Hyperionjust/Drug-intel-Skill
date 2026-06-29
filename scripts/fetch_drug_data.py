#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_drug_data.py  --  deterministic-source collector for the `drug-intel` skill.

Usage:
    python scripts/fetch_drug_data.py "<drug name or code>"
    python scripts/fetch_drug_data.py "Osimertinib" --max-studies 200
    python scripts/fetch_drug_data.py "AZD9291" --compact

What it does
------------
Hits ONLY the sources that have a clean, deterministic public API and merges
them into a single JSON document printed to stdout:

    * PubChem PUG-REST .......... name -> CID, formula, SMILES, IUPAC, synonyms, structure PNG url
    * ChEMBL REST ............... molecule search (chembl_id, pref_name, max_phase) + mechanism_of_action
    * ClinicalTrials.gov v2 ..... trials by intervention -> phases / status / country / dates / sponsor,
                                  with US & China highest-phase + counts + recent events computed
    * openFDA ................... drugsfda + ndc -> approval, sponsors, ANDA(generic) signal

Design rules (match SKILL.md)
-----------------------------
  * stdlib only (urllib) -- no pip required.
  * A source that fails OR finds nothing returns null; it is NEVER treated as
    "the drug does not exist". Every null is explained in `source_status`.
  * The dirty / API-less regions (chinadrugtrials.org.cn, Orange/Purple Book LOE,
    China patents & generics) are returned as null placeholders WITH the URL to
    check by hand -- the script does not try to scrape them. SKILL.md routes
    those through web + human review.
  * Nothing here ever raises out of a single source; the process always prints
    valid JSON and exits 0 unless the CLI itself is misused.

This script gathers the *deterministic* slice only. The badges, the China side,
LOE reasoning, sales numbers and the AI comparison all live in SKILL.md and are
the human/-web part of the workflow.
"""

import re
import sys
import json
import time
import argparse
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone

# Force UTF-8 stdout so Chinese notes / IUPAC names never blow up on a Windows console.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

USER_AGENT = "drug-intel/1.0 (R&D competitive-intelligence; contact: research)"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_STUDIES = 200


# --------------------------------------------------------------------------- #
# Low-level HTTP helper                                                        #
# --------------------------------------------------------------------------- #
def http_get_json(url, timeout=DEFAULT_TIMEOUT, retries=1):
    """
    GET a URL and parse JSON.

    Returns (data, status) where status is one of:
        "ok"                 -> data is the parsed JSON
        "no_data"            -> HTTP 404 (a valid "nothing found" for these APIs)
        "error: <detail>"    -> anything else; data is None

    Never raises.
    """
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                       "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
            return json.loads(raw), "ok"
        except HTTPError as e:
            # openFDA & PubChem answer "nothing matched" with 404 -- that is data, not an error.
            if e.code == 404:
                return None, "no_data"
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:160]
            except Exception:
                pass
            last_err = "error: HTTP {} {}".format(e.code, body).strip()
            if e.code >= 500 and attempt < retries:
                time.sleep(1.0)
                continue
            return None, last_err
        except (URLError, TimeoutError) as e:
            last_err = "error: {}: {}".format(type(e).__name__, e)
            if attempt < retries:
                time.sleep(1.0)
                continue
            return None, last_err
        except (ValueError, json.JSONDecodeError) as e:
            return None, "error: bad JSON: {}".format(e)
    return None, last_err or "error: unknown"


def _q(params):
    """urlencode that keeps API query operators readable."""
    return urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


# --------------------------------------------------------------------------- #
# PubChem                                                                      #
# --------------------------------------------------------------------------- #
PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def fetch_pubchem(name, status_sink):
    """name -> CID, molecular formula, SMILES, IUPAC name, synonyms, structure PNG url."""
    cids_url = "{}/compound/name/{}/cids/JSON".format(PUBCHEM, urllib.parse.quote(name))
    data, st = http_get_json(cids_url)
    if st != "ok" or not data:
        status_sink["pubchem"] = "no_data" if st == "no_data" else st
        return None
    cids = (data.get("IdentifierList") or {}).get("CID") or []
    if not cids:
        status_sink["pubchem"] = "no_data"
        return None
    cid = cids[0]

    out = {
        "cid": cid,
        "all_cids": cids[:5],
        "molecular_formula": None,
        "smiles": None,
        "iupac_name": None,
        "synonyms": [],
        "structure_png_url": "{}/compound/cid/{}/PNG".format(PUBCHEM, cid),
        "pubchem_url": "https://pubchem.ncbi.nlm.nih.gov/compound/{}".format(cid),
    }

    # Properties. PubChem renamed CanonicalSMILES -> ConnectivitySMILES/SMILES, so try a
    # couple of property strings and then grab whatever *SMILES* key comes back.
    props = None
    for prop_str in ("MolecularFormula,SMILES,IUPACName",
                     "MolecularFormula,ConnectivitySMILES,IUPACName",
                     "MolecularFormula,CanonicalSMILES,IUPACName"):
        purl = "{}/compound/cid/{}/property/{}/JSON".format(PUBCHEM, cid, prop_str)
        pdata, pst = http_get_json(purl)
        if pst == "ok" and pdata:
            try:
                props = pdata["PropertyTable"]["Properties"][0]
                break
            except (KeyError, IndexError):
                continue
    if props:
        out["molecular_formula"] = props.get("MolecularFormula")
        out["iupac_name"] = props.get("IUPACName")
        for k, v in props.items():
            if "SMILES" in k and v:
                out["smiles"] = v
                out["smiles_field"] = k
                break

    # Synonyms (INN, brand names, research codes, salt forms) -- the disambiguation fuel.
    syn_url = "{}/compound/cid/{}/synonyms/JSON".format(PUBCHEM, cid)
    sdata, sst = http_get_json(syn_url)
    if sst == "ok" and sdata:
        try:
            syns = sdata["InformationList"]["Information"][0].get("Synonym", []) or []
            out["synonyms"] = syns[:20]
        except (KeyError, IndexError):
            pass

    status_sink["pubchem"] = "ok"
    return out


# --------------------------------------------------------------------------- #
# ChEMBL                                                                       #
# --------------------------------------------------------------------------- #
CHEMBL = "https://www.ebi.ac.uk/chembl/api/data"


def fetch_chembl(name, status_sink):
    """molecule search + mechanism_of_action. Mechanisms can live on the parent OR the salt."""
    surl = "{}/molecule/search.json?{}".format(CHEMBL, _q({"q": name, "limit": 10}))
    data, st = http_get_json(surl)
    if st != "ok" or not data:
        status_sink["chembl"] = "no_data" if st == "no_data" else st
        return None
    mols = data.get("molecules") or []
    if not mols:
        status_sink["chembl"] = "no_data"
        return None

    molecules = []
    for m in mols[:10]:
        molecules.append({
            "molecule_chembl_id": m.get("molecule_chembl_id"),
            "pref_name": m.get("pref_name"),
            "max_phase": m.get("max_phase"),
            "molecule_type": m.get("molecule_type"),
            "first_approval": m.get("first_approval"),
            "structure_type": m.get("structure_type"),
            "synonyms": [s.get("molecule_synonym")
                         for s in (m.get("molecule_synonyms") or [])][:8],
        })

    # Query mechanism for the most relevant candidates (named ones, up to 4) and dedupe.
    mech_ids = [m["molecule_chembl_id"] for m in molecules
                if m["molecule_chembl_id"] and (m["pref_name"] or m["max_phase"])][:4]
    mechanisms = []
    seen = set()
    for cid in mech_ids:
        murl = "{}/mechanism.json?{}".format(CHEMBL, _q({"molecule_chembl_id": cid}))
        mdata, mst = http_get_json(murl)
        if mst != "ok" or not mdata:
            continue
        for mech in mdata.get("mechanisms", []) or []:
            key = (mech.get("mechanism_of_action"), mech.get("target_chembl_id"),
                   mech.get("action_type"))
            if key in seen:
                continue
            seen.add(key)
            mechanisms.append({
                "mechanism_of_action": mech.get("mechanism_of_action"),
                "action_type": mech.get("action_type"),
                "target_chembl_id": mech.get("target_chembl_id"),
                "max_phase": mech.get("max_phase"),
                "molecule_chembl_id": mech.get("molecule_chembl_id"),
                "mechanism_refs": [r.get("ref_url") for r in (mech.get("mechanism_refs") or [])][:3],
            })

    # best_match: prefer a NAMED molecule with the highest max_phase. A bare search-rank
    # #1 is unreliable for research codes (returns structure-similar fuzzy hits first).
    def _phase_num(m):
        try:
            return float(m.get("max_phase") or 0)
        except (TypeError, ValueError):
            return 0.0
    named = [m for m in molecules if m.get("pref_name")]
    best = max(named, key=_phase_num) if named else (molecules[0] if molecules else None)

    status_sink["chembl"] = "ok"
    return {
        "molecules": molecules,
        "best_match": best,
        "mechanisms": mechanisms,
    }


# --------------------------------------------------------------------------- #
# ClinicalTrials.gov v2                                                        #
# --------------------------------------------------------------------------- #
CTGOV = "https://clinicaltrials.gov/api/v2/studies"

PHASE_RANK = {
    "EARLY_PHASE1": 0.5,
    "PHASE1": 1.0,
    "PHASE2": 2.0,
    "PHASE3": 3.0,
    "PHASE4": 4.0,
    "NA": 0.0,
}
RANK_LABEL = {0.5: "EARLY_PHASE1", 1.0: "PHASE1", 2.0: "PHASE2",
              3.0: "PHASE3", 4.0: "PHASE4", 0.0: "NA/Not Applicable"}


def _phase_rank(phases):
    if not phases:
        return 0.0
    return max(PHASE_RANK.get(p, 0.0) for p in phases)


def _dig(d, *path):
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def fetch_clinicaltrials(name, status_sink, max_studies=DEFAULT_MAX_STUDIES):
    """Pull trials by intervention, then compute US/China highest-phase, counts, recent events."""
    studies = []
    total = None
    token = None
    page_size = 100
    while len(studies) < max_studies:
        params = {"query.intr": name, "pageSize": page_size, "countTotal": "true"}
        if token:
            params["pageToken"] = token
        url = "{}?{}".format(CTGOV, _q(params))
        data, st = http_get_json(url, timeout=45)
        if st != "ok" or not data:
            if not studies:   # nothing fetched at all
                status_sink["clinicaltrials_gov"] = "no_data" if st == "no_data" else st
                return None
            break
        if total is None:
            total = data.get("totalCount")
        studies.extend(data.get("studies", []) or [])
        token = data.get("nextPageToken")
        if not token:
            break

    if not studies:
        status_sink["clinicaltrials_gov"] = "no_data"
        return None
    studies = studies[:max_studies]   # honor the cap exactly (pages overshoot in 100s)

    parsed = []
    for s in studies:
        ps = s.get("protocolSection", {}) or {}
        phases = _dig(ps, "designModule", "phases") or []
        countries = sorted({l.get("country") for l in
                            (_dig(ps, "contactsLocationsModule", "locations") or [])
                            if l.get("country")})
        parsed.append({
            "nctId": _dig(ps, "identificationModule", "nctId"),
            "briefTitle": _dig(ps, "identificationModule", "briefTitle"),
            "phases": phases,
            "phase_rank": _phase_rank(phases),
            "overallStatus": _dig(ps, "statusModule", "overallStatus"),
            "startDate": _dig(ps, "statusModule", "startDateStruct", "date"),
            "primaryCompletionDate": _dig(ps, "statusModule", "primaryCompletionDateStruct", "date"),
            "completionDate": _dig(ps, "statusModule", "completionDateStruct", "date"),
            "leadSponsor": _dig(ps, "sponsorCollaboratorsModule", "leadSponsor", "name"),
            "conditions": _dig(ps, "conditionsModule", "conditions") or [],
            "countries": countries,
        })

    def country_summary(tag):
        subset = [p for p in parsed if tag in p["countries"]]
        if not subset:
            return {"trial_count": 0, "highest_phase": None}
        top = max(p["phase_rank"] for p in subset)
        return {
            "trial_count": len(subset),
            "highest_phase": RANK_LABEL.get(top, "rank {}".format(top)),
            "highest_phase_rank": top,
        }

    # phase distribution (by each study's top phase)
    dist = {}
    for p in parsed:
        lbl = RANK_LABEL.get(p["phase_rank"], "rank {}".format(p["phase_rank"]))
        dist[lbl] = dist.get(lbl, 0) + 1

    recent = sorted([p for p in parsed if p["startDate"]],
                    key=lambda p: p["startDate"], reverse=True)[:8]

    status_count = {}
    for p in parsed:
        s = p["overallStatus"] or "UNKNOWN"
        status_count[s] = status_count.get(s, 0) + 1

    status_sink["clinicaltrials_gov"] = "ok"
    return {
        "total_matching": total,
        "fetched": len(parsed),
        "note": ("Stats below are computed over the {} fetched studies (of {} total). "
                 "Increase --max-studies for fuller coverage.".format(len(parsed), total)),
        "overall_highest_phase": RANK_LABEL.get(max((p["phase_rank"] for p in parsed), default=0.0)),
        "us": country_summary("United States"),
        "china": country_summary("China"),
        "phase_distribution": dist,
        "status_distribution": status_count,
        "recent_trials": recent,
        "studies": parsed,
    }


# --------------------------------------------------------------------------- #
# openFDA                                                                      #
# --------------------------------------------------------------------------- #
OPENFDA_DRUGSFDA = "https://api.fda.gov/drug/drugsfda.json"
OPENFDA_NDC = "https://api.fda.gov/drug/ndc.json"


def _app_type(app_no):
    if not app_no:
        return "UNKNOWN"
    for t in ("ANDA", "NDA", "BLA"):
        if app_no.upper().startswith(t):
            return t
    return "OTHER"


def fetch_openfda(name, status_sink):
    """Approval / sponsors / ANDA(generic) signal from drugsfda + ndc."""
    out = {"drugsfda": None, "ndc": None}
    any_ok = False

    # ---- drugsfda ----
    durl = "{}?{}".format(OPENFDA_DRUGSFDA,
                          _q({"search": 'openfda.generic_name:"{}"'.format(name), "limit": 50}))
    data, st = http_get_json(durl)
    if st == "ok" and data and data.get("results"):
        apps = []
        all_ap_dates = []
        for res in data["results"]:
            app_no = res.get("application_number")
            ap_dates = [su.get("submission_status_date") for su in (res.get("submissions") or [])
                        if su.get("submission_status") == "AP" and su.get("submission_status_date")]
            all_ap_dates.extend(ap_dates)
            brand = sorted({p.get("brand_name") for p in (res.get("products") or []) if p.get("brand_name")})
            mstat = sorted({p.get("marketing_status") for p in (res.get("products") or []) if p.get("marketing_status")})
            apps.append({
                "application_number": app_no,
                "type": _app_type(app_no),
                "sponsor_name": res.get("sponsor_name"),
                "brand_names": brand,
                "marketing_statuses": mstat,
                "earliest_approval": min(ap_dates) if ap_dates else None,
            })
        has_anda = any(a["type"] == "ANDA" for a in apps)
        out["drugsfda"] = {
            "total": _dig(data, "meta", "results", "total"),
            "applications": apps,
            "originators": sorted({a["sponsor_name"] for a in apps
                                   if a["type"] in ("NDA", "BLA") and a["sponsor_name"]}),
            "has_anda_generic": has_anda,
            "earliest_approval_year": (min(all_ap_dates)[:4] if all_ap_dates else None),
        }
        any_ok = True
    elif st not in ("ok", "no_data"):
        status_sink["openfda_drugsfda"] = st

    # ---- ndc (currently-marketed packaging; marketing_category = NDA / ANDA / ...) ----
    nurl = "{}?{}".format(OPENFDA_NDC,
                          _q({"search": 'generic_name:"{}"'.format(name), "limit": 100}))
    ndata, nst = http_get_json(nurl)
    if nst == "ok" and ndata and ndata.get("results"):
        cats, labelers = {}, set()
        for res in ndata["results"]:
            cat = res.get("marketing_category") or "UNKNOWN"
            cats[cat] = cats.get(cat, 0) + 1
            if res.get("labeler_name"):
                labelers.add(res["labeler_name"])
        out["ndc"] = {
            "total": _dig(ndata, "meta", "results", "total"),
            "marketing_categories": cats,
            "labelers": sorted(labelers)[:25],
            "has_anda_generic": cats.get("ANDA", 0) > 0,
        }
        any_ok = True
    elif nst not in ("ok", "no_data"):
        status_sink["openfda_ndc"] = nst

    if not any_ok:
        status_sink["openfda"] = "no_data"
        return None
    status_sink["openfda"] = "ok"
    return out


# --------------------------------------------------------------------------- #
# API-less regions: return null placeholders WITH where-to-look URLs           #
# --------------------------------------------------------------------------- #
def web_and_manual_placeholders():
    """
    These have no clean public API. The script intentionally does NOT scrape them;
    it returns null + the canonical URL so SKILL.md can route them through
    web fetch + human review (and badge them 🔍web / ❓N/A / 🔴).
    """
    return {
        "china_clinical_trials": {
            "data": None,
            "source": "https://www.chinadrugtrials.org.cn/index.html",
            "note": "CDE official registry. No public API, dynamic page -> fetch via web in SKILL.md; "
                    "badge 🔍web if retrieved, ❓N/A + manual link if not. High human-in-the-loop.",
        },
        "us_loe_orange_book": {
            "data": None,
            "source": "https://www.accessdata.fda.gov/scripts/cder/ob/",
            "note": "Small-molecule patents + exclusivity. No single 'LOE=date' field -> derive latest "
                    "patent/exclusivity expiry. Forced 🔴.",
        },
        "us_loe_purple_book": {
            "data": None,
            "source": "https://purplebooksearch.fda.gov/",
            "note": "Biologics exclusivity / reference-product info. Forced 🔴.",
        },
        "china_loe_patents": {
            "data": None,
            "source": "https://zldj.cnipa.gov.cn/  (中国上市药品专利信息登记平台)",
            "note": "No clean equivalent to Orange Book. Patent登记平台 / industry DB / news. Forced 🔴.",
        },
        "china_generics_nmpa": {
            "data": None,
            "source": "https://www.nmpa.gov.cn/  /  https://www.cde.org.cn/  (一致性评价 / 仿制批文)",
            "note": "Generic approvals & consistency-evaluation. No clean API -> web + manual. Forced 🔴.",
        },
    }


# --------------------------------------------------------------------------- #
# Orchestration                                                               #
# --------------------------------------------------------------------------- #
def collect(name, max_studies=DEFAULT_MAX_STUDIES):
    status = {}
    result = {
        "query": name,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0",
        "regions_scope": ["US", "China"],
        "deterministic_sources": {},
        "web_and_manual": web_and_manual_placeholders(),
        "source_status": status,
        "disclaimer": "R&D competitive-intelligence only. Not medical advice, not investment advice. "
                      "All high-hallucination fields must be badged & human-verified per SKILL.md.",
    }

    ds = result["deterministic_sources"]
    # Each call is independent and self-contained; one failure never stops the others.
    ds["pubchem"] = _safe(fetch_pubchem, name, status, key="pubchem")
    ds["chembl"] = _safe(fetch_chembl, name, status, key="chembl")
    ds["clinicaltrials_gov"] = _safe(fetch_clinicaltrials, name, status, key="clinicaltrials_gov",
                                     extra=(max_studies,))
    ds["openfda"] = _safe(fetch_openfda, name, status, key="openfda")

    # convenience identity roll-up for the disambiguation step
    result["identity_rollup"] = build_identity(name, ds)
    return result


def _safe(fn, name, status, key, extra=()):
    """Run a source fn; if it throws unexpectedly, record the error and return None."""
    try:
        return fn(name, status, *extra)
    except Exception as e:  # last-resort guard -- a source must never crash the run
        status[key] = "error: unhandled {}: {}".format(type(e).__name__, e)
        return None


_ATC_RE = re.compile(r"^[A-Z]\d{2}[A-Z]{2}\d{2}$")   # e.g. L01XE35
_UNII_RE = re.compile(r"^[A-Z0-9]{10}$")              # e.g. 3C06JJ0Z2O


def _looks_like_research_code(s):
    """AZD9291 / LY-3009120 style, excluding ATC / UNII / DB-accession noise."""
    if ":" in s or "/" in s:                 # CHEBI:..., RefChem:..., 2-Propenamide,...
        return False
    if _ATC_RE.match(s) or _UNII_RE.match(s):
        return False
    has_d = any(c.isdigit() for c in s)
    has_a = any(c.isalpha() for c in s)
    return has_d and has_a and len(s) <= 12


def build_identity(name, ds):
    ident = {"query": name, "resolved_names": [], "pubchem_cid": None,
             "chembl_ids": [], "research_codes": [], "brand_names": []}
    pc = ds.get("pubchem")
    if pc:
        ident["pubchem_cid"] = pc.get("cid")
        for s in pc.get("synonyms", []):
            if _looks_like_research_code(s):
                ident["research_codes"].append(s)
        ident["resolved_names"] = pc.get("synonyms", [])[:8]
    cb = ds.get("chembl")
    if cb:
        ident["chembl_ids"] = [m["molecule_chembl_id"] for m in cb.get("molecules", [])
                               if m.get("molecule_chembl_id")][:6]
    of = ds.get("openfda")
    if of and of.get("drugsfda"):
        brands = set()
        for a in of["drugsfda"].get("applications", []):
            brands.update(a.get("brand_names", []))
        ident["brand_names"] = sorted(brands)
    ident["research_codes"] = sorted(set(ident["research_codes"]))[:10]
    return ident


def main(argv):
    ap = argparse.ArgumentParser(
        description="Collect deterministic drug-intel from PubChem, ChEMBL, ClinicalTrials.gov, openFDA.")
    ap.add_argument("name", help="drug name, INN, brand, or research code (quote it)")
    ap.add_argument("--max-studies", type=int, default=DEFAULT_MAX_STUDIES,
                    help="cap of ClinicalTrials.gov studies to pull (default %(default)s)")
    ap.add_argument("--compact", action="store_true", help="single-line JSON")
    ap.add_argument("--no-studies-list", action="store_true",
                    help="drop the per-study array (keep only computed summaries)")
    args = ap.parse_args(argv)

    result = collect(args.name, max_studies=args.max_studies)

    if args.no_studies_list and result["deterministic_sources"].get("clinicaltrials_gov"):
        result["deterministic_sources"]["clinicaltrials_gov"].pop("studies", None)

    if args.compact:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
