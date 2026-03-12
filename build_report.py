import json
import pandas as pd
from pathlib import Path

# -------- COLUMN INDEXES (EDIT IF NEEDED) --------
COL_CURR_ID = 0
COL_CURR_TITLE = 1

COL_MATCH = 44  # used to keep match rows OR standalone rows

COL_SUB_ID = 42
COL_SUB_TITLE = 43

COL_ITEM_ID = 9
COL_ITEM_TYPE = 8
COL_ITEM_TITLE = 12
# -------------------------------------------------


def export_curriculum_json(csv_path: str, output_json: str = "report.json") -> str:
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)

    def clean(series: pd.Series) -> pd.Series:
        return series.fillna("").astype(str).str.strip()

    # Clean important columns
    col0 = clean(df.iloc[:, COL_CURR_ID])
    col44 = clean(df.iloc[:, COL_MATCH])

    # Keep:
    # - rows where col0 == col44
    # - rows where col44 is empty (standalone items)
    filtered = df[(col0 != "") & ((col0 == col44) | (col44 == ""))].copy()

    # Clean columns used in output
    filtered["_curr_id"] = clean(filtered.iloc[:, COL_CURR_ID])
    filtered["_curr_title"] = clean(filtered.iloc[:, COL_CURR_TITLE])
    filtered["_sub_id"] = clean(filtered.iloc[:, COL_SUB_ID])
    filtered["_sub_title"] = clean(filtered.iloc[:, COL_SUB_TITLE])
    filtered["_item_id"] = clean(filtered.iloc[:, COL_ITEM_ID])
    filtered["_item_type"] = clean(filtered.iloc[:, COL_ITEM_TYPE])
    filtered["_item_title"] = clean(filtered.iloc[:, COL_ITEM_TITLE])

    # Remove rows without item ID
    filtered = filtered[filtered["_item_id"] != ""]

    report = []

    for curr_id, group in filtered.groupby("_curr_id"):

        # Curriculum title (first non-empty)
        curr_title = next((t for t in group["_curr_title"].tolist() if t != ""), "")

        curriculum_node = {
            "id": curr_id,
            "title": curr_title,
            "subcurriculums": [],
            "standalone_items": []
        }

        # Split into with-sub and no-sub
        has_sub = group["_sub_id"] != ""
        group_with_sub = group[has_sub]
        group_no_sub = group[~has_sub]

        # -------- Subcurriculums --------
        for sub_id, sub_group in group_with_sub.groupby("_sub_id"):

            sub_title = next((t for t in sub_group["_sub_title"].tolist() if t != ""), "")

            # Deduplicate items
            items_df = sub_group[["_item_id", "_item_type", "_item_title"]].drop_duplicates("_item_id")

            items = []
            for _, row in items_df.iterrows():
                items.append({
                    "id": row["_item_id"],
                    "type": row["_item_type"],
                    "title": row["_item_title"]
                })

            curriculum_node["subcurriculums"].append({
                "id": sub_id,
                "title": sub_title,
                "items": items
            })

        # -------- Standalone Items --------
        if not group_no_sub.empty:
            items_df = group_no_sub[["_item_id", "_item_type", "_item_title"]].drop_duplicates("_item_id")

            for _, row in items_df.iterrows():
                curriculum_node["standalone_items"].append({
                    "id": row["_item_id"],
                    "type": row["_item_type"],
                    "title": row["_item_title"]
                })

        report.append(curriculum_node)

    # Sort curriculums alphabetically
    report.sort(key=lambda x: x["id"])

    # Write JSON file
    output_path = Path(output_json)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return str(output_path)


# --------- RUN IT ---------
if __name__ == "__main__":
    csv_file = r"C:\Users\andrea.macgown\OneDrive - Thermo Fisher Scientific\Desktop\TRAINING SYSTEM\OFFICIAL REPORTS FOR DEPARTMENTS\QC RAW DATA 12MAR2026.csv"

    json_path = export_curriculum_json(csv_file)
    print("Created:", json_path)