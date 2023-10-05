import re
import os
from collections import Counter
from pdfminer.high_level import extract_text
from helpers import read_config, save_to_json


def extract_udhr_text(pdf_path):
    """Extract text content from a PDF"""
    return extract_text(pdf_path)


def preprocess_udhr_text(text):
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
    """Process each PDF and save results to JSON"""
    config = read_config()
    languages = config['languages']
    for language, item in languages.items():
        text = extract_udhr_text(item['path'])
        tokens = preprocess_udhr_text(text)
        common_words = get_common_words(tokens)
        filename = f"dicts/common_words_{language.lower()}.json"
        # Check if file exists and act according to `reset` parameter
        if not os.path.exists(filename) or reset:
            save_to_json(dict(common_words), filename)
