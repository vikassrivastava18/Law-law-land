import argparse
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


# =============================================================
# Configuration
# =============================================================

ERROR_FILE = Path(
    "data/metadata_extraction_errors.json"
)


# =============================================================
# Utility functions
# =============================================================

def clean_text(text):
    """
    Normalize whitespace and remove unwanted characters.
    """

    if not text:
        return None

    text = str(text)

    # Non-breaking space
    text = text.replace("\xa0", " ")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_date(date_string):
    """
    Convert DD-MM-YYYY to YYYY-MM-DD.
    """

    if not date_string:
        return None

    match = re.search(
        r"(\d{2})-(\d{2})-(\d{4})",
        date_string
    )

    if not match:
        return None

    day, month, year = match.groups()

    return f"{year}-{month}-{day}"


def extract_judges(coram_text):
    """
    Extract individual judge names from Coram text.

    Example:

        Coram : M.R. SHAH*, B.V. NAGARATHNA

    becomes:

        [
            "M.R. SHAH",
            "B.V. NAGARATHNA"
        ]
    """

    if not coram_text:
        return []

    # Remove "Coram :"
    coram_text = re.sub(
        r"^\s*Coram\s*:\s*",
        "",
        coram_text,
        flags=re.IGNORECASE
    )

    # Remove author marker (*)
    coram_text = coram_text.replace("*", "")

    judges = []

    for judge in coram_text.split(","):

        judge = clean_text(judge)

        if judge:
            judges.append(judge)

    return judges


# =============================================================
# Case title
# =============================================================

def extract_case_title(soup):
    """
    Extract case title from the <strong> element containing
    'versus'.
    """

    for tag in soup.find_all("strong"):

        text = clean_text(
            tag.get_text(" ", strip=True)
        )

        if not text:
            continue

        if re.search(
            r"\bversus\b",
            text,
            re.IGNORECASE
        ):
            return text

    return None


# =============================================================
# Coram / Judges
# =============================================================

def extract_coram_and_issue(soup):
    """
    Extract judges and issue/summary from the section:

        <strong>
            Coram : ...
        </strong>
        <br>

        Issue / summary

        <br>

        <strong class="caseDetailsTD">
            Decision Date : ...
        </strong>

    Works with both:

        Issue for Consideration ...

    and:

        Appeal: Murder case ...
    """

    judges = []
    issue = None

    # ---------------------------------------------------------
    # Find Coram tag
    # ---------------------------------------------------------

    coram_tag = None

    for tag in soup.find_all("strong"):

        text = clean_text(
            tag.get_text(" ", strip=True)
        )

        if not text:
            continue

        if re.search(
            r"\bCoram\s*:",
            text,
            re.IGNORECASE
        ):
            coram_tag = tag
            break

    if not coram_tag:
        return judges, issue

    # ---------------------------------------------------------
    # Extract judges
    # ---------------------------------------------------------

    coram_text = clean_text(
        coram_tag.get_text(
            " ",
            strip=True
        )
    )

    judges = extract_judges(coram_text)

    # ---------------------------------------------------------
    # Extract issue / summary
    # ---------------------------------------------------------

    issue_parts = []

    # The next sibling should normally be <br>
    current = coram_tag.next_sibling

    # Move past the <br> following Coram
    if (
        current is not None
        and getattr(current, "name", None) == "br"
    ):
        current = current.next_sibling

    while current is not None:

        tag_name = getattr(
            current,
            "name",
            None
        )

        # -----------------------------------------------------
        # Stop at the next <br>
        #
        # This is the normal end of the issue/summary.
        # -----------------------------------------------------

        if tag_name == "br":
            break

        # -----------------------------------------------------
        # Defensive stop:
        # case details section
        # -----------------------------------------------------

        if (
            tag_name == "strong"
            and "caseDetailsTD" in (
                current.get("class") or []
            )
        ):
            break

        # -----------------------------------------------------
        # Extract text
        # -----------------------------------------------------

        if hasattr(current, "get_text"):

            text = current.get_text(
                " ",
                strip=True
            )

        else:

            text = str(current)

        text = clean_text(text)

        if text:
            issue_parts.append(text)

        current = current.next_sibling

    issue = clean_text(
        " ".join(issue_parts)
    )

    if issue:

        # Remove heading if present
        issue = re.sub(
            r"^\s*Issue\s+for\s+Consideration\s*",
            "",
            issue,
            flags=re.IGNORECASE
        )

        issue = clean_text(issue)

    return judges, issue


# =============================================================
# Case details
# =============================================================

def extract_case_details(soup):
    """
    Extract:

        Decision Date
        Case Number
        Disposal Nature
        Bench Strength
    """

    result = {
        "decision_date": None,
        "case_number": None,
        "disposal_nature": None,
        "bench_strength": None,
    }

    # ---------------------------------------------------------
    # Find caseDetailsTD
    # ---------------------------------------------------------

    case_details = soup.select_one(
        "strong.caseDetailsTD"
    )

    if not case_details:
        return result

    text = clean_text(
        case_details.get_text(
            " ",
            strip=True
        )
    )

    if not text:
        return result

    # ---------------------------------------------------------
    # Decision Date
    # ---------------------------------------------------------

    date_match = re.search(
        r"Decision\s*Date\s*:\s*"
        r"(\d{2}-\d{2}-\d{4})",
        text,
        re.IGNORECASE
    )

    if date_match:

        result["decision_date"] = normalize_date(
            date_match.group(1)
        )

    # ---------------------------------------------------------
    # Case Number
    #
    # Everything between:
    #
    # Case No :
    #
    # and:
    #
    # Disposal Nature :
    # ---------------------------------------------------------

    case_match = re.search(
        r"Case\s*No\s*:\s*"
        r"(.*?)"
        r"\s*\|\s*"
        r"Disposal\s+Nature\s*:",
        text,
        re.IGNORECASE
    )

    if case_match:

        result["case_number"] = clean_text(
            case_match.group(1)
        )

    # ---------------------------------------------------------
    # Disposal Nature
    #
    # Everything between:
    #
    # Disposal Nature :
    #
    # and:
    #
    # Bench :
    # ---------------------------------------------------------

    disposal_match = re.search(
        r"Disposal\s+Nature\s*:\s*"
        r"(.*?)"
        r"\s*\|\s*"
        r"Bench\s*:",
        text,
        re.IGNORECASE
    )

    if disposal_match:

        result["disposal_nature"] = clean_text(
            disposal_match.group(1)
        )

    # ---------------------------------------------------------
    # Bench
    # ---------------------------------------------------------

    bench_match = re.search(
        r"Bench\s*:\s*"
        r"(\d+)\s*Judges?",
        text,
        re.IGNORECASE
    )

    if bench_match:

        result["bench_strength"] = int(
            bench_match.group(1)
        )

    return result


# =============================================================
# Languages
# =============================================================

def extract_languages(soup):
    """
    Extract languages from the language <select>.
    """

    languages = []

    language_select = soup.find(
        "select",
        {
            "id": re.compile(
                r"language",
                re.IGNORECASE
            )
        }
    )

    if not language_select:
        return ["English"]

    for option in language_select.find_all(
        "option"
    ):

        language = clean_text(
            option.get_text(
                " ",
                strip=True
            )
        )

        if language:
            languages.append(language)

    if not languages:
        languages.append("English")

    return languages


# =============================================================
# Main metadata extraction
# =============================================================

def extract_metadata(file_path):
    """
    Extract all metadata from one JSON file.
    """

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    raw_html = data.get(
        "raw_html",
        ""
    )

    if not raw_html:
        return None

    soup = BeautifulSoup(
        raw_html,
        "lxml"
    )

    # ---------------------------------------------------------
    # Basic metadata from JSON
    # ---------------------------------------------------------

    metadata = {

        "judgment_id": None,

        "year": data.get(
            "citation_year",
            2023
        ),

        "case_title": None,

        "decision_date": None,

        "case_number": None,

        "citation": None,

        "neutral_citation": data.get(
            "nc_display"
        ),

        "cnr": None,

        "judges": [],

        "bench_strength": None,

        "disposal_nature": None,

        "languages": [],

        "issue": None,

        "source_path": data.get(
            "path"
        ),

        "scraped_at": data.get(
            "scraped_at"
        ),
    }

    # =========================================================
    # Case title
    # =========================================================

    metadata["case_title"] = (
        extract_case_title(soup)
    )

    # =========================================================
    # Citation
    # =========================================================

    escr_text = soup.select_one(
        ".escrText"
    )

    if escr_text:

        metadata["citation"] = clean_text(
            escr_text.get_text()
        )

    # =========================================================
    # Neutral citation
    #
    # IMPORTANT:
    #
    # We prefer the JSON's nc_display because it is already
    # provided separately from raw_html.
    # =========================================================

    if not metadata["neutral_citation"]:

        nc_display = soup.select_one(
            ".ncDisplay"
        )

        if nc_display:

            metadata["neutral_citation"] = (
                clean_text(
                    nc_display.get_text()
                )
            )

    # =========================================================
    # CNR
    # =========================================================

    cnr = soup.find(
        "input",
        {
            "id": "cnr"
        }
    )

    if cnr:

        metadata["cnr"] = cnr.get(
            "value"
        )

    # =========================================================
    # Coram + Issue
    # =========================================================

    (
        metadata["judges"],
        metadata["issue"]
    ) = extract_coram_and_issue(
        soup
    )

    # =========================================================
    # Case details
    # =========================================================

    case_details = extract_case_details(
        soup
    )

    metadata.update(
        case_details
    )

    # =========================================================
    # Languages
    # =========================================================

    metadata["languages"] = (
        extract_languages(soup)
    )

    # =========================================================
    # Judgment ID
    #
    # Example:
    #
    # 2025 INSC 18
    #
    # becomes:
    #
    # 2025INSC18
    # =========================================================

    if metadata["neutral_citation"]:

        judgment_id = re.sub(
            r"[^A-Za-z0-9]",
            "",
            metadata["neutral_citation"]
        )

        metadata["judgment_id"] = (
            judgment_id
        )

    # ---------------------------------------------------------
    # Fallback
    # ---------------------------------------------------------

    if not metadata["judgment_id"]:

        metadata["judgment_id"] = (
            file_path.stem
        )

    return metadata


# =============================================================
# Main
# =============================================================

def main(year: int):

    input_dir = Path("data/metadata") / str(year)
    output_file = Path(f"data/judgments_metadata_{year}.json")

    # ---------------------------------------------------------
    # Find all JSON files
    # ---------------------------------------------------------

    json_files = list(
        input_dir.rglob("*.json")
    )

    print(
        f"Found {len(json_files)} JSON files."
    )

    results = []
    failed = []

    # ---------------------------------------------------------
    # Process files
    # ---------------------------------------------------------

    for index, file_path in enumerate(
        json_files,
        start=1
    ):

        try:

            metadata = extract_metadata(
                file_path
            )

            if metadata:

                results.append(
                    metadata
                )

            if index % 100 == 0:

                print(
                    f"Processed "
                    f"{index}/{len(json_files)}"
                )

        except Exception as e:

            failed.append(
                {
                    "file": str(file_path),
                    "error": str(e),
                }
            )

            print(
                f"\nERROR: {file_path}"
            )

            print(
                f"       {e}"
            )

    # =========================================================
    # Save metadata
    # =========================================================

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )

    # =========================================================
    # Statistics
    # =========================================================

    print("\n" + "=" * 60)

    print(
        "Extraction complete"
    )

    print("=" * 60)

    print(
        f"JSON files found     : "
        f"{len(json_files)}"
    )

    print(
        f"Successfully parsed  : "
        f"{len(results)}"
    )

    print(
        f"Failed               : "
        f"{len(failed)}"
    )

    # =========================================================
    # Missing field report
    # =========================================================

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
            f"  {field:<20} "
            f"{missing}"
        )

    # =========================================================
    # Save failed files
    # =========================================================

    if failed:

        with open(
            ERROR_FILE,
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
            f"\nFailed files written to:"
            f"\n{ERROR_FILE}"
        )

    print(
        f"\nOutput:"
        f"\n{output_file}"
    )


# =============================================================
# Entry point
# =============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract judgment metadata for a specified year."
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Year of metadata to process (for example, 2023).",
    )
    args = parser.parse_args()
    main(args.year)