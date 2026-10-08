import json
import re
from pathlib import Path
from bs4 import BeautifulSoup


INPUT_DIR = Path("/home/vikas/Documents/Law-law-land/data/metadata/2026")
OUTPUT_FILE = Path("/home/vikas/Documents/Law-law-land/data/judgments_metadata_2026.json")


def clean_text(text):
    """Normalize whitespace and HTML text."""
    if not text:
        return None

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_metadata(file_path):
    """Extract judgment metadata from one JSON file."""

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_html = data.get("raw_html", "")

    if not raw_html:
        return None

    soup = BeautifulSoup(raw_html, "lxml")

    metadata = {
        "judgment_id": None,
        "year": data.get("citation_year", 2026),
        "case_title": None,
        "decision_date": None,
        "case_number": None,
        "citation": None,
        "neutral_citation": data.get("nc_display"),
        "cnr": None,
        "judges": [],
        "bench_strength": None,
        "disposal_nature": None,
        "languages": [],
        "issue": None,
        "source_path": data.get("path"),
        "scraped_at": data.get("scraped_at"),
    }

    # ---------------------------------------------------------
    # Case title
    # ---------------------------------------------------------

    # Example:
    # <button ...>
    #   <strong>
    #       GOPAL KRISHAN & ORS.
    #       versus
    #       DAULAT RAM & ORS.
    #   </strong>
    # </button>

    strong_tags = soup.find_all("strong")

    for tag in strong_tags:
        text = clean_text(tag.get_text(" ", strip=True))

        if text and " versus " in text.lower():
            metadata["case_title"] = text
            break

    # ---------------------------------------------------------
    # Citation
    # ---------------------------------------------------------

    # Example:
    # [2025] 1 S.C.R. 93

    escr_text = soup.select_one(".escrText")

    if escr_text:
        metadata["citation"] = clean_text(escr_text.get_text())

    # ---------------------------------------------------------
    # Neutral citation
    # ---------------------------------------------------------

    nc_display = soup.select_one(".ncDisplay")

    if nc_display:
        metadata["neutral_citation"] = clean_text(
            nc_display.get_text()
        )

    # ---------------------------------------------------------
    # CNR
    # ---------------------------------------------------------

    cnr = soup.find("input", {"id": "cnr"})

    if cnr:
        metadata["cnr"] = cnr.get("value")

    # ---------------------------------------------------------
    # Coram / Judges
    # ---------------------------------------------------------

    # Example:
    # <strong>
    #   Coram : C.T. RAVIKUMAR, SANJAY KAROL
    # </strong>

    page_text = soup.get_text(" ", strip=True)

    coram_match = re.search(
        r"Coram\s*:\s*(.*?)(?=\s+Issue for Consideration|\s+Decision Date)",
        page_text,
        re.IGNORECASE,
    )

    if coram_match:
        coram_text = clean_text(coram_match.group(1))

        # Split judges by comma
        judges = [
            clean_text(j)
            for j in coram_text.split(",")
            if clean_text(j)
        ]

        metadata["judges"] = judges

    # ---------------------------------------------------------
    # Bench strength
    # ---------------------------------------------------------

    bench_match = re.search(
        r"Bench\s*:\s*(\d+)\s*Judges?",
        page_text,
        re.IGNORECASE,
    )

    if bench_match:
        metadata["bench_strength"] = int(
            bench_match.group(1)
        )

    # ---------------------------------------------------------
    # Decision date
    # ---------------------------------------------------------

    date_match = re.search(
        r"Decision\s*Date\s*:\s*(\d{2}-\d{2}-\d{4})",
        page_text,
        re.IGNORECASE,
    )

    if date_match:
        raw_date = date_match.group(1)

        # Convert DD-MM-YYYY -> YYYY-MM-DD
        day, month, year = raw_date.split("-")

        metadata["decision_date"] = (
            f"{year}-{month}-{day}"
        )

    # ---------------------------------------------------------
    # Case number
    # ---------------------------------------------------------

    case_match = re.search(
        r"Case\s*No\s*:\s*(.*?)(?=\s*\|\s*Disposal Nature)",
        page_text,
        re.IGNORECASE,
    )

    if case_match:
        metadata["case_number"] = clean_text(
            case_match.group(1)
        )

    # ---------------------------------------------------------
    # Disposal nature
    # ---------------------------------------------------------

    disposal_match = re.search(
        r"Disposal\s*Nature\s*:\s*(.*?)(?=\s*\|\s*Bench)",
        page_text,
        re.IGNORECASE,
    )

    if disposal_match:
        metadata["disposal_nature"] = clean_text(
            disposal_match.group(1)
        )

    # ---------------------------------------------------------
    # Issue for Consideration
    # ---------------------------------------------------------

    issue_match = re.search(
        r"Issue\s+for\s+Consideration\s*(.*?)(?=\s+Decision\s+Date\s*:)",
        page_text,
        re.IGNORECASE,
    )

    if issue_match:
        metadata["issue"] = clean_text(
            issue_match.group(1)
        )

    # ---------------------------------------------------------
    # Languages
    # ---------------------------------------------------------

    language_select = soup.find(
        "select",
        {"id": re.compile(r"language", re.IGNORECASE)}
    )

    if language_select:

        for option in language_select.find_all("option"):

            language = clean_text(
                option.get_text(" ", strip=True)
            )

            if not language:
                continue

            # Remove empty/default options
            metadata["languages"].append(language)

    # If no language selector was found, assume English
    if not metadata["languages"]:
        metadata["languages"] = ["English"]

    # ---------------------------------------------------------
    # Judgment ID
    # ---------------------------------------------------------

    # Prefer neutral citation.
    #
    # Example:
    # 2025 INSC 18
    #
    # becomes:
    # 2025INSC18

    if metadata["neutral_citation"]:

        judgment_id = re.sub(
            r"[^A-Za-z0-9]",
            "",
            metadata["neutral_citation"]
        )

        metadata["judgment_id"] = judgment_id

    # Fallback to filename/path if necessary
    if not metadata["judgment_id"]:

        metadata["judgment_id"] = file_path.stem

    return metadata


def main():

    json_files = list(
        INPUT_DIR.rglob("*.json")
    )

    print(f"Found {len(json_files)} JSON files.")

    results = []

    failed = []

    for index, file_path in enumerate(json_files, start=1):

        try:

            metadata = extract_metadata(file_path)

            if metadata:
                results.append(metadata)

            if index % 100 == 0:
                print(
                    f"Processed {index}/{len(json_files)}"
                )

        except Exception as e:

            failed.append({
                "file": str(file_path),
                "error": str(e),
            })

            print(
                f"ERROR: {file_path}\n"
                f"       {e}"
            )

    # ---------------------------------------------------------
    # Save output
    # ---------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("Extraction complete")
    print("=" * 60)

    print(f"JSON files found : {len(json_files)}")
    print(f"Successfully parsed : {len(results)}")
    print(f"Failed : {len(failed)}")

    # ---------------------------------------------------------
    # Missing-field report
    # ---------------------------------------------------------

    fields = [
        "judgment_id",
        "case_title",
        "decision_date",
        "case_number",
        "citation",
        "neutral_citation",
        "cnr",
        "judges",
        "bench_strength",
        "disposal_nature",
        "languages",
        "issue",
    ]

    print("\nMissing fields:")

    for field in fields:

        missing = sum(
            1
            for item in results
            if not item.get(field)
        )

        print(
            f"  {field:<20} {missing}"
        )

    print(f"\nOutput: {OUTPUT_FILE}")

    # ---------------------------------------------------------
    # Failed files
    # ---------------------------------------------------------

    if failed:

        failed_file = Path(
            "data/metadata_extraction_errors.json"
        )

        with open(
            failed_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                failed,
                f,
                ensure_ascii=False,
                indent=2
            )

        print(
            f"\nFailed files written to: {failed_file}"
        )


if __name__ == "__main__":
    main()