import hashlib
from datetime import datetime
from urllib.parse import urlparse
import re
import requests
import json
from pathlib import Path


def normalize_filename(url):
    # Parse the URL to extract the hostname and path
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc
    # Remove the www. if it exists
    hostname = hostname.replace("www.", "")
    full_path = parsed_url.path.strip("/")
    # Remove or replace characters not allowed in filenames
    allowed_chars = re.compile(r'[^A-Za-z0-9\-_\.]')
    full_path_sanitized = re.sub(allowed_chars, '_', full_path)
    # Truncate the path to a reasonable length to avoid extremely long filenames
    path_sanitized = full_path_sanitized[:25]  # Adjust length as needed

    # Remove any special characters from the hostname and path
    valid_filename_part = re.sub(r'[^A-Za-z0-9\-_]', '', f"{hostname}_{path_sanitized}")

    # Create a hash of the URL
    url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()[:8]
    # Get a timestamp
    timestamp = datetime.now().strftime('%Y%m%d')
    # Generate a normalized filename
    filename = f"{valid_filename_part}_{url_hash}-{timestamp}.html"
    return filename


def fetch(
        url, 
        force=False, 
        cache_dir='cache', 
        staleness_tolerance=24,
        verbose=True
    ):
    cache_dir = Path(cache_dir)
    # ensure the cache directory exists
    cache_dir.mkdir(parents=True, exist_ok=True)

    TIME_THRESHOLD = staleness_tolerance * 60 * 60

    # Normalize URL; remove hash fragments
    url = url.split('#')[0]

    # Normalize the file name
    filename = normalize_filename(url)
    filepath = cache_dir / filename

    # Check if the file exists and get the modification time
    if filepath.exists() and not force:
        file_mod_time = str(filepath).rstrip('.html').split('-')[-1]
        file_mod_time = datetime.strptime(file_mod_time, '%Y%m%d')
        time_delta = datetime.now() - file_mod_time
        staleness = time_delta.total_seconds()

        # If the file is older than the threshold, fetch again
        if staleness < TIME_THRESHOLD:
            if verbose:
                print(f"Using cached version of {url}")
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()

    # If the file doesn't exist or is outdated, fetch the content
    if verbose:
        print(f"Fetching {url}")

    response = requests.get(url)
    if response.status_code == 200:
        # Ensure the cache directory exists

        # Get the current date and time
        current_datetime = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        metadata = {
            'url': url,
            'timestamp': current_datetime
        }

        # Create a comment with the metadata
        metadata_comment = f"<!-- Scrape Metadata:\n{json.dumps(metadata, indent=4)}\n-->\n\n"
        raw_html = response.text

        # Add the metadata comment to the beginning of the file
        html = f"{metadata_comment}{raw_html}"

        # Write the content to the file
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(html)
        return raw_html
    else:
        response.raise_for_status()