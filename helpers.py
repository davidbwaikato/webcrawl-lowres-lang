import os
import json
import hashlib
from const import GOOGLE, GOOGLE_API, BING, BING_API, QUERY, TYPE, TOTAL, MAORI, UNHANDLED, ITEMS


def read_file(filename):
    """Read file in UTF-8 format"""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read().splitlines()


def add_to_file(filename, text):
    """Add to file in UTF-8 format"""
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(text)


def read_config():
    """Read config.json"""
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def save_to_json(data, filename):
    """Save data to a JSON file"""
    filename = f"{filename}"
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    return filename


def read_json(filename):
    """Read data from a JSON file"""
    with open(filename, 'r', encoding="utf-8") as file:
        return json.load(file)


def hash_url(url):
    """Return an MD5 hash of a given URL"""
    return hashlib.md5(url.encode()).hexdigest()


def remove_blacklisted(urls, blacklist):
    """Remove blacklisted domains from the list of URLs"""
    return [url for url in urls if not any(domain in url for domain in blacklist)]


def initialize_query(query_dict):
    """Initialize JSON structure for a query and save it to a file"""
    # Extract the query and its type from the dictionary
    query = query_dict["query"]
    query_type = query_dict["type"]
    # File name is the query with spaces replaced by underscores
    filename = f"queries/{query.replace(' ', '_')}.json"
    # If file already exists, don't create a new one
    if os.path.exists(filename):
        return 0
    data = {
        QUERY: query,
        TYPE: query_type,
        TOTAL: 0,
        MAORI: 0,
        UNHANDLED: 0,
        GOOGLE: {
            TOTAL: 0,
            MAORI: 0,
            UNHANDLED: 0,
            ITEMS: []
        },
        GOOGLE_API: {
            TOTAL: 0,
            MAORI: 0,
            UNHANDLED: 0,
            ITEMS: []
        },
        BING: {
            TOTAL: 0,
            MAORI: 0,
            UNHANDLED: 0,
            ITEMS: []
        },
        BING_API: {
            TOTAL: 0,
            MAORI: 0,
            UNHANDLED: 0,
            ITEMS: []
        }
    }
    save_to_json(data, filename)
    return 1
