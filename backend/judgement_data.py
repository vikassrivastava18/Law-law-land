import json
import tarfile
import requests
from pathlib import Path


YEAR = 2022
BASE_URL = (
    "https://indian-supreme-court-judgments.s3.ap-south-1.amazonaws.com"
)

DATA_DIR = Path("data")
PDF_DIR = DATA_DIR / "pdfs" / str(YEAR)
METADATA_DIR = DATA_DIR / "metadata" / str(YEAR)

PDF_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)


def download_file(url, output_path):
    """Download a file with streaming."""

    print(f"Downloading: {url}")

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    print(f"Saved: {output_path}")


def download_metadata():
    """Download 2025 metadata archive."""

    url = (
        f"{BASE_URL}/metadata/tar/"
        f"year={YEAR}/metadata.tar"
    )

    tar_path = DATA_DIR / f"metadata_{YEAR}.tar"

    download_file(url, tar_path)

    print("Extracting metadata...")

    with tarfile.open(tar_path, "r") as tar:
        tar.extractall(METADATA_DIR)

    print("Metadata extraction complete.")


def download_english_judgments():
    """Download 2025 English judgment archive."""

    url = (
        f"{BASE_URL}/data/tar/"
        f"year={YEAR}/english/english.tar"
    )

    tar_path = DATA_DIR / f"judgments_{YEAR}_english.tar"

    download_file(url, tar_path)

    print("Extracting judgments...")

    with tarfile.open(tar_path, "r") as tar:
        tar.extractall(PDF_DIR)

    print("Judgment extraction complete.")


def main():
    print(f"Downloading Indian Supreme Court data for {YEAR}")

    download_metadata()
    download_english_judgments()

    print("\nDone!")
    print(f"PDFs:      {PDF_DIR}")
    print(f"Metadata:  {METADATA_DIR}")


if __name__ == "__main__":
    main()