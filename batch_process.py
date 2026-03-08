#!/usr/bin/env python3
"""
This script automates the process of converting a batch of comic book folders 
(containing JPEG images) into compressed CBZ archives with JXL-encoded images.

It performs the following steps for each folder:
1. Converts all JPEG images to JPEG XL (JXL) format.
2. Generates a ComicInfo.xml metadata file.
3. Creates a CBZ archive containing the JXL images and metadata file.
4. Optionally cleans up the intermediate JXL files.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional

from config import get_api_key, set_api_key, get_cached_series_info, cache_series_info, get_cached_series
from comicvine_client import ComicVineClient, map_to_comicinfo, find_issue_by_number


def setup_comicvine() -> Optional[ComicVineClient]:
    """Setup Comic Vine client, prompt for API key if needed."""
    api_key = get_api_key()
    
    if not api_key:
        print("\n=== Comic Vine API Setup ===")
        print("You need a free API key from https://comicvine.gamespot.com/api/")
        api_key = input("Enter your Comic Vine API key: ").strip()
        if api_key:
            set_api_key(api_key)
            print("API key saved!")
        else:
            print("No API key provided, Comic Vine lookup disabled.")
            return None
    
    try:
        return ComicVineClient(api_key)
    except Exception as e:
        print(f"Failed to initialize Comic Vine client: {e}")
        return None


def handle_not_found(series_name: str, number: str) -> str:
    """Prompt user for action when comic not found in Comic Vine."""
    print(f"\n  Comic not found in Comic Vine: {series_name} #{number}")
    print(f"    1. Skip (use folder metadata only)")
    print(f"    2. Enter summary manually")
    print(f"    3. Use partial data (year, publisher only)")
    
    while True:
        choice = input("  Choice [1]: ").strip() or "1"
        
        if choice == "1":
            return "skip"
        elif choice == "2":
            return "manual"
        elif choice == "3":
            return "partial"
        print("  Invalid choice. Enter 1, 2, or 3.")


def confirm_series(client: ComicVineClient, series_name: str) -> Optional[dict]:
    """Prompt user to confirm the correct series from search results."""
    print(f"\n  Searching Comic Vine for: {series_name}")
    results = client.search_series(series_name, limit=10)
    
    if not results:
        return None
    
    print(f"  Found {len(results)} results:")
    for i, r in enumerate(results):
        publisher = f" ({r['publisher']})" if r.get("publisher") else ""
        year = f" {r.get('start_year', '')}" if r.get("start_year") else ""
        issues = f" [{r.get('count_of_issues', '?')} issues]" if r.get("count_of_issues") else ""
        print(f"    {i+1}. {r['name']}{year}{publisher}{issues}")
    
    print(f"    0. Skip (don't use Comic Vine)")
    print(f"    s. Skip all remaining (don't ask for this series again)")
    
    while True:
        choice = input(f"  Select series [1-{len(results)}]: ").strip().lower()
        
        if choice == "0":
            return None
        if choice == "s":
            return {"skip_all": True}
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                selected = results[idx]
                print(f"  Selected: {selected['name']}")
                return selected
        except ValueError:
            pass
        print(f"  Invalid choice. Enter a number 1-{len(results)} or 0 to skip.")


def run_cmd(cmd):
    """
    Executes a shell command and prints STDERR if it fails.

    Args:
        cmd (str): The command to execute.

    Returns:
        bool: True if the command succeeded, False otherwise.
    """
    result = subprocess.run(cmd, shell=True, capture_output=True)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr.decode()}")
    return result.returncode == 0


def process_folder(folder: Path, quality: int, lossless: bool, keep_jxl: bool, output_folder: Optional[Path] = None, threads: int = 4, comicvine_client: Optional[ComicVineClient] = None, series_cache: Optional[dict] = None):
    """
    Processes a single folder of JPEG images to create a JXL-based CBZ archive.

    Args:
        folder (Path): The path to the folder to process.
        quality (int): The JXL encoding quality (1-100).
        lossless (bool): Whether to use lossless JXL encoding.
        keep_jxl (bool): Whether to keep the intermediate JXL folder.
        output_folder (Path, optional): The folder to save the CBZ file in. Defaults to the parent of the input folder.
        threads (int): The number of threads to use for JXL conversion.
        comicvine_client: Optional Comic Vine client for metadata enrichment.
        series_cache: Cached series data for automatic lookup.

    Returns:
        bool: True if processing was successful, False otherwise.
    """
    import re
    
    folder = Path(folder)
    print(f"\n{'='*50}")
    print(f"Processing: {folder.name}")
    print(f"{'='*50}")
    
    # Find all JPEG files in the folder
    jpeg_files = list(folder.glob('*.jpg')) + list(folder.glob('*.jpeg'))
    jpeg_files += list(folder.glob('*.JPG')) + list(folder.glob('*.JPEG'))
    
    if not jpeg_files:
        print(f"  No JPEG files found, skipping...")
        return False
    
    # Extract series, tome/number, and title from the directory structure
    # Expected format: serie_name/tome_number - tome_name
    series_name = folder.parent.name
    dir_name_match = re.match(r'(\d+)\s*-\s*(.+)', folder.name)
    if dir_name_match:
        number = str(int(dir_name_match.group(1)))
        title = dir_name_match.group(2).strip()
    else:
        number = None
        title = None
    
    # Comic Vine metadata lookup
    cv_metadata = {}
    if comicvine_client and series_cache is not None:
        # Check if we have a cached series
        if series_name in series_cache:
            cached = series_cache[series_name]
            if cached.get("skip"):
                print(f"  Skipping Comic Vine lookup (marked as skip)")
            else:
                print(f"  Using cached series: {cached['name']}")
                # Fetch issue by number
                issues = cached.get("issues", [])
                issue = find_issue_by_number(issues, number) if issues and number is not None else None
                
                if issue:
                    print(f"  Found issue #{number}: {issue.get('name', 'N/A')}")
                    issue_data = comicvine_client.get_issue(issue["id"])
                    cv_metadata = map_to_comicinfo(issue_data)
                else:
                    print(f"  Issue #{number} not found in series")
        else:
            # Need to confirm series first
            print(f"  Series not cached, searching Comic Vine...")
            series_info = confirm_series(comicvine_client, series_name)
            
            if series_info and series_info.get("skip_all"):
                series_cache[series_name] = {"skip": True, "name": series_name}
                print(f"  Skipping Comic Vine for series: {series_name}")
            elif series_info:
                # Fetch all issues for this series
                print(f"  Fetching issues for {series_info['name']}...")
                volume_id = series_info["id"]
                issues = comicvine_client.get_volume_issues(volume_id)
                print(f"  Found {len(issues)} issues")
                
                # Cache the series
                series_cache[series_name] = {
                    "id": volume_id,
                    "name": series_info["name"],
                    "issues": issues
                }
                
                # Find the issue
                issue = find_issue_by_number(issues, number) if number is not None else None
                if issue:
                    print(f"  Found issue #{number}: {issue.get('name', 'N/A')}")
                    issue_data = comicvine_client.get_issue(issue["id"])
                    cv_metadata = map_to_comicinfo(issue_data)
                else:
                    print(f"  Issue #{number} not found in series")
    
    # Create a temporary folder for JXL files
    jxl_folder = folder.parent / f"{folder.name}_jxl"
    
    # Convert JPEGs to JXL
    print(f"  Converting {len(jpeg_files)} JPEGs to JXL...")
    lossless_flag = "-l" if lossless else ""
    cmd = f'python convert_jpeg_to_jxl.py "{folder}" "{jxl_folder}" -q {quality} {lossless_flag} -t {threads}'
    if not run_cmd(cmd):
        print("  ERROR: Conversion failed")
        return False
    
    # Generate ComicInfo.xml metadata
    print(f"  Generating ComicInfo.xml...")
    series_arg = f'--series "{series_name}"' if series_name else ""
    number_arg = f'--number {number}' if number else ""
    title_arg = f'--title "{title}"' if title else ""
    
    # Add Comic Vine metadata as arguments
    cv_args = ""
    if cv_metadata:
        if cv_metadata.get("summary"):
            cv_args += f' --summary "{cv_metadata["summary"]}"'
        if cv_metadata.get("writer"):
            cv_args += f' --writer "{cv_metadata["writer"]}"'
        if cv_metadata.get("artist"):
            cv_args += f' --artist "{cv_metadata["artist"]}"'
        if cv_metadata.get("inker"):
            cv_args += f' --inker "{cv_metadata["inker"]}"'
        if cv_metadata.get("colorist"):
            cv_args += f' --colorist "{cv_metadata["colorist"]}"'
        if cv_metadata.get("letterer"):
            cv_args += f' --letterer "{cv_metadata["letterer"]}"'
        if cv_metadata.get("cover_artist"):
            cv_args += f' --cover-artist "{cv_metadata["cover_artist"]}"'
        if cv_metadata.get("publisher"):
            cv_args += f' --publisher "{cv_metadata["publisher"]}"'
        if cv_metadata.get("year"):
            cv_args += f' --year {cv_metadata["year"]}'
        if cv_metadata.get("month"):
            cv_args += f' --month {cv_metadata["month"]}'
        if cv_metadata.get("genre"):
            cv_args += f' --genre "{cv_metadata["genre"]}"'
        if cv_metadata.get("notes"):
            cv_args += f' --notes "{cv_metadata["notes"]}"'
    
    cmd = f'python generate_comicinfo.py "{jxl_folder}" {series_arg} {number_arg} {title_arg} {cv_args} --images "{jxl_folder}"'
    if not run_cmd(cmd):
        print("  ERROR: Metadata generation failed")
        return False
    
    # Create the CBZ archive
    print(f"  Creating CBZ archive...")
    if output_folder:
        cbz_path = output_folder / f"{folder.name}.cbz"
    else:
        cbz_path = folder.parent / f"{folder.name}.cbz"
    cmd = f'python create_cbz.py "{jxl_folder}" "{cbz_path}"'
    if not run_cmd(cmd):
        print("  ERROR: CBZ creation failed")
        return False
    
    # Clean up the temporary JXL folder if requested
    if not keep_jxl:
        print(f"  Cleaning up JXL folder...")
        import shutil
        shutil.rmtree(jxl_folder)
    
    print(f"  Done: {cbz_path.name}")
    return True


def main():
    """
    Main function to parse command-line arguments and process folders.
    """
    parser = argparse.ArgumentParser(description='Batch process comic folders')
    parser.add_argument('input', help='Input folder or file pattern (e.g., ./comics or "./comics/*")')
    parser.add_argument('-q', '--quality', type=int, default=90, help='JXL quality (1-100)')
    parser.add_argument('-l', '--lossless', action='store_true', help='Use lossless mode')
    parser.add_argument('-k', '--keep-jxl', action='store_true', help='Keep intermediate JXL files')
    parser.add_argument('--single', action='store_true', help='Process single folder (not batch of subfolders)')
    parser.add_argument('-o', '--output-folder', type=Path, help='Output folder for CBZ files')
    parser.add_argument('-t', '--threads', type=int, default=4, help='Number of threads to use')
    parser.add_argument('--comicvine', action='store_true', help='Enrich metadata using Comic Vine API')
    
    args = parser.parse_args()
    
    # Setup Comic Vine client if requested
    comicvine_client = None
    series_cache = {}
    if args.comicvine:
        comicvine_client = setup_comicvine()
        if comicvine_client:
            # Load cached series from config
            cached_series = get_cached_series()
            for name, info in cached_series.items():
                if "skip" not in info:
                    series_cache[name] = info
            print(f"\nLoaded {len(series_cache)} cached series")
    
    input_path = Path(args.input)
    
    # Determine which folders to process based on the input path and arguments
    if args.single:
        folders = [input_path]
    elif input_path.is_dir() and not any(input_path.glob('*.jpg')):
        folders = sorted([d for d in input_path.iterdir() if d.is_dir()])
    else:
        folders = [input_path.parent]
    
    print(f"Found {len(folders)} folder(s) to process")
    
    # Process each folder and track the number of successes
    success = 0
    for folder in folders:
        if process_folder(folder, args.quality, args.lossless, args.keep_jxl, args.output_folder, args.threads, comicvine_client, series_cache):
            success += 1
    
    # Save cached series to config
    if args.comicvine and series_cache:
        from config import cache_series_info
        for name, info in series_cache.items():
            if "skip" not in info:
                cache_series_info(name, info)
        print(f"\nSaved {len(series_cache)} series to cache")
    
    # Print a summary of the batch processing
    print(f"\n{'='*50}")
    print(f"Completed: {success}/{len(folders)} folders processed")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
