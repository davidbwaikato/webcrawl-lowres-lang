import jsonc
import hashlib
import os

import termdistribution
import globals

def move_file(src_path,dst_path):
    try:
        os.rename(src_path,dst_path)
    except Exception as e:
        print(f"Error renaming file from {src_path} to {dst_path}: {e}")

def delete_file(path):
    try:
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



def load_language_dictionary(lang):
    """Load the dictionary for a specific language from its JSON file"""    
    try:
        lang_lc = lang.lower()
        filename = os.path.join("dicts",f"unigram_words_{lang_lc}.json")
        with open(filename, "r", encoding="utf-8") as file:
            return jsonc.load(file)
    except:
        return None


def load_language_dictionary_vector(lang):
    word_dict = load_language_dictionary(lang)

    termvec_rec = termdistribution.freqdict_to_termvec(word_dict)

    return termvec_rec


def append_to_language_dictionary(core_dict,topup_dict):

    for topup_key in topup_dict.keys():
        topup_val = topup_dict[topup_key]
        if topup_key in core_dict:
            core_dict[topup_key] += topup_val
        else:
            core_dict[topup_key] = topup_val
            

def hash_url(url):
    """Return an MD5 hash of a given URL"""
    return hashlib.md5(url.encode()).hexdigest()


def remove_excluded_domains(urls, excluded_domain_list):
    """Remove excluded domains from the list of URLs"""
    return [url for url in urls if not any(domain in url for domain in excluded_domain_list)]


def get_download_filename_pair(downloads_dir,filehash,doctype):
    filename = filehash + "." + doctype
    full_filename = os.path.join(downloads_dir, filename)

    rejected_filename =f"REJECTED-{filehash}.{doctype}"
    full_rejected_filename = os.path.join(downloads_dir, rejected_filename)
    
    return full_filename,full_rejected_filename
