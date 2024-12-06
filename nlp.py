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
    return supported_lingua_uc_langs_lookup[lang_uc]

    

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
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    elif doc_type == "docx":
        doc = docx.Document(filepath)
        return " ".join([para.text for para in doc.paragraphs])
    else:
        print(f"Unsupported doc_type: {doc_type}")
        return None

def convert_text_to_parachunks(text, min_para_word_len, min_parachunk_word_len=None):
    """Gets optimal sized chunks to run paragraph language detection for"""

    #if (globals.verbose >= 5):
    #    verbose_char_len = globals.verbose*50
    #    print(f"++++ process_text_in_chunks() text[:{verbose_char_len}] ++++")
    #    print(text[:verbose_char_len])
    #    print("++++")


    paras = text_to_clean_paras(text)

    if (globals.verbose >= 4):
        verbose_numpara_len = globals.verbose*10
        print(f"++++ convert_text_to_parachunks() paras[:{verbose_numpara_len}] ++++")
        print(f"{paras[:verbose_numpara_len]}")
        print("++++")
        
    
    processed_paras = []
    
    if (min_para_word_len != None):
        for para in paras:
            # **** XXXX
            #if para.isspace():
            #    continue
            para_words = para.split()
            if (len(para_words) > min_para_word_len):
                # enough words to include/be processed
                #para = para.strip()
                processed_paras.append(para)
        
    else:
        para_cat = ""

        for para in paras:
            #if para.isspace():
            #    continue
            para_cat = para_cat + para + '\n'
            para_cat_words = para_cat.split()
            if (len(para_cat_words) > min_parachunk_word_len):
                # enough concatenated words to include/be processed
                #para_cat = para_cat.strip()            
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

    min_para_word_len = globals.config['nlp'].get('min_para_word_len',None)
    min_para_confidence = globals.config['nlp'].get('min_para_confidence',None)

    min_parachunk_word_len = globals.config['nlp'].get('min_parachunk_word_len',None)
    min_parachunk_confidence = globals.config['nlp'].get('min_parachunk_confidence',None)

    min_termdist_confidence = globals.config['nlp']['min_termdist_confidence']
    
    para_chunks = convert_text_to_parachunks(text,min_para_word_len,min_parachunk_word_len)
    
    # Process each chunk and count paragraphs
    num_para_chunks = len(para_chunks)

    lrl_lingua_match_count  = 0
    lrl_lingua_match_paras  = []

    lrl_termdist_match_count  = 0
    lrl_termdist_match_paras  = []

    lrl_agreement_match_paras = []
    
    for para_chunk in para_chunks:
        lingua_paralang_rec = lingua_detector.detect_language_of(para_chunk)
        lingua_para_confidence = lingua_detector.compute_language_confidence(para_chunk, lingua_paralang_rec)

        termdist_para_confidence = termdist_compute_language_confidence(para_chunk,lang_dict_termvec_rec)

        show_para = False
        
        if (globals.verbose >= 2):
            #print(f"----\n    Para block:\n----\n{para_chunk}\n----\n")
            show_para = True
            
        if (globals.verbose > 1):            
            print(f"    Para predicted language = {lingua_paralang_rec.name} (confidence={lingua_para_confidence}) (low-resoure language cosine similarity score={termdist_para_confidence})")
            print("====")
            show_para = True
            
        if termdist_para_confidence >= min_termdist_confidence:
            print(f"==== LRL Cosine Similarity match  ({termdist_para_confidence}) ====")            
            lrl_termdist_match_count += 1
            lrl_termdist_match_paras.append(para_chunk)
            show_para = True
            
        if nlp_lang_supported:
            if lingua_paralang_rec.name == detect_langname and lingua_para_confidence >= min_para_confidence:
                print(f"==== LRL NLP Lingua match         ({lingua_para_confidence}) ====")            
                lrl_lingua_match_count += 1
                lrl_lingua_match_paras.append(para_chunk)
                show_para = True
                
            if lingua_paralang_rec.name == detect_langname and lingua_para_confidence >= min_para_confidence and termdist_para_confidence >= min_termdist_confidence:
                lrl_agreement_match_paras.append(para_chunk)
                show_para = True
                
        if show_para:
            print( "----")
            print(para_chunk)
            print( "----")
            print()
                        
    print(f"  Paras: lrl_termdist_match_count = {lrl_termdist_match_count} out of {num_para_chunks}")
    if nlp_lang_supported:    
        print(f"         lrl_lingua_match_count   = {lrl_lingua_match_count} out of {num_para_chunks}") 
    
    return {
        "num_paras"                 : num_para_chunks,
        "lrl_lingua_match_paras"    : lrl_lingua_match_paras,
        "lrl_termdist_match_paras"  : lrl_termdist_match_paras,
        "lrl_agreement_match_paras" : lrl_agreement_match_paras
    }
        

def detect_language_lingua(text,  detect_langname, lang_dict_termvec_rec):
    """Detect language with confidence level using Lingua.py"""

    nlp_lang_supported = is_lingua_supported_lang(detect_langname)
    
    # Full-text level analysis
    lingua_fulllang_rec = lingua_detector.detect_language_of(text)
    lingua_fullconf = lingua_detector.compute_language_confidence(text, lingua_fulllang_rec)

    if nlp_lang_supported:
        lrl_lingua_lang_rec = get_lingua_lang_rec(detect_langname)        
        lrl_lingua_fullconf = lingua_detector.compute_language_confidence(text, lrl_lingua_lang_rec)
        print(f"**** !!!! top lang {lingua_fulllang_rec} ({lingua_fulllang_rec.name}): fullconf={lingua_fullconf}")
        print(f"**** !!!! for lrl  {lrl_lingua_lang_rec} ({detect_langname}): fullconf={lrl_lingua_fullconf}")

    predicted_full_langname = None
    if lingua_fulllang_rec != None:
        predicted_full_langname = lingua_fulllang_rec.name
        
    # Paragraph-level analysis    
    detect_info = detect_para_language_lingua(text,detect_langname, nlp_lang_supported, lang_dict_termvec_rec)
    
    num_paras                = detect_info["num_paras"]
    lrl_lingua_match_paras   = detect_info["lrl_lingua_match_paras"]
    lrl_termdist_match_paras = detect_info["lrl_termdist_match_paras"]

    lrl_lingua_match_count   = len(lrl_lingua_match_paras)
    lrl_termdist_match_count = len(lrl_termdist_match_paras)

    lrl_match_count = lrl_lingua_match_count if (nlp_lang_supported) else lrl_termdist_match_count
    
    lrl_para_percentage = (lrl_match_count / num_paras) * 100 if num_paras > 0 else 0
      
    return {
        "full_lang": predicted_full_langname,
        "full_conf": round(lingua_fullconf, 2),
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
