from __future__ import annotations

import collections
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
from sklearn.cluster import KMeans
try:  # optional dependency; we fallback to kmeans if unavailable
    import hdbscan  # type: ignore
except Exception:  # pragma: no cover
    hdbscan = None  # type: ignore
from sentence_transformers import SentenceTransformer

from .config import GROQ_API_KEY

try:
    from .llm import get_llm
except Exception:  # pragma: no cover
    get_llm = None  # type: ignore


def parse_iso_dt(s: str) -> Optional[datetime]:
    """Parse YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS into datetime. Return None if invalid."""
    if not s:
        return None
    try:
        if "T" in s:
            return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except Exception:
        return None


def season_for_month(m: int) -> str:
    """Rough India-centric seasons: Winter (Dec–Feb), Summer (Mar–May), Monsoon (Jun–Sep), Post-monsoon (Oct–Nov)."""
    if m in (12, 1, 2):
        return "winter"
    if m in (3, 4, 5):
        return "summer"
    if m in (6, 7, 8, 9):
        return "monsoon"
    return "post-monsoon"


def time_of_day_bucket(dt: Optional[datetime]) -> str:
    if not dt:
        return "unknown"
    h = dt.hour
    if 0 <= h < 6:
        return "00:00–05:59"
    if 6 <= h < 12:
        return "06:00–11:59"
    if 12 <= h < 18:
        return "12:00–17:59"
    return "18:00–23:59"

@dataclass
class ClusterInsight:
    label: int
    size: int
    top_terms: List[str]
    sample_causes: List[str]


@dataclass
class AdvancedReport:
    total_incidents: int
    date_range: Tuple[str, str]
    clusters: List[ClusterInsight]
    by_cause: List[Tuple[str, int]]
    by_state: List[Tuple[str, int]]
    by_district: List[Tuple[str, int]]
    by_mineral: List[Tuple[str, int]]
    by_season: List[Tuple[str, int]]
    by_time_of_day: List[Tuple[str, int]]


def filter_last_months(docs: Iterable[Dict[str, Any]], months: int = 6):
    now = datetime.utcnow()
    cutoff = now - timedelta(days=months * 30)
    filtered = []
    min_dt = None
    max_dt = None
    for d in docs:
        dt = parse_iso_dt(d.get("accident_date", "") or "") or parse_iso_dt(d.get("date_reported", "") or "")
        if not dt:
            continue
        if dt >= cutoff:
            filtered.append(d)
            min_dt = dt if not min_dt or dt < min_dt else min_dt
            max_dt = dt if not max_dt or dt > max_dt else max_dt
    return filtered, (min_dt.strftime("%Y-%m-%d") if min_dt else "", max_dt.strftime("%Y-%m-%d") if max_dt else "")


def embed_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    model = SentenceTransformer(model_name)
    return model.encode(texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)


def kmeans_clusters(embeddings: np.ndarray, k: int) -> np.ndarray:
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = km.fit_predict(embeddings)
    return labels


def hdbscan_clusters(
    embeddings: np.ndarray,
    min_cluster_size: int = 5,
    min_samples: Optional[int] = None,
    metric: str = "euclidean",
    cluster_selection_epsilon: float = 0.0,
) -> Optional[np.ndarray]:
    if hdbscan is None:
        return None
    kwargs = {
        "min_cluster_size": max(2, int(min_cluster_size)),
        "metric": metric,
        "cluster_selection_epsilon": float(cluster_selection_epsilon),
    }
    if min_samples is not None:
        kwargs["min_samples"] = int(min_samples)
    clusterer = hdbscan.HDBSCAN(**kwargs)
    return clusterer.fit_predict(embeddings)


def top_terms_per_cluster(texts: List[str], labels: np.ndarray, top_n: int = 5) -> List[List[str]]:
    # very light term frequency approach
    by_cluster = collections.defaultdict(list)
    for t, lab in zip(texts, labels):
        ilab = int(lab)
        if ilab < 0:  # ignore noise cluster if any
            continue
        by_cluster[ilab].append(t.lower())

    terms = []
    stop = set("the a an of to and for in on with without by due from as is was were be been being shall should must may can could would not no into at it this that those these there here".split())
    for lab, docs in sorted(by_cluster.items()):
        counter = collections.Counter()
        for d in docs:
            tokens = [w.strip(".,;:()[]{}'\"-_/") for w in d.split()]
            tokens = [w for w in tokens if len(w) > 2 and w not in stop and not any(ch.isdigit() for ch in w)]
            counter.update(tokens)
        terms.append([w for w, _ in counter.most_common(top_n)])
    return terms


def make_advanced_report(
    docs: Iterable[Dict[str, Any]],
    months: int = 6,
    k: int = 5,
    clustering: str = "kmeans",
    min_cluster_size: int = 5,
    min_samples: Optional[int] = None,
) -> AdvancedReport:
    filtered, date_range = filter_last_months(docs, months=months)
    total = len(filtered)
    if total == 0:
        return AdvancedReport(0, date_range, [], [], [], [], [], [], [])

    # Build texts from brief_cause + location + mineral for semantics
    texts = []
    for d in filtered:
        cause = d.get("incident_details", {}).get("brief_cause", "") or ""
        md = d.get("mine_details", {}) or {}
        loc = " ".join([md.get("district", ""), md.get("state", "")]).strip()
        mineral = md.get("mineral", "") or ""
        text = " | ".join([cause, loc, mineral]).strip(" |")
        texts.append(text if text else "unknown")

    # Embeddings + clustering
    embeddings = embed_texts(texts)
    labels = None
    used_k = None
    if clustering.lower() == "hdbscan":
        labels = hdbscan_clusters(
            embeddings,
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric="euclidean",
            cluster_selection_epsilon=0.0,
        )
        if labels is None:
            # Fallback to kmeans if hdbscan not installed
            clustering = "kmeans"
    if labels is None:
        used_k = max(2, min(k, min(10, total)))
        labels = kmeans_clusters(embeddings, used_k)

    # Build cluster list, skipping noise (-1)
    terms = top_terms_per_cluster(texts, labels, top_n=6)

    # Summaries per cluster
    clusters = []
    unique_labels = sorted({int(l) for l in labels if int(l) >= 0})
    for lab in unique_labels:
        idxs = [i for i, l in enumerate(labels) if int(l) == lab]
        sample_causes = [filtered[i].get("incident_details", {}).get("brief_cause", "") or "" for i in idxs[:5]]
        # terms list is ordered by sorted cluster keys used above; map label index safely
        terms_map = {lbl: t for lbl, t in zip(unique_labels, terms)} if terms else {}
        clusters.append(ClusterInsight(label=lab, size=len(idxs), top_terms=terms_map.get(lab, []), sample_causes=sample_causes))

    # Other distributions
    c_state = collections.Counter()
    c_district = collections.Counter()
    c_mineral = collections.Counter()
    c_season = collections.Counter()
    c_tod = collections.Counter()
    c_cause = collections.Counter()

    # Simple keyword-based cause categorization
    CAUSE_MAP = {
        "vehicle_collision": ["truck", "tipper", "dumper", "vehicle", "haul road", "run over", "hit by"],
        "electrocution": ["electrocution", "electric", "shock", "cable", "energized"],
        "fall_of_ground": ["overhang", "side fall", "slope", "bench failure", "rock fall", "fall of roof", "fall of rib"],
        "conveyor_machinery": ["conveyor", "belt", "pulley", "roller", "gear", "guard"],
        "blasting": ["blast", "explosive", "detonator", "misfire"],
        "maintenance": ["maintenance", "repair", "overhaul", "servicing"],
        "training_noncompliance": ["violation", "non-compliance", "unauthorised", "unauthorized", "no ppe", "no helmet", "no training"],
    }

    def categorize_cause(text: str) -> str:
        if not text:
            return "unknown"
        tl = text.lower()
        for label, kws in CAUSE_MAP.items():
            if any(k in tl for k in kws):
                return label
        if any(k in tl for k in ["fall", "slip", "trip"]):
            return "fall_other"
        return "unknown"

    for d in filtered:
        md = d.get("mine_details", {}) or {}
        c_state[(md.get("state") or "unknown").strip() or "unknown"] += 1
        c_district[(md.get("district") or "unknown").strip() or "unknown"] += 1
        c_mineral[(md.get("mineral") or "unknown").strip() or "unknown"] += 1
        # Cause category
        cause_text = d.get("incident_details", {}).get("brief_cause", "") or ""
        c_cause[categorize_cause(cause_text)] += 1
        adt = parse_iso_dt(d.get("accident_date", "") or "")
        drt = parse_iso_dt(d.get("date_reported", "") or "")
        dt = adt or drt
        if dt:
            c_season[season_for_month(dt.month)] += 1
        c_tod[time_of_day_bucket(adt) if adt else "unknown"] += 1

    return AdvancedReport(
        total_incidents=total,
        date_range=date_range,
        clusters=clusters,
        by_cause=c_cause.most_common(10),
        by_state=c_state.most_common(10),
        by_district=c_district.most_common(10),
        by_mineral=c_mineral.most_common(10),
        by_season=c_season.most_common(10),
        by_time_of_day=c_tod.most_common(10),
    )


def render_narrative(report: AdvancedReport) -> str:
    # If LLM configured, ask it for a narrative; otherwise provide a concise heuristic summary
    def bullet_pairs(title: str, pairs: List[Tuple[str, int]]):
        if not pairs:
            return f"## {title}\n(none)\n"
        return "\n".join([f"## {title}"] + [f"- {k}: {v}" for k, v in pairs]) + "\n"

    md = [
        f"# DGMS Fatal Accident Patterns (Last 6 Months)",
        f"Period: {report.date_range[0]} to {report.date_range[1]}",
        f"Total incidents: {report.total_incidents}",
        "",
        "## Clustered Themes",
    ]
    for c in report.clusters:
        md.append(f"- Cluster {c.label} (n={c.size}): top terms = {', '.join(c.top_terms) if c.top_terms else '(none)'}")
    md.append("")
    md.append(bullet_pairs("Causes", report.by_cause))
    md.append(bullet_pairs("States", report.by_state))
    md.append(bullet_pairs("Districts", report.by_district))
    md.append(bullet_pairs("Minerals", report.by_mineral))
    md.append(bullet_pairs("Seasons", report.by_season))
    md.append(bullet_pairs("Time of Day", report.by_time_of_day))

    narrative_intro = "\n".join(md) + "\n"

    if GROQ_API_KEY and get_llm is not None:
        llm = get_llm()
        prompt = (
            "You are a safety analytics expert. Given the clusters (with top terms) and distributions "
            "by state, district, mineral, season, and time of day, write a concise, actionable narrative "
            "(8-12 bullet points) summarizing regional trends, common causes, and prioritized safety recommendations "
            "for the next quarter. Avoid generic advice; be specific and grounded in the data.\n\n"
            f"DATA:\n{narrative_intro}"
        )
        try:
            resp = llm.invoke(prompt)
            text = resp.content if hasattr(resp, "content") else str(resp)
            return narrative_intro + "\n## AI Narrative\n" + text.strip() + "\n"
        except Exception:
            pass

    # Fallback minimal narrative
    md2 = [
        "## Narrative (Heuristic)",
        "- The clusters suggest recurring themes driven by location/mineral context and similar brief causes.",
        "- Prioritize controls around haul roads and bench stability where relevant.",
        "- States/districts with higher counts may warrant targeted inspections and training refreshers.",
        "- Incidents that concentrate in certain seasons (e.g., monsoon) suggest weather-related controls.",
        "- Time-of-day spikes should inform shift briefs and supervision intensity.",
    ]
    return narrative_intro + "\n" + "\n".join(md2) + "\n"
