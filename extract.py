import json
import os
import re
import sys

#from collections import Counter
import collections
from pdfminer.high_level import extract_text as pdfminer_extract_text

import globals
import nlp
import sql
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


def preprocess_text_into_words(text):
    """Tokenize the content"""
    #return re.findall(r'\b\w+\b', text.lower())
    return re.findall(r'\b\w+\b', text)


def filter_words(words, min_char_len=3):
    """Remove any words that are combined with digits, e.g. xyz12"""

    filtered_lc_words = [word.lower() for word in words if len(word) >= min_char_len and not any(char.isdigit() for char in word)]

    return filtered_lc_words
    
def get_common_words(tokens, min_length=3):
    """Filter out words based on length and get all words"""

    # Also removes any digits
    # filtered_tokens = [word for word in tokens if len(word) >= min_length and not any(char.isdigit() for char in word)]

    word_freq = collections.Counter(tokens)
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
        #if os.path.exists(filename):
        #    print(f"  Skipping generating output file '{filename}' as this already exists.")
        #    print(f"  To regenerate/update this file, remove this file before running the script, or use -force to overwrite.")
        #    continue

        file_path = item['path']
        if file_path.endswith('.pdf'):
            text = extract_pdf(file_path)
        elif file_path.endswith('.txt'):
            text = extract_text(file_path)
        else:
            print(f"Error: Unsupported file type for {file_path}. Only pdf and txt files are supported.",file=sys.stderr)
            exit(1)

        words = preprocess_text_into_words(text)
        tokens = filter_words(words,min_char_len=3)
        common_words = get_common_words(tokens)

        if (verbose>1):
            print(json.dump(dict(common_words), fp=sys.stdout, ensure_ascii=False, indent=4))
            
        # Check if file exists and act according to `force` parameter
        if not os.path.exists(filename) or force:
            utils.save_to_json(dict(common_words), filename)
        else:
            print(f"  Output file '{filename}' already exists.")
            print(f"  To regenerate/update this file, remove this file first before running the script, or use -force to overwrite.")
            
def get_lang_paragraphs(urls,lang_uc):

    lang_all_paras = []

    downloads_dir = globals.config['downloads_dir']
    
    for url in urls:
        print(f"url_row = {url}")
        url_filehash = url[5]
        url_doctype  = url[6]
        nlp_para_count_lrl = url[11]
        
        if (nlp_para_count_lrl>0):
            filepath,rejected_filepath = utils.get_download_filename_pair(downloads_dir,url_filehash,url_doctype)
            text =nlp.extract_text_from_file(filepath, url_doctype)
                
            num_para_chunks_unused,lrl_lang_match_count_unused,lrl_paras = nlp.detect_para_language_lingua(text,lang_uc)
            lang_all_paras.extend(lrl_paras)
            
    return lang_all_paras

def extract_dict(lang_initialcap,force=False):

    """Use the database to go through the downloaded files, apply NLP to locate
    paragraphs of text the score extremely highly for the given language, and
    from that generate the word-based frequency counts to save as JSON"""

    lang_uc = lang_initialcap.upper()
    verbose = globals.verbose

    database_filename = globals.config.get('database_file')
    sql.set_db_filename(database_filename)
    
    config_languages = globals.config['languages']
    
    for config_language, item in config_languages.items():
        # print(f"args.lang={lang_initialcap}, config_language = {config_language}")
        
        if (lang_initialcap != "All") and (lang_initialcap != config_language):
            continue

        print(f"Processing langauge: {config_language}")

        # Check if file exists and act according to `force` parameter
        filename = f"dicts/common_words_{config_language.lower()}.json"
#        if os.path.exists(filename):
#            print(f"  Skipping generating output file '{filename}' as this already exists.")
#            print(f"  To regenerate/update this file, remove this file before running the script, or use -force to overwrite.")
#            continue

        urls = sql.get_all_urls_filter_downloaded_handled(downloaded=True, handled=True)
        lang_all_paras = get_lang_paragraphs(urls,lang_uc)

        text = "\n".join(lang_all_paras)
        words = preprocess_text_into_words(text)
        tokens = filter_words(words,min_char_len=3)        
        common_words = get_common_words(tokens)
        
        if (verbose>1):
            print(json.dump(dict(common_words), fp=sys.stdout, ensure_ascii=False, indent=4))
            
        # Check if file exists and act according to `force` parameter
        if not os.path.exists(filename) or force:
            utils.save_to_json(dict(common_words), filename)
        else:
            print(f"  Output file '{filename}' already exists.")
            print(f"  To regenerate/update this file, remove this file first before running the script, or use -force to overwrite.")
            
    return
