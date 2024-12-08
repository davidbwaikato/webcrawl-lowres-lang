import math
import re

#from bs4 import BeautifulSoup
import bs4
import PyPDF2
import docx

import extract
import queries
import termdistribution

import globals

from lingua import Language, LanguageDetectorBuilder


_total_num_paras           = 0
_total_processed_num_paras = 0
_total_lrl_num_paras       = 0

# import spacy
# import nltk
# from langdetect import DetectorFactory
# DetectorFactory.seed = 0
# from langdetect import detect
# from spacy_langdetect import LanguageDetector
# from nltk.corpus import stopwords
# from googletrans import Translator


# # nltk.download('punkt')
# # nltk.download('stopwords')
# # nltk.download('averaged_perceptron_tagger')
# # python -m spacy download en_core_web_sm
# nlp = spacy.load("en_core_web_sm")
# # Create a custom component
# @spacy.Language.factory("language_detector")
# def create_language_detector(nlp, name):
#     return LanguageDetector()
# # Add the component to the pipeline
# nlp.add_pipe("language_detector")

lingua_detector = LanguageDetectorBuilder.from_all_languages().with_preloaded_language_models().build()
#linguaLanguages = [Language.ENGLISH, Language.MAORI]
#lingua_detector = LanguageDetectorBuilder.from_languages(*linguaLanguages).build()

supported_lingua_uc_langs = [ lang.name for lang in Language.all()]

supported_lingua_uc_langs_lookup = {}
for lang in Language.all():
    supported_lingua_uc_langs_lookup[lang.name] = lang

def is_lingua_supported_lang(lang):
    lang_uc = lang.upper()
    return lang_uc in supported_lingua_uc_langs

def get_lingua_lang_rec(lang):
    lang_uc = lang.upper()

    lang_rec = supported_lingua_uc_langs_lookup.get(lang_uc,None)

    return lang_rec 

    

def clean_text(text,reg_expr=r'\n{3,}',replace_str='\n\n'):
    # Replace instances where there are more than two consecutive newlines with just two.
    cleaned_text = re.sub(reg_expr, replace_str, text)
    return cleaned_text

def text_to_clean_paras(text):
    
    simplified_para_boundary_text = clean_text(text, r'(\s*\n){2,}','\n')
    paras = simplified_para_boundary_text.splitlines()

    # Still possible to a leading empty para, and lines of text starting with a space
    # => clean up the paras array

    clean_paras = []
    for para in paras:
        if re.match(r'^\s*$',para):
            continue
        clean_para = re.sub(r'(^\s+)|(\s+$)', "", para)
        clean_paras.append(clean_para)
        
    return clean_paras
    
        
def extract_text_from_file(filepath, doc_type):
    if doc_type == "html":
        # open the file as raw-binary (rather than utf-8) as it turns out BeautifulSoup
        # auto-magically works out charset encoding of the file (e.g. explicitly as chatset
        # <meta> tag), ultimately returning a Unicode string
        with open(filepath, 'rb') as f: 
            soup = bs4.BeautifulSoup(f, 'html.parser')
            #text = soup.get_text(separator=" ")
            text = soup.get_text(separator="\n",strip=True)
            return text
    elif doc_type == "pdf":
        with open(filepath, 'rb') as f:
            text = ""
            try:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text()
            except Exception as e:
                print(f"Error encountered when reading in PDF document: {e}")
            return text
    elif doc_type == "docx":
        doc = docx.Document(filepath)
        return " ".join([para.text for para in doc.paragraphs])
    else:
        print(f"Unsupported doc_type: {doc_type}")
        return None

def convert_text_to_paras(text, min_para_word_len):
    """Return array of paragraphs to run language detection over"""

    global _total_num_paras
    
    #if (globals.verbose >= 5):
    #    verbose_char_len = globals.verbose*50
    #    print(f"++++ convert_text_to_paras() text[:{verbose_char_len}] ++++")
    #    print(text[:verbose_char_len])
    #    print("++++")


    paras = text_to_clean_paras(text)
    num_paras = len(paras)
    _total_num_paras += num_paras
    
    if (globals.verbose >= 4):
        verbose_numpara_len = globals.verbose*10
        print(f"++++ convert_text_to_paras() paras[:{verbose_numpara_len}] ++++")
        print(f"{paras[:verbose_numpara_len]}")
        print("++++")
        
    
    processed_paras = []

    for para in paras:
        para_words = para.split()
        if (len(para_words) > min_para_word_len):
            # enough words to include/be processed
            processed_paras.append(para)
        
    return processed_paras

def convert_text_to_parachunks(text, min_parachunk_word_len):
    """Gets optimal sized chunks to run paragraph language detection for"""

    #if (globals.verbose >= 5):
    #    verbose_char_len = globals.verbose*50
    #    print(f"++++ convert_text_to_parachunks() text[:{verbose_char_len}] ++++")
    #    print(text[:verbose_char_len])
    #    print("++++")


    paras = text_to_clean_paras(text)

    if (globals.verbose >= 4):
        verbose_numpara_len = globals.verbose*10
        print(f"++++ convert_text_to_parachunks() paras[:{verbose_numpara_len}] ++++")
        print(f"{paras[:verbose_numpara_len]}")
        print("++++")
        
    
    processed_paras = []
    
    para_cat = ""

    for para in paras:
        para_cat = para_cat + para + '\n'
        para_cat_words = para_cat.split()
        if (len(para_cat_words) > min_parachunk_word_len):
            # enough concatenated words to include/be processed
            processed_paras.append(para_cat)
            para_cat = ""
            
    return processed_paras


# def detect_language_spacy(text):
#     doc = nlp(text)
#     if doc._.language:
#         return doc._.language["language"]
#     return None

# def detect_language_nltk(text):
#     languages_ratios = {}
#     tokens = text.split()
#     words = [word.lower() for word in tokens]
#     for language in stopwords.fileids():
#         stopwords_set = set(stopwords.words(language))
#         words_set = set(words)
#         common_elements = words_set.intersection(stopwords_set)
#         languages_ratios[language] = len(common_elements)
#     most_rated_language = max(languages_ratios, key=languages_ratios.get)
#     return most_rated_language

# translator = Translator()
# def detect_language_google(text):
#     detected = translator.detect(text)
#     if detected is not None and detected.lang is not None:
#         return detected.lang
#     else:
#         print("Translation response is None.")
#         return None

# def detect_language_langdetect(text):
#     """Detect language using langdetect."""
#     try:
#         return detect(text)
#     except:
#         print("Error detecting language with langdetect")
#         return None

def process_text_in_chunksDEPRECATED(text, detect:Language):
    """Gets an optimal chunk size to run paragraph language detection for"""

    #if (globals.verbose >= 3):
    #    print("++++ process_text_in_chunks() ++++")
    #    print(text[:globals.verbose*100])
    #    print("++++")
        
    words = text.split()
    num_words = len(words)

    short_text_threshold = 50
    medium_text_threshold = 200
    chunk_size = 500

    if num_words <= short_text_threshold:
        chunk_size = 50
    elif num_words <= medium_text_threshold:
        chunk_size = 200
        
    # Split the text into chunks
    paragraphs = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    # Process each chunk and count paragraphs
    total = len(paragraphs)
    count = 0
    for chunk in paragraphs:
        language = lingua_detector.detect_language_of(chunk)
        if language == detect:
            count += 1

    # Calculate the percentage
    percentage = (count / total) * 100 if total > 0 else 0
    return percentage

# Precision and Recall Counts
_pr_counts = {
    'tp': 0,
    'fp': 0,
    'fn': 0
}
    

def termdist_compute_language_confidence(para_chunk,lang_dict_termvec_rec):

    # **** XXXX refactor into function
    para_unigram_words = extract.preprocess_text_into_unigram_words(para_chunk)
    para_unigram_tokens = extract.filter_words(para_unigram_words,min_char_len=3)
    para_unigram_word_freq = extract.get_token_frequencies(para_unigram_tokens)
    para_unigram_word_freq_dict = dict(para_unigram_word_freq)

    para_termvec_rec = termdistribution.aligned_freqdict_to_termvec(lang_dict_termvec_rec,para_unigram_word_freq_dict)
    
    confidence = termdistribution.calc_cosine_similarity(para_termvec_rec,lang_dict_termvec_rec)
    return confidence


def detect_para_language_lingua(text,detect_langname, nlp_lang_supported, lang_dict_termvec_rec):
    """
    Working with (potetially contatenated paragraphs to reach config set min word count) 
    run language detection on paragraphs.  Compute both the Cosine Similarity measure based
    on 'lang_dict_termvec_rec' and (if 'nlp_lang_supported') the Lingua-based one
    """

    global _total_processed_num_paras
    
    min_lingua_para_word_len     = globals.config['nlp']['min_lingua_para_word_len']
    min_lingua_para_confidence   = globals.config['nlp']['min_lingua_para_confidence']

    min_termdist_para_word_len   = globals.config['nlp']['min_termdist_para_word_len']
    min_termdist_para_confidence = globals.config['nlp']['min_termdist_para_confidence']

    min_parachunk_word_len = globals.config['nlp'].get('min_parachunk_word_len',None)

    min_para_word_len = min_lingua_para_word_len if nlp_lang_supported else min_termdist_para_word_len
    
    paras = convert_text_to_paras(text,min_para_word_len)
    # **** Future Proofing idea
    #paras = convert_text_to_parachunks(text,min_parachunk_word_len)
    
    # Process each paragraph and count language detection results
    num_paras = len(paras)

    _total_processed_num_paras += num_paras
    
    lrl_lingua_match_count  = 0
    lrl_lingua_match_paras  = []

    lrl_termdist_match_count  = 0
    lrl_termdist_match_paras  = []

    lrl_agreement_match_paras = []

    lrl_lingua_lang_rec = get_lingua_lang_rec(detect_langname)        

    for para in paras:
        if nlp_lang_supported:
            lrl_lingua_para_confidence = lingua_detector.compute_language_confidence(para, lrl_lingua_lang_rec)

            if lrl_lingua_para_confidence > min_lingua_para_confidence:
                lrl_lingua_para_langname = detect_langname
            else:
                lrl_lingua_para_langname = f"NON-{detect_langname}"
                lrl_lignua_para_confidende = 0.0            
        else:
            lrl_lingua_para_langname = "<UNDEFINED>"
            lrl_lingua_para_confidence = 0.0
            
        # Can always calculate the Cosine-Similarity
        lrl_termdist_para_confidence = termdist_compute_language_confidence(para,lang_dict_termvec_rec)

        show_para = False
        show_prefix_matches = []
        
        if (globals.verbose >= 3):
            show_para = True
            
        if lrl_termdist_para_confidence >= min_termdist_para_confidence:
            print(f"==== LRL Cosine Similarity match  ({lrl_termdist_para_confidence}) ====")
            lrl_termdist_match_count += 1
            lrl_termdist_match_paras.append(para)
            show_para = True
            show_prefix_matches.append(f"CosSim-{detect_langname}")

        if nlp_lang_supported:
            if lrl_lingua_para_confidence >= min_lingua_para_confidence:
                    
                print(f"==== LRL NLP Lingua match         ({lrl_lingua_para_confidence}) ====")            
                lrl_lingua_match_count += 1
                lrl_lingua_match_paras.append(para)
                show_para = True
                show_prefix_matches.append(f"Lingua-{detect_langname}")
                
            if lrl_termdist_para_confidence >= min_termdist_para_confidence:
                if lrl_lingua_para_confidence >= min_lingua_para_confidence:
                    # True-positive NLP test                    
                    lrl_agreement_match_paras.append(para)
                    _pr_counts['tp'] += 1
                    print("True-Positive")
                else:
                    # False-positive NLP test
                    _pr_counts['fp'] += 1
                    print("False-Positive")
            else:
                # Have a False-negative NLP test if NLP found the para to be LRL, but not the Cosine-Similarity test
                if lrl_lingua_para_confidence >= min_lingua_para_confidence:
                    _pr_counts['fn'] += 1
                    print("False-Negative")
                    

        show_prefix = ""
        if len(show_prefix_matches) > 0:
            show_prefix = ",".join(show_prefix_matches) + ":\t"
        
        if show_para:
            print( "----")
            print(f"{show_prefix}{para}")
            print( "----")
            print()
                        
    print(f"  Paras: lrl_termdist_match_count = {lrl_termdist_match_count} out of {num_paras}")
    if nlp_lang_supported:    
        print(f"         lrl_lingua_match_count   = {lrl_lingua_match_count} out of {num_paras}") 
    
    return {
        "num_paras"                 : num_paras,
        "lrl_lingua_match_paras"    : lrl_lingua_match_paras,
        "lrl_termdist_match_paras"  : lrl_termdist_match_paras,
        "lrl_agreement_match_paras" : lrl_agreement_match_paras
    }
        

def detect_language_lingua(text,  detect_langname, lang_dict_termvec_rec):
    """Detect language with confidence level using Lingua.py"""
    global _total_num_paras
    global _total_processed_num_paras
    global _total_lrl_num_paras

    nlp_lang_supported = is_lingua_supported_lang(detect_langname)
    
    # Full-text level analysis
    predicted_full_langname = None
    lrl_lingua_fullconf = 0.0
        
    min_lingua_full_confidence = globals.config['nlp']['min_lingua_full_confidence']
        
    if nlp_lang_supported:
        lrl_lingua_lang_rec = get_lingua_lang_rec(detect_langname)        
        lrl_lingua_fullconf = lingua_detector.compute_language_confidence(text, lrl_lingua_lang_rec)

        if lrl_lingua_fullconf > min_lingua_full_confidence:
            predicted_full_langname = detect_langname
        else:
            predicted_full_langname = f"NON-{detect_langname}"
            lrl_lignua_fullconf = 0.0
    else:
        predicted_full_langname = "<UNDEFINED>"
        lrl_lingua_fullconf = 0.0
    
    # Paragraph-level analysis    
    detect_info = detect_para_language_lingua(text,detect_langname, nlp_lang_supported, lang_dict_termvec_rec)
    
    num_paras                = detect_info["num_paras"]
    lrl_lingua_match_paras   = detect_info["lrl_lingua_match_paras"]
    lrl_termdist_match_paras = detect_info["lrl_termdist_match_paras"]

    lrl_lingua_match_count   = len(lrl_lingua_match_paras)
    lrl_termdist_match_count = len(lrl_termdist_match_paras)

    lrl_match_count = lrl_lingua_match_count if (nlp_lang_supported) else lrl_termdist_match_count    
    lrl_para_percentage = (lrl_match_count / num_paras) * 100 if num_paras > 0 else 0

    if (nlp_lang_supported):
        _total_lrl_num_paras += lrl_lingua_match_count
    else:
        _total_lrl_num_paras += lrl_termdist_match_count
        

    print( "========")
    print(f"Recall and Precision raw counts:{_pr_counts}")

    precision = _pr_counts['tp'] / (_pr_counts['tp'] + _pr_counts['fp']) if (_pr_counts['tp'] > 0) and (_pr_counts['fp'] > 0) else 0
    recall    = _pr_counts['tp'] / (_pr_counts['tp'] + _pr_counts['fn']) if (_pr_counts['tp'] > 0) and (_pr_counts['fn'] > 0) else 0

    print( "----")
    print(f"Precision = {precision}")
    print(f"Recall    = {recall}")
    print( "----")

    print(f"Total number of paragraphs           = {_total_num_paras}")
    print(f"Total number of processed paragraphs = {_total_processed_num_paras}")
    print(f"Total number of lrl paragraphs       = {_total_lrl_num_paras}")
    print( "========")
    
    return {
        "full_lang": predicted_full_langname,
        "full_conf": round(lrl_lingua_fullconf, 2),
        "para_count": num_paras,
        "para_count_lrl": lrl_match_count,
        "para_perc_lrl":  round(lrl_para_percentage, 2)
    }

def run_nlp_algorithms(text, detect_langname, lang_dict_termvec_rec):
    """Detect language of the text using (at this stage of development, just the) lingua method."""
    lingua = detect_language_lingua(text, detect_langname, lang_dict_termvec_rec)
    
    return {
        "lingua": lingua,
    }
