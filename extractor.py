import fitz  # PyMuPDF  

def load_pdf(file_path: str) -> fitz.Document:
    """
    Load a PDF document using PyMuPDF.
    
    Args:
        file_path (str): Path to the PDF file.
        
    Returns:
        fitz.Document: The loaded PDF document object.
    """
    try:
        doc = fitz.open(file_path)
        return doc
    except Exception as e:
        raise RuntimeError(f"Failed to load PDF: {file_path}. Error: {str(e)}")
    

################################

def extract_lines(doc: fitz.Document) -> list:
    """
    Extracts text lines from a PDF document using PyMuPDF, preserving visual layout
    and returning font size, font name, position, and page number per line.

    Returns:
        List[Dict]: Each dict contains: text, font_size, font_name, x0, y0, page
    """
    lines_data = []

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                # Filter empty or whitespace-only spans
                clean_spans = [s for s in spans if s["text"].strip()]
                if not clean_spans:
                    continue

                # Construct full line text from clean spans
                line_text = " ".join(span["text"].strip() for span in clean_spans)
                if not line_text:
                    continue

                # Use average font size across spans
                avg_font_size = sum(span["size"] for span in clean_spans) / len(clean_spans)

                # Dominant font name (if consistent, otherwise take first)
                font_name = clean_spans[0]["font"]

                # Use top-left of first span as reference position
                x0, y0 = clean_spans[0]["origin"]

                lines_data.append({
                    "text": line_text.strip(),
                    "font_size": round(avg_font_size, 2),
                    "font_name": font_name,
                    "x0": x0,
                    "y0": y0,
                    "page": page_num
                })

    return lines_data


#################################



def extract_blocks(doc: fitz.Document) -> list:
    """
    Extracts text blocks from the PDF. Each block is typically a paragraph
    or a heading. We extract average font size, representative font,
    and position per block.

    Returns:
        List[Dict]: Each block contains:
            - text
            - font_size (average of spans)
            - font_name (from first span)
            - x0, y0 (top-left corner of first span)
            - page (1-based)
    """
    blocks_data = []

    for page_num, page in enumerate(doc, start=1):
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])

        for block in blocks:
            if "lines" not in block or not block["lines"]:
                continue

            block_text = []
            font_sizes = []
            first_span = None

            for line in block["lines"]:
                for span in line["spans"]:
                    if not span["text"].strip():
                        continue
                    block_text.append(span["text"].strip())
                    font_sizes.append(span["size"])
                    if first_span is None:
                        first_span = span

            if not block_text or not font_sizes or not first_span:
                continue

            # Construct block entry
            text = " ".join(block_text).strip()
            avg_font_size = sum(font_sizes) / len(font_sizes)
            x0, y0 = first_span["origin"]
            font_name = first_span["font"]

            blocks_data.append({
                "text": text,
                "font_size": round(avg_font_size, 2),
                "font_name": font_name,
                "x0": x0,
                "y0": y0,
                "page": page_num
            })

    return blocks_data






from collections import Counter

def rank_font_sizes(lines: list) -> dict:
    """
    Analyze font sizes across all lines and assign heading levels
    to the top 3 largest font sizes.

    Args:
        lines (List[Dict]): List of line-level text metadata.

    Returns:
        Dict[float, str]: Mapping from font size to heading level (e.g. 18.0 -> "H1")
    """
    # Count font size frequencies
    font_sizes = [round(line["font_size"], 2) for line in lines]
    font_counter = Counter(font_sizes)

    # Sort font sizes in descending order (largest first)
    sorted_sizes = sorted(font_counter.keys(), reverse=True)

    # Map top 3 font sizes to H1, H2, H3
    level_map = {}
    heading_levels = ["H1", "H2", "H3"]

    for i, size in enumerate(sorted_sizes[:3]):
        level_map[size] = heading_levels[i]

    return level_map


def assign_heading_levels(lines: list, font_level_map: dict) -> list:
    """
    Assign heading levels (H1, H2, H3) to lines based on font size.

    Args:
        lines (List[Dict]): Extracted text lines.
        font_level_map (Dict[float, str]): Font size → heading level map.

    Returns:
        List[Dict]: Lines with assigned heading levels (if matched).
    """
    labeled_lines = []

    for line in lines:
        size_key = round(line["font_size"], 2)
        if size_key in font_level_map:
            labeled_lines.append({
                "text": line["text"],
                "font_size": size_key,
                "font_name": line["font_name"],
                "x0": line["x0"],
                "y0": line["y0"],
                "page": line["page"],
                "level": font_level_map[size_key]
            })

    return labeled_lines

def get_title_from_metadata(doc: fitz.Document) -> str | None:
    """
    Attempts to extract the title from the PDF's metadata.

    Args:
        doc (fitz.Document): The loaded PDF document.

    Returns:
        Optional[str]: The title if found, else None.
    """
    title = doc.metadata.get("title", "").strip()
    return title if title else None



def infer_title_from_lines(lines: list, page_width: float = 595.2) -> str:
    """
    Infer document title based on visual heuristics from the first page lines.

    Args:
        lines (List[Dict]): All extracted lines from the document.
        page_width (float): Width of the page (default is A4 portrait in points).

    Returns:
        str: The inferred title text.
    """
    # Filter lines from only page 1
    first_page_lines = [line for line in lines if line["page"] == 1]

    # If nothing on page 1, fallback to top 10 lines from whole doc
    if not first_page_lines:
        first_page_lines = lines[:10]

    # Step 1: Find the max font size on page 1
    max_size = max(line["font_size"] for line in first_page_lines)

    # Step 2: Filter candidates with same font size and short text
    candidates = [
        line for line in first_page_lines
        if round(line["font_size"], 2) == round(max_size, 2)
        and len(line["text"]) <= 100
    ]

    # Step 3: Rank candidates by y-position (topmost wins)
    candidates.sort(key=lambda l: (l["y0"], abs((l["x0"] + 10) - page_width / 2)))  # prefer centered

    if candidates:
        return candidates[0]["text"].strip()

    # Fallback: topmost short line on first page
    top_line = sorted(first_page_lines, key=lambda l: l["y0"])[0]
    return top_line["text"].strip()


from collections import Counter

def filter_headings(labeled_lines: list) -> list:
    """
    Filter and clean heading lines based on heuristics such as length,
    position, and repetition to remove false positives like footers.

    Args:
        labeled_lines (List[Dict]): Lines already tagged with H1/H2/H3.

    Returns:
        List[Dict]: Filtered list of heading lines.
    """
    # Count occurrences of each text to detect repeated lines
    text_counter = Counter(line["text"] for line in labeled_lines)

    filtered = []

    for line in labeled_lines:
        text = line["text"].strip()

        # 1. Skip lines that are too long
        if len(text) > 120:
            continue

        # 2. Skip very frequently repeated lines (likely boilerplate)
        if text_counter[text] > 2:
            continue

        # 3. Skip lines very low on the page (possible footer)
        if line["y0"] > 750:  # depends on page height, adjust if needed
            continue

        # All good — include this heading
        filtered.append({
            "level": line["level"],
            "text": text,
            "page": line["page"]
        })

    return filtered



def build_outline_json(title: str, headings: list) -> dict:
    """
    Constructs the final outline JSON structure from the title and headings.

    Args:
        title (str): The inferred or metadata title.
        headings (List[Dict]): Filtered list of headings.

    Returns:
        Dict: JSON-serializable dictionary with "title" and "outline".
    """
    return {
        "title": title,
        "outline": [
            {
                "level": heading["level"],
                "text": heading["text"],
                "page": heading["page"]
            }
            for heading in headings
        ]
    }


import os
import json

def write_output_json(data: dict, output_path: str) -> None:
    """
    Writes the JSON data to a file.

    Args:
        data (dict): JSON data to write.
        output_path (str): Full path to output .json file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


import os

def process_pdf(file_path: str, output_dir: str) -> None:
    """
    Processes a single PDF file using block-based extraction and writes
    the structured heading outline to a JSON file.

    Args:
        file_path (str): Path to the input PDF.
        output_dir (str): Path to the output directory for JSON.
    """
    file_name = os.path.basename(file_path)
    print(f"\n🚀 Starting: {file_name}")

    try:
        doc = load_pdf(file_path)
        print("📄 Loaded PDF successfully.")

        blocks = extract_blocks(doc)
        print(f"📦 Extracted {len(blocks)} text blocks.")

        if not blocks:
            print("⚠️ No blocks found — skipping file.")
            return

        font_level_map = rank_font_sizes(blocks)
        print("🔤 Font size → heading level map:", font_level_map)

        if not font_level_map:
            print("⚠️ Could not rank font sizes — skipping heading detection.")
            return

        labeled_blocks = assign_heading_levels(blocks, font_level_map)
        print(f"🏷️ {len(labeled_blocks)} blocks assigned H1–H3.")

        if not labeled_blocks:
            print("⚠️ No headings found — skipping.")
            return

        title = get_title_from_metadata(doc)
        if title:
            print(f"📚 Title from metadata: {title}")
        else:
            title = infer_title_from_lines(blocks)  # still uses same structure
            print(f"🧠 Title inferred: {title}")

        clean_headings = filter_headings(labeled_blocks)
        print(f"✅ {len(clean_headings)} headings retained after filtering.")

        if not clean_headings:
            print("⚠️ All headings filtered out — skipping.")
            return

        outline_data = build_outline_json(title, clean_headings)

        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.splitext(file_name)[0] + ".json"
        output_path = os.path.join(output_dir, output_filename)
        write_output_json(outline_data, output_path)

        print(f"💾 Output saved to: {output_path}")

    except Exception as e:
        print(f"❌ Error processing {file_name}: {e}")





import os

def main(input_dir: str = "app/input", output_dir: str = "app/output") -> None:
    """
    Main entry point for batch processing all PDFs in the input directory.
    """
    print("📁 Looking for PDFs in:", os.path.abspath(input_dir))

    if not os.path.exists(input_dir):
        print(f"❌ Input directory not found: {input_dir}")
        return

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("⚠️ No PDF files found in the input directory.")
        return

    print(f"📄 Found {len(pdf_files)} PDF file(s):", pdf_files)
    os.makedirs(output_dir, exist_ok=True)

    for file_name in pdf_files:
        file_path = os.path.join(input_dir, file_name)
        try:
            process_pdf(file_path, output_dir)
        except Exception as e:
            print(f"❌ Failed to process {file_name}: {e}")

    print("✅ All processing done.")



if __name__ == "__main__":
    main()