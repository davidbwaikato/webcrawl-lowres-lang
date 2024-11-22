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
    return word_freq.most_common()


def extractDEPRECATED(reset=False):
    """Process each file and save results to JSON"""
    languages = globals.config['languages']
    for language, item in languages.items():
        file_path = item['path']
        if file_path.endswith('.pdf'):
            text = extract_pdf(file_path)
        elif file_path.endswith('.txt'):
            text = extract_text(file_path)
        else:
            print(f"Error: Unsupported file type for {file_path}. Only pdf and txt files are supported.")
            exit(1)
        tokens = preprocess_text(text)
        common_words = get_common_words(tokens)
        filename = f"dicts/common_words_{language.lower()}.json"
        # Check if file exists and act according to `reset` parameter
        if not os.path.exists(filename) or reset:
            utils.save_to_json(dict(common_words), filename)
        else:
            print(f"{filename} already exists.  As function argument 'reset'={reset}, not overwriting file")


def extractNew(lang,force=False,verbose=False):
    """Process each file and save results to JSON"""

    languages = globals.config['languages']

    for language, item in languages.items():
        # print(f"args.lang={lang}, language = {language}")
        
        if (lang != "All") and (lang != language):
            continue

        print(f"Processing langauge: {language}")
        
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
        filename = f"dicts/common_words_{language.lower()}.json"

        if (verbose):
            print(json.dump(dict(common_words), fp=sys.stdout, ensure_ascii=False, indent=4))
            
        # Check if file exists and act according to `force` parameter
        if not os.path.exists(filename) or force:
            utils.save_to_json(dict(common_words), filename)
        else:
            print(f"  As function argument 'force'={force}, not overwriting existig: {filename}")
            
