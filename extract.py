import json
import os
import re
import sys

from collections import Counter
from pdfminer.high_level import extract_text as pdfminer_extract_text

import globals
import utils


def extract_text(path):
    """Extract text from a .txt file"""
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading {path}: {e}")
        exit(1)

def extract_pdf(path):
    """Extract text content from a PDF"""
    try:
        return pdfminer_extract_text(path)
    except Exception as e:
        print(f"Error reading {path}: {e}")
        exit(1)


def preprocess_text(text):
    """Tokenize the content"""
    return re.findall(r'\b\w+\b', text.lower())


def get_common_words(tokens, min_length=3):
    """Filter out words based on length and get all words"""

    # Also removes any digits
    filtered_tokens = [word for word in tokens if len(
        word) >= min_length and not any(char.isdigit() for char in word)]

    word_freq = Counter(filtered_tokens)
    most_common = word_freq.most_common() # returns all frequency counts if no int-param passed in
    
    return most_common


def extract_udhr(lang_initialcap,force=False):
    """Process each UHDR pdf/text file and save results to JSON"""

    verbose = globals.verbose
    
    config_languages = globals.config['languages']

    for config_language, item in config_languages.items():
        # print(f"args.lang={lang_initialcap}, config_language = {config_language}")
        
        if (lang_initialcap != "All") and (lang_initialcap != config_language):
            continue

        print(f"Processing langauge: {config_language}")

        # Check if file exists and act according to `force` parameter
        filename = f"dicts/common_words_{config_language.lower()}.json"
        if os.path.exists(filename):
            print(f"  Skipping generating output file '{filename}' as this already exists.")
            print(f"  To regenerate/update this file, remove this file before running the script, or use -force to overwrite.")
            continue
        
        file_path = item['path']
        if file_path.endswith('.pdf'):
            text = extract_pdf(file_path)
        elif file_path.endswith('.txt'):
            text = extract_text(file_path)
        else:
            print(f"Error: Unsupported file type for {file_path}. Only pdf and txt files are supported.",file=sys.stderr)
            exit(1)

        tokens = preprocess_text(text)
        common_words = get_common_words(tokens)

        if (verbose>1):
            print(json.dump(dict(common_words), fp=sys.stdout, ensure_ascii=False, indent=4))
            
        # Check if file exists and act according to `force` parameter
        if not os.path.exists(filename) or force:
            utils.save_to_json(dict(common_words), filename)

def get_lang_paragraphs(queries,lang_uc):

    lang_paras = []
    
    for query in queries:
        url_id       = query[0]
        url_filehash = query[5]
        url_doctype  = query[6]
        url_fulllang = query[9]

        if (url_fullang == lang_uc):
            # Read it in
            # apply NLP per paragraph
            x =5
            
    return lang_paras

def extract_dict(lang_initialcap,force=False):

    """Use the database to go through the downloaded files, apply NLP to locate
    paragraphs of text the score extremely highly for the given language, and
    from that generate the word-based frequency counts to save as JSON"""

    lang_uc = lang_initialcap.upper()
    
    verbose = globals.verbose
    
    config_languages = globals.config['languages']

    for config_language, item in config_languages.items():
        # print(f"args.lang={lang_initialcap}, config_language = {config_language}")
        
        if (lang_initialcap != "All") and (lang_initialcap != config_language):
            continue

        print(f"Processing langauge: {config_language}")

        # Check if file exists and act according to `force` parameter
        filename = f"dicts/common_words_{config_language.lower()}.json"
        if os.path.exists(filename):
            print(f"  Skipping generating output file '{filename}' as this already exists.")
            print(f"  To regenerate/update this file, remove this file before running the script, or use -force to overwrite.")
            continue

        queries = sql.get_all_queries(lang_uc, handled=True)
        lang_paras = get_lang_paragraphs(queries,lang_uc)
            
        common_words = []
        

        if (verbose>1):
            print(json.dump(dict(common_words), fp=sys.stdout, ensure_ascii=False, indent=4))
            
        # Check if file exists and act according to `force` parameter
        if not os.path.exists(filename) or force:
            utils.save_to_json(dict(common_words), filename)
    
    return
