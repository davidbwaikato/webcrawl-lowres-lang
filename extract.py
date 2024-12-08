import json
import os
import re
import sys

import collections
from pdfminer.high_level import extract_text as pdfminer_extract_text


import fileutils
import enums
import globals
import nlp
import sql


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


def preprocess_text_into_unigram_words(text):
    """Tokenize the content into unigrams"""
    #return re.findall(r'\b\w+\b', text)

    text_without_punc = re.sub(r'[^\w\s]',' ',text)    
    unigrams = text_without_punc.split()
    return unigrams


def preprocess_text_into_bigram_words(text):
    """Tokenize the content into bigrams"""
    #re.findall(r'\b\w+\b\s*\w+\b', text)

    text_without_punc = re.sub(r'[^\w\s]',' ',text)    
    words = text_without_punc.split()

    bigrams = []
    word1 = words.pop()
    
    for word in words:
        word2 = word
        bigram_word = word1 + " " + word2

        bigrams.append(bigram_word)
        word1 = word2


    return bigrams


def filter_words(words, min_char_len=3):
    """Remove any words that are combined with digits, e.g. xyz12"""

    filtered_lc_words = [word.lower() for word in words if len(word) >= min_char_len and not any(char.isdigit() for char in word)]

    return filtered_lc_words
    
def get_token_frequencies(tokens):
    """Filter out words based on length and get all words"""

    word_freq = collections.Counter(tokens)
    most_common = word_freq.most_common() # returns all frequency counts if no int-param passed in
    
    return most_common


def extract_udhr(lang_initialcap,force=False):
    """Process each UHDR pdf/text file and save results to JSON"""

    verbose = globals.verbose
    
    config_languages = globals.config['languages']

    found_lang = False
    
    for config_language, item in config_languages.items():
        # print(f"args.lang={lang_initialcap}, config_language = {config_language}")
        
        if (lang_initialcap != "All") and (lang_initialcap != config_language):
            continue

        print(f"Processing langauge: {config_language}")
        found_lang = True
        
        file_path = item['path']
        if file_path.endswith('.pdf'):
            text = extract_pdf(file_path)
        elif file_path.endswith('.txt'):
            text = extract_text(file_path)
        else:
            print(f"Error: Unsupported file type for {file_path}. Only pdf and txt files are supported.",file=sys.stderr)
            exit(1)

        unigram_words = preprocess_text_into_unigram_words(text)
        unigram_tokens = filter_words(unigram_words,min_char_len=3)
        unigram_word_freq = get_token_frequencies(unigram_tokens)
        unigram_word_freq_dict = dict(unigram_word_freq)
        
        bigram_words = preprocess_text_into_bigram_words(text)
        bigram_tokens = filter_words(bigram_words,min_char_len=3)
        bigram_word_freq = get_token_frequencies(bigram_tokens)
        bigram_word_freq_dict = dict(bigram_word_freq)
        
        unigram_ofilename = f"dicts/unigram_words_{config_language.lower()}.json"
        bigram_ofilename = f"dicts/bigram_words_{config_language.lower()}.json"
        
        if (verbose>1):
            print(f"====")
            print(f"Unigram Word Frequencies for {lang_initialcap}")
            print(f"====")
            print(json.dump(unigram_word_freq_dict, fp=sys.stdout, ensure_ascii=False, indent=4))
            print(f"====")
            print(f"Bigram Word Frequencies for {lang_initialcap}")
            print(f"====")
            print(json.dump(bigram_word_freq_dict, fp=sys.stdout, ensure_ascii=False, indent=4))
            
        # Check if file exists and act according to `force` parameter
        if not os.path.exists(unigram_ofilename) or force:
            fileutils.save_to_json(dict(unigram_word_freq), unigram_ofilename)
        else:
            print(f"  Output file '{unigram_ofilename}' already exists.")
            print(f"  To regenerate/update this file, remove this file first before running the script, or use -f/--force to overwrite.")
            print( "  ----")
        if not os.path.exists(bigram_ofilename) or force:
            fileutils.save_to_json(bigram_word_freq_dict, bigram_ofilename)
        else:
            print(f"  Output file '{bigram_ofilename}' already exists.")
            print(f"  To regenerate/update this file, remove this file first before running the script, or use -f/--force to overwrite.")
            print( "  ----")

    if (not found_lang):
        print( "----")
        print(f"Failed to find language '{lang_initialcap}' in config.json.  No frequency-count dictionary generated")
        print( "----")
        
def get_lang_paragraphs(urls,lang_uc, nlp_lang_supported,lang_detect_algorithm, lang_dict_termvec_rec):

    lang_all_paras = []

    downloads_dir = globals.config['downloads_dir']
    
    for url in urls:
        url_href     = url[3]
        url_filehash = url[5]
        url_doctype  = url[6]
        nlp_para_count_lrl = url[11]

        print(f"++++ Processing filehash: {url_filehash} ++++")
        print(f"  {url_href}")

        # **** XXXX
        #if (nlp_para_count_lrl>0):
        filepath,rejected_filepath = fileutils.get_download_filename_pair(downloads_dir,url_filehash,url_doctype)
        if os.path.exists(filepath):
            text =nlp.extract_text_from_file(filepath, url_doctype)

            detect_info = nlp.detect_para_language_lingua(text,lang_uc, nlp_lang_supported, lang_dict_termvec_rec)
    
            #num_paras                = detect_info["num_paras"]
            lrl_lingua_match_paras   = detect_info["lrl_lingua_match_paras"]
            lrl_termdist_match_paras = detect_info["lrl_termdist_match_paras"]

            #lrl_lingua_match_count = len(lrl_lingua_match_paras)

            if (lang_detect_algorithm == enums.LangDetect.cossim):
                lang_all_paras.extend(lrl_termdist_match_paras)
            else:
                lang_all_paras.extend(lrl_lingua_match_paras)
            
    return lang_all_paras


def extract_database_downloaded(lang_initialcap,force, nlp_lang_supported,lang_detect_algorithm):
    """Use the database to go through the downloaded files, apply NLP to locate
    paragraphs of text the score extremely highly for the given language, and
    from that generate the word-based frequency counts to save as JSON"""

    lang_uc = lang_initialcap.upper()
    lang_lc = lang_initialcap.lower()
    verbose = globals.verbose

    database_filename = globals.config.get('database_file')
    sql.set_db_filename(database_filename)
    
    print(f"Processing langauge: {lang_initialcap}")
    lang_dict_termvec_rec = fileutils.load_language_dictionary_vector(lang_initialcap)    
    
    #urls = sql.get_all_urls_filter_downloaded_handled(downloaded=True, handled=True)
    urls = sql.get_all_urls_filter_downloaded(downloaded=True)
    
    lang_all_paras = get_lang_paragraphs(urls,lang_uc, nlp_lang_supported,lang_detect_algorithm, lang_dict_termvec_rec)

    # **** XXXX refactor into subroutine ????
    text = "\n".join(lang_all_paras)
    words = preprocess_text_into_unigram_words(text)
    tokens = filter_words(words,min_char_len=3)        
    
    downloaded_unigram_words = get_token_frequencies(tokens)
    downloaded_unigram_words_dict = dict(downloaded_unigram_words)

    dst_unigram_words_dict = None
    
    if globals.args.output_mode == enums.DictOutputMode.merge:
        core_unigram_words_dict = fileutils.load_language_dictionary(lang_uc)        
        fileutils.append_to_language_dictionary(core_unigram_words_dict,downloaded_unigram_words_dict)
        dst_unigram_words_dict = core_unigram_words_dict        
    else:
        dst_unigram_words_dict = downloaded_unigram_words_dict
        
    # Check if frequency-coutn dictionary already exists and act according to `force` parameter
    unigram_filename = f"dicts/unigram_words_{lang_lc}.json"        
    if not os.path.exists(unigram_filename) or force:
        fileutils.save_to_json(dst_unigram_words_dict, unigram_filename)
    else:
        print( "----")
        print( "Frequency-based unigrams from downloaded files:")
        json.dump(dst_unigram_words_dict, fp=sys.stdout, ensure_ascii=False, indent=4)
        print()
        print( "----")              
        print()
        print( "====")
        print(f"Output file '{unigram_filename}' already exists, so have printed JSON dict to standard-out..")
        print(f"To regenerate/update this file, remove this file first before running the script, or use -f/--force to overwrite.")
        print( "====")

            
