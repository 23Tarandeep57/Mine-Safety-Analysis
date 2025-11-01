#!/usr/bin/env python3
import os
from pymongo import MongoClient
from utility.config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION, DATA_DIR
from utility.analysis import make_advanced_report, render_narrative


def analyze_all_reports():
    months = int(os.environ.get("ANALYSIS_MONTHS", "12"))
    output_path = os.environ.get("ANALYSIS_OUTPUT", str(DATA_DIR / "analysis_report_advanced.md"))
    k = int(os.environ.get("ANALYSIS_CLUSTERS", "5"))
    clustering = os.environ.get("ANALYSIS_CLUSTERING", "kmeans")  # or "hdbscan"
    min_cluster_size = int(os.environ.get("HDBSCAN_MIN_CLUSTER_SIZE", "5"))
    min_samples = os.environ.get("HDBSCAN_MIN_SAMPLES")
    min_samples = int(min_samples) if min_samples is not None and min_samples != "" else None

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
    coll = client[MONGODB_DB][MONGODB_COLLECTION]
    docs = list(coll.find({}))

    report = make_advanced_report(
        docs,
        months=months,
        k=k,
        clustering=clustering,
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
    )
    md = render_narrative(report)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Advanced analysis report written to {output_path}")


def main():
    analyze_all_reports()


if __name__ == "__main__":
    main()
