# export_result_logs.py
# Exports matchday report data to JSON, CSV, and text formats for archival or external use

import json
import csv
from pathlib import Path
from typing import Dict


def export_to_json(report: Dict, filepath: str):
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)


def export_to_csv(report: Dict, filepath: str):
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "match_id", "white_id", "black_id", "white_status", "black_status", "rDD", "rULT", "rMBi"
        ])
        for match in report.get("matches", []):
            row = [
                match["match_id"],
                match["white_id"],
                match["black_id"],
                match["white_status"],
                match["black_status"],
                match["white_rStats"].get("rDD", 0),
                match["white_rStats"].get("rULT", 0),
                match["white_rStats"].get("rMBi", 0)
            ]
            writer.writerow(row)


def export_to_txt_summary(report: Dict, filepath: str):
    with open(filepath, "w") as f:
        f.write(f"Total Matches: {report['summary']['total_matches']}\n")
        f.write(f"FL Replacements: {report['summary']['FL_replacements']}\n")
        f.write("\nTotal rStats:\n")
        for k, v in report["summary"]["total_rStats"].items():
            f.write(f"{k}: {v}\n")


# Example usage
if __name__ == "__main__":
    mock_report = {
        "summary": {
            "total_matches": 1,
            "FL_replacements": 1,
            "total_rStats": {"rDD": 12, "rULT": 1, "rMBi": 1}
        },
        "matches": [
            {
                "match_id": "match_01",
                "white_id": "A1",
                "black_id": "B1",
                "white_status": "active",
                "black_status": "dead",
                "white_rStats": {"rDD": 12, "rULT": 1, "rMBi": 1},
                "black_rStats": {}
            }
        ]
    }

    export_to_json(mock_report, "matchday_report.json")
    export_to_csv(mock_report, "matchday_report.csv")
    export_to_txt_summary(mock_report, "matchday_summary.txt")
