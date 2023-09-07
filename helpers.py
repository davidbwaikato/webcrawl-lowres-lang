import os
import json
import hashlib


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
        "query": query,
        "type": query_type,
        "total": 0,
        "maori": 0,
        "unhandled": 0,
        "google": {
            "total": 0,
            "maori": 0,
            "unhandled": 0,
            "items": []
        },
        "google_api": {
            "total": 0,
            "maori": 0,
            "unhandled": 0,
            "items": []
        },
        "bing": {
            "total": 0,
            "maori": 0,
            "unhandled": 0,
            "items": []
        },
        "bing_api": {
            "total": 0,
            "maori": 0,
            "unhandled": 0,
            "items": []
        }
    }
    save_to_json(data, filename)
    return 1
