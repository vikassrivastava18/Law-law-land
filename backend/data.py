from datasets import load_dataset
import base64
from pathlib import Path

dataset = load_dataset(
    "CUAD_v1_Contract_Understanding_PDF"
)

output_dir = Path("data/contracts")
output_dir.mkdir(parents=True, exist_ok=True)

for row in dataset["train"]:
    filename = row["file_name"]
    pdf_bytes = base64.b64decode(row["pdf_bytes_base64"])

    output_path = output_dir / filename
    output_path.write_bytes(pdf_bytes)

print(f"Extracted {len(dataset['train'])} PDFs")