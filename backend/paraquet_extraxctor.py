import json
from pathlib import Path

import pandas as pd

# Directories
INPUT_DIR = Path("/home/vikas/Documents/Law-law-land/data/metadata")
OUTPUT_DIR = Path("/home/vikas/Documents/Law-law-land/data/metadata_json")
    
# Set to True if you want to retain the raw HTML in the JSON.
INCLUDE_RAW_HTML = False

# Columns useful for legal judgment search and filtering.
METADATA_COLUMNS = [
    "title",
    "petitioner",
    "respondent",
    "description",
    "judge",
    "author_judge",
    "citation",
    "case_id",
    "cnr",
    "decision_date",
    "disposal_nature",
    "court",
    "available_languages",
    "path",
    "nc_display",
    "scraped_at",
    "year",
]


def clean_value(value):
    """Convert missing values and Pandas types to JSON-compatible values."""
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass

    return value


def convert_parquet_to_json(parquet_path: Path) -> int:
    """Convert one yearly Parquet file into a JSON array."""

    print(f"Reading: {parquet_path}")

    df = pd.read_parquet(parquet_path)

    # Retain all columns or only the structured metadata.
    if INCLUDE_RAW_HTML:
        columns = df.columns.tolist()
    else:
        columns = [
            column
            for column in METADATA_COLUMNS
            if column in df.columns
        ]

    df = df[columns]

    # Preserve the year-based directory structure.
    relative_path = parquet_path.relative_to(INPUT_DIR)
    output_path = (
        OUTPUT_DIR
        / relative_path.parent
        / "metadata.json"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert each row into a JSON-compatible dictionary.
    records = [
        {
            key: clean_value(value)
            for key, value in record.items()
        }
        for record in df.to_dict(orient="records")
    ]

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Saved {len(records):,} records to {output_path}")

    return len(records)


def main():
    if not INPUT_DIR.exists():
        raise FileNotFoundError(
            f"Directory not found: {INPUT_DIR.resolve()}"
        )

    parquet_files = sorted(
        INPUT_DIR.rglob("metadata.parquet")
    )

    if not parquet_files:
        raise FileNotFoundError(
            f"No metadata.parquet files found in {INPUT_DIR.resolve()}"
        )

    total_records = 0

    for parquet_path in parquet_files:
        total_records += convert_parquet_to_json(parquet_path)

    print("\nConversion complete.")
    print(f"Total records: {total_records:,}")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()