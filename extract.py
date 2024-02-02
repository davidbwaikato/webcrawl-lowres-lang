import re
import os
from collections import Counter
from pdfminer.high_level import extract_text as pdfminer_extract_text
from helpers import read_config, save_to_json


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


def extract(reset=False):
    """Process each file and save results to JSON"""
    config = read_config()
    languages = config['languages']
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
            save_to_json(dict(common_words), filename)
