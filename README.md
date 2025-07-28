# PDF Heading Extractor (1a)

This project extracts structured outlines (Title, H1, H2, H3 headings) from PDF documents without using LLMs or external APIs.

### Overview

- Input: PDF files
- Output: JSON files with the following structure:

```json
{
  "title": "Document Title",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "Background", "page": 2 },
    { "level": "H3", "text": "Details", "page": 3 }
  ]
}
```

---

### Folder Structure

```
project_root/
├── extractor.py               # Main Python script
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container build file
├── app/
│   ├── input/                 # Place your input PDFs here
│   └── output/                # JSON output will appear here
```

---

### 🐳 How to Run (via Docker)

1. Build the Docker image:

```bash
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
```

2. Run the container:

```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  mysolutionname:somerandomidentifier
```

✅ Your container should:

- Automatically process all PDFs from /app/input
- Generate a corresponding filename.json in /app/output for each filename.pdf

---

### How to Run (Locally)

1. Install Python 3.10+
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add your PDFs to app/input
4. Run the script:

```bash
python extractor.py
```

5. Find results in app/output/

---

### 📦 Model and Libraries Used

- ❌ No LLMs, ML models, or external APIs used
- ✅ Fully rule-based, font- and layout-driven approach

Libraries:

- Python 3.10+
- PyMuPDF (fitz) → for PDF text and font extraction
- os, json → built-in Python utilities

This ensures the container remains lightweight, offline, and fast.

---

## 🔍 Challenge Approach & Learnings

This submission was built for the Adobe India Hackathon – Connecting the Dots (Round 1A). The goal was to extract structured outlines (Title, H1–H3) from PDF files.

### 🌟 Intended Approach

Originally, we aimed to:

- Parse PDF blocks with visual features (font size, boldness, position)
- Label blocks using an AI model (title, h1, h2, h3, …)
- Build a labeled dataset by auto-labeling with Groq's LLaMA3 and Ollama
- Train a custom document-structure classifier
- Convert labeled data to the required JSON outline format

We created:

- A modular PDF parser with over 30 block-level features
- A robust AI-labeling engine supporting Groq API and local Ollama models
- A CLI and metadata system for tracking labeling status
- Retry logic, and partial relabeling recovery
- Logs and outputs structured cleanly into a reproducible folder

### ❌ Why It Didn't Fully Work

Due to lack of pre-labeled data:

- We couldn't label enough PDFs to train a model from scratch
- LLM-based labeling showed inconsistencies across batches
- Some block-level structures were too ambiguous without human verification

So, we fell back to a simpler rule-based version, which is what this Dockerized submission runs. It uses font-size heuristics, position, and grouping to infer headings from blocks without any LLM or API dependency.

### ✅ What We Did Deliver

- Fully working rule-based extractor
- LLM-based labeling pipeline (modular and testable)
- Logs, retries, metadata tracking for relabeling
- A flexible base that can be extended to train a model in future rounds

---

### ✅ Current Features

- Rule-based extraction of Title, H1–H3
- Block-level text grouping (not line-based)
- Font-size ranking to infer heading hierarchy
- Full Dockerized version (submission ready)

---

### 📘 Closing Thought

This submission might not fully demonstrate our AI-labeling pipeline yet, but we’re proud of how far we went in designing a complete system, and we’d love to build on it further if given the chance.

### ✅ Current Features

- Rule-based extraction of Title, H1–H3
- Block-level text grouping (not line-based)
- Font-size ranking to infer heading hierarchy
- Full Dockerized version (submission ready)

---
