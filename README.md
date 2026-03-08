# BD Library Manager

A small **vibe coding experiment** to automate comic archive preparation.

It was coded using Gemini Copilot and other free access AI.
In conjuncture with OpenCode and worktrunk to guide more easily the agents.

## What this project does

This project helps you process folders of comic pages (JPEG) into clean comic archives:

- Converts JPEG pages to JPEG XL (`.jxl`) using `cjxl`
- Generates `ComicInfo.xml` metadata
- Optionally enriches metadata from the Comic Vine API
- Builds `.cbz` archives ready for comic readers
- Supports batch processing for multiple folders

## Main scripts

- `batch_process.py`: end-to-end batch workflow (convert + metadata + CBZ)
- `convert_jpeg_to_jxl.py`: JPEG → JXL conversion
- `generate_comicinfo.py`: standalone ComicInfo.xml generator
- `create_cbz.py`: build CBZ archives from image folders
- `comicvine_client.py`: Comic Vine API integration and metadata mapping
- `config.py`: local config and cache (`~/.bd_library_manager/config.json`)

## Requirements

- Python 3.10+
- `cjxl` installed and available in `PATH`
- Python packages:
  - `requests`
  - `Pillow`
  - `jxlpy`

Install Python dependencies:

```bash
pip install requests Pillow jxlpy
```

## Quick start

### 1) Convert one folder of JPEGs to JXL

```bash
python convert_jpeg_to_jxl.py /path/to/jpeg_folder /path/to/output_jxl -t 4
```

### 2) Generate ComicInfo.xml

```bash
python generate_comicinfo.py /path/to/output --series "Series Name" --number 1 --title "Issue Title"
```

### 3) Create a CBZ

```bash
python create_cbz.py /path/to/output_jxl /path/to/output.cbz
```

### 4) Run the full batch workflow

```bash
python batch_process.py /path/to/library_root
```

On first use of Comic Vine features, the script prompts for an API key and stores it locally.

## Notes

- The expected folder naming convention in batch mode is close to: `Series Name/01 - Issue Title`
- Comic Vine matching may require manual confirmation for ambiguous series names
- Cache and API key are stored in `~/.bd_library_manager/`
