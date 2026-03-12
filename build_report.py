import json
import pandas as pd
from pathlib import Path

def export_curriculum_json(csv_path: str, out_json_path: str = "report.json") -> str:
    # Column indexes (your current mapping)
    COL_CURR_ID = 0
    COL_CURR_TITLE = 1
    COL_MATCH = 44
    COL_SUB_ID = 42
    COL_SUB_TITLE = 43
    COL_ITEM_ID = 9
    COL_ITEM_TYPE = 8
    COL_ITEM_TITLE = 12

    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)

    def clean_series(s: pd.Series) -> pd.Series:
        return s.fillna("").astype(str).str.strip()

    col0 = clean_series(df.iloc[:, COL_CURR_ID])
    col44 = clean_series(df.iloc[:, COL_MATCH])

    # Keep match rows OR standalone rows where col44 is blank
    filtered = df[(col0 != "") & ((col0 == col44) | (col44 == ""))].copy()

    # Pre-clean the key columns we’ll use a lot
    filtered["_curr_id"] = clean_series(filtered.iloc[:, COL_CURR_ID])
    filtered["_curr_title"] = clean_series(filtered.iloc[:, COL_CURR_TITLE])
    filtered["_sub_id"] = clean_series(filtered.iloc[:, COL_SUB_ID])
    filtered["_sub_title"] = clean_series(filtered.iloc[:, COL_SUB_TITLE])
    filtered["_item_id"] = clean_series(filtered.iloc[:, COL_ITEM_ID])
    filtered["_item_type"] = clean_series(filtered.iloc[:, COL_ITEM_TYPE])
    filtered["_item_title"] = clean_series(filtered.iloc[:, COL_ITEM_TITLE])

    # Drop rows without item_id (optional but usually correct)
    filtered = filtered[filtered["_item_id"] != ""]

    report = []

    for curr_id, g in filtered.groupby("_curr_id"):
        curr_title = next((t for t in g["_curr_title"].tolist() if t), "")
        curriculum_node = {
            "id": curr_id,
            "title": curr_title,
            "subcurriculums": [],
            "standalone_items": []
        }

        # Split into with-sub and no-sub
        has_sub = g["_sub_id"] != ""
        g_with_sub = g[has_sub].copy()
        g_no_sub = g[~has_sub].copy()

        # Subcurriculums
        if not g_with_sub.empty:
            for sub_id, sg in g_with_sub.groupby("_sub_id"):
                sub_title = next((t for t in sg["_sub_title"].tolist() if t), "")
                # Deduplicate items by item_id
                items_df = sg[["_item_id", "_item_type", "_item_title"]].drop_duplicates("_item_id")
                items = [
                    {"id": r["_item_id"], "type": r["_item_type"], "title": r["_item_title"]}
                    for _, r in items_df.iterrows()
                ]
                curriculum_node["subcurriculums"].append({
                    "id": sub_id,
                    "title": sub_title,
                    "items": items
                })

        # Standalone items
        if not g_no_sub.empty:
            items_df = g_no_sub[["_item_id", "_item_type", "_item_title"]].drop_duplicates("_item_id")
            curriculum_node["standalone_items"] = [
                {"id": r["_item_id"], "type": r["_item_type"], "title": r["_item_title"]}
                for _, r in items_df.iterrows()
            ]

        report.append(curriculum_node)

    # Optional: sort for nicer UI
    report.sort(key=lambda x: x["id"])

    out_path = Path(out_json_path)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return str(out_path)


if __name__ == "__main__":
    csv_file = r"C:\path\to\QC RAW DATA 12MAR2026.csv"
    print("Wrote:", export_curriculum_json(csv_file, "report.json"))