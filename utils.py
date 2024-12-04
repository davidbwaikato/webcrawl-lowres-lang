import jsonc
import hashlib
import os

import globals

from const import GOOGLE, GOOGLE_API, BING, BING_API, QUERY, TYPE, TOTAL, MAORI, UNHANDLED, ITEMS

def move_file(src_path,dst_path):
    try:
        print(f"***** moving {src_path} -> {dst_path}")
        os.rename(src_path,dst_path)
    except Exception as e:
        print(f"Error renaming file from {src_path} to {dst_path}: {e}")

def delete_file(path):
    try:
        print(f"***** deleting {path}")
        os.remove(path)
    except FileNotFoundError:
        print(f"File not found: {path}")
    except Exception as e:
        print(f"Error deleting file: {e}")
        

def read_file(filename):
    """Read file in UTF-8 format"""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read().splitlines()


def add_to_file(filename, text):
    """Add/Append to file in UTF-8 format"""
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(text)


def read_config():
    """Read config.json"""
    with open('config.json', 'r', encoding='utf-8') as f:
        return jsonc.load(f)


def save_to_json(data, filename, indent=4):
    """Save data to a JSON file"""

    if globals.verbose > 0:
        print(f"Saving JSON to: {filename}")
        
    filename = f"{filename}"
    with open(filename, "w", encoding="utf-8") as file:
        jsonc.dump(data, file, ensure_ascii=False, indent=4)
    return filename


def read_json(filename):
    """Read data from a JSON file"""
    with open(filename, 'r', encoding="utf-8") as file:
        return jsonc.load(file)


def hash_url(url):
    """Return an MD5 hash of a given URL"""
    return hashlib.md5(url.encode()).hexdigest()


def remove_blacklisted(urls, blacklist):
    """Remove blacklisted domains from the list of URLs"""
    return [url for url in urls if not any(domain in url for domain in blacklist)]


def get_download_filename_pair(downloads_dir,filehash,doctype):
    filename = filehash + "." + doctype
    full_filename = os.path.join(downloads_dir, filename)

    rejected_filename =f"REJECTED-{filehash}.{doctype}"
    full_rejected_filename = os.path.join(downloads_dir, rejected_filename)
    
    return full_filename,full_rejected_filename
