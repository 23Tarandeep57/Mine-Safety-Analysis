import json
import re
from datetime import datetime, timezone
from dateutil import parser as dateparse
from .llm import get_llm
from .config import GROQ_API_KEY

def _normalize_text_for_parsing(text: str) -> str:
    text = re.sub(r"\x00", " ", text)
    text = re.sub(r"(?<=\d)\s+(?=\d)", "", text)
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("%PDF")]
    return "\n".join(lines)


def _parse_dgms_alert_text(text: str) -> dict:
    t = _normalize_text_for_parsing(text)
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    t_lower = "\n".join(lines)

    def find(pattern, flags=re.IGNORECASE):
        m = re.search(pattern, t_lower, flags)
        return (m.group(1).strip() if m else "")

    subject = find(r"subject\s*[:\-–]\s*(.+)")
    brief_cause = find(r"brief\s*cause\s*[:\-–]\s*(.+)")
    place = find(r"place\s*of\s*accident[^:]*[:\-–]\s*(.+)")
    date_time = find(r"date\s*(?:and\s*time)?\s*of\s*accident[^:]*[:\-–]\s*(.+)")

    district = find(r"district\s*[:\-–]\s*([A-Za-z .]+)")
    state = find(r"state\s*[:\-–]\s*([A-Za-z .]+)")

    recs = []
    rec_block_match = re.search(r"(recommendations?[^\n]*?:)([\s\S]{0,1200})", t_lower, re.IGNORECASE)
    if rec_block_match:
        block = rec_block_match.group(2)
        for ln in block.splitlines():
            ln = ln.strip(" -*•\t")
            if not ln:
                continue
            if len(ln) < 8:
                continue
            if any(k in ln.lower() for k in ["shall", "should", "ensure", "must", "provide", "prohibit", "avoid", "maintain"]):
                recs.append(ln)
            if len(recs) >= 5:
                break
    if not recs:
        for ln in lines:
            ll = ln.lower().lstrip("-*•")
            if any(k in ll for k in ["shall", "should", "ensure", "must", "provide", "prohibit", "avoid", "maintain", "supervise", "training"]):
                if 20 <= len(ln) <= 220:
                    recs.append(ln)
            if len(recs) >= 5:
                break

    score = sum(1 for v in [subject, brief_cause, place, date_time] if v)
    return {
        "subject": subject,
        "brief_cause": brief_cause,
        "place": place,
        "date_time": date_time,
        "district": district,
        "state": state,
        "recs": recs,
        "score": score,
    }


def _parse_date_to_iso(datestr: str, default_time: bool = False) -> str:
    if not datestr:
        return ""
    try:
        dt = dateparse.parse(datestr, dayfirst=True, fuzzy=True)
        if default_time and dt.time() == datetime.min.time():
            return dt.strftime("%Y-%m-%d")
        return dt.strftime("%Y-%m-%dT%H:%M:%S") if dt.time() != datetime.min.time() else dt.strftime("%Y-%m-%d")
    except Exception:
        m = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", datestr)
        if m:
            d, mth, y = map(int, m.groups())
            try:
                dt = datetime(y, mth, d)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
        return ""


def _derive_report_id(text: str, title: str) -> str:
    t = _normalize_text_for_parsing(title + "\n" + text)
    m = re.search(r"s(?:afety)?\s*alert\s*[:\-]?\s*(\d{1,3})\s*[\/-]\s*(20\d{2})", t, re.IGNORECASE)
    if not m:
        m = re.search(r"\b(\d{1,3})\s*/\s*(20\d{2})\b", t)
    if m:
        return f"SA-{m.group(1)}-{m.group(2)}"
    return ""


def _extract_mine_fields(lines: list[str]) -> dict:
    def find_val(key_regex: str) -> str:
        # Ensure alternations are grouped so the value pattern applies to all alternatives
        pattern = rf"(?:{key_regex})\s*[:\-–]\s*(.+)"
        for ln in lines:
            m = re.search(pattern, ln, re.IGNORECASE)
            if m:
                val = m.group(1) if m.lastindex and m.group(1) is not None else ""
                return val.strip() if isinstance(val, str) else ""
        return ""

    name = find_val(r"name\s*of\s*mine|mine\s*name")
    owner = find_val(r"name\s*of\s*owner|owner")
    district = find_val(r"district")
    state = find_val(r"state")
    mineral = find_val(r"mineral|ore|coal|limestone|granite|iron|bauxite")
    return {
        "name": name,
        "owner": owner,
        "district": district,
        "state": state,
        "mineral": mineral,
    }


def _extract_casualties(lines: list[str]) -> tuple[list[dict], list[dict]]:
    fatalities = []
    injuries = []
    block = "\n".join(lines)
    name_matches = re.findall(r"name\s*of\s*deceased\s*[:\-–]\s*([^\n]+)", block, re.IGNORECASE)
    for nm in name_matches:
        fatalities.append({"name": nm.strip(), "designation": "", "age": None, "experience": ""})

    for i, ln in enumerate(lines):
        ll = ln.lower()
        if any(k in ll for k in ["deceased", "died", "succumbed"]) and len(ln) < 180:
            window = " ".join(lines[max(0, i-2): i+3])
            name_match = re.search(r"(shri|smt|kumari|mr\.?|ms\.?|mrs\.?)\s+([A-Za-z][A-Za-z .'-]{2,})", window, re.IGNORECASE)
            age_match = re.search(r"age\s*[:\-–]?\s*(\d{1,2})", window, re.IGNORECASE)
            desig_match = re.search(r"designation\s*[:\-–]\s*([^,.;\n]+)", window, re.IGNORECASE)
            exp_match = re.search(r"experience\s*[:\-–]?\s*([A-Za-z0-9 ./-]+)", window, re.IGNORECASE)
            victim = {
                "name": (name_match.group(2).strip() if name_match else "").strip(),
                "designation": (desig_match.group(1).strip() if desig_match else "").strip(),
                "age": int(age_match.group(1)) if age_match else None,
                "experience": (exp_match.group(1).strip() if exp_match else "").strip(),
            }
            if victim not in fatalities:
                fatalities.append(victim)

    return fatalities, injuries


def parse_report_to_schema_heuristic(text: str, source_url: str, title: str) -> dict:
    t = _normalize_text_for_parsing(text)
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    parsed = _parse_dgms_alert_text(text)

    report_id = _derive_report_id(text, title)
    date_reported = ""
    for ln in lines[:40]:
        m = re.search(r"dated\s*[:\-–]?\s*([A-Za-z0-9 .:/-]+)", ln, re.IGNORECASE)
        if m:
            date_reported = _parse_date_to_iso(m.group(1), default_time=True)
            if date_reported:
                break

    accident_dt = _parse_date_to_iso(parsed.get("date_time", ""))
    mine = _extract_mine_fields(lines)
    loc = parsed.get("place")
    fatalities, injuries = _extract_casualties(lines)
    brief_cause = parsed.get("brief_cause")
    best_practices = parsed.get("recs", [])

    doc = {
        "report_id": report_id,
        "date_reported": date_reported,
        "accident_date": accident_dt,
        "mine_details": mine,
        "incident_details": {
            "location": loc,
            "fatalities": fatalities,
            "injuries": injuries,
            "brief_cause": brief_cause,
        },
        "best_practices": best_practices,
        "source_url": source_url,
        "summary": "",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "_raw_title": title,
        "_raw_text": t,
    }
    return doc


def parse_report_to_schema_llm(text: str, source_url: str, title: str) -> dict | None:
    if not GROQ_API_KEY:
        return None
    system = (
        "You are a precise information extraction system for DGMS India Safety Alerts. "
        "Return ONLY valid JSON matching the provided schema. Do not include comments or extra keys. "
        "Dates must be ISO: date_reported as YYYY-MM-DD; accident_date as YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS if time known. "
        "If a field is unknown, use an empty string, empty list, or null where appropriate."
    )
    schema_example = {
        "report_id": "SA-21-2025",
        "date_reported": "2025-08-22",
        "accident_date": "2025-07-23T02:15:00",
        "mine_details": {"name": "", "owner": "", "district": "", "state": "", "mineral": ""},
        "incident_details": {
            "location": "",
            "fatalities": [{"name": "", "designation": "", "age": None, "experience": ""}],
            "injuries": [],
            "brief_cause": "",
        },
        "best_practices": [],
        "source_url": source_url,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    prompt = (
        f"Extract the following report into this JSON schema (no extra keys):\n{json.dumps(schema_example, ensure_ascii=False)}\n\n"
        f"Title: {title}\n\nReport text:\n{text[:6000]}\n"
    )
    try:
        print("Using LLM for extraction...")
        llm = get_llm()
        resp = llm.invoke([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ])
        content = resp.content if hasattr(resp, "content") else str(resp)
        json_str = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.IGNORECASE | re.MULTILINE)
        data = json.loads(json_str)
        if not data.get("report_id"):
            data["report_id"] = _derive_report_id(text, title)
        if not data.get("date_reported"):
            for ln in _normalize_text_for_parsing(text).splitlines()[:40]:
                m = re.search(r"dated\s*[:\-–]?\s*([A-Za-z0-9 .:/-]+)", ln, re.IGNORECASE)
                if m:
                    data["date_reported"] = _parse_date_to_iso(m.group(1), default_time=True)
                    break
        if data.get("date_reported"):
            data["date_reported"] = _parse_date_to_iso(data["date_reported"], default_time=True)
        if data.get("accident_date"):
            data["accident_date"] = _parse_date_to_iso(data["accident_date"]) or _parse_date_to_iso(data.get("incident_details", {}).get("date_time", ""))
        data["source_url"] = source_url
        data["created_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        data.setdefault("mine_details", {"name": "", "owner": "", "district": "", "state": "", "mineral": ""})
        data.setdefault("incident_details", {"location": "", "fatalities": [], "injuries": [], "brief_cause": ""})
        data.setdefault("best_practices", [])
        return data
    except Exception:
        return None
