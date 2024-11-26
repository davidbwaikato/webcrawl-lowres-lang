from bs4 import BeautifulSoup
import PyPDF2
import docx
import re
from lingua import Language, LanguageDetectorBuilder
#detector = LanguageDetectorBuilder.from_all_languages().with_preloaded_language_models().build()
linguaLanguages = [Language.ENGLISH, Language.MAORI]
detector = LanguageDetectorBuilder.from_languages(*linguaLanguages).build()
# import spacy
# import nltk
# from langdetect import DetectorFactory
# DetectorFactory.seed = 0
# from langdetect import detect
# from spacy_langdetect import LanguageDetector
# from nltk.corpus import stopwords
# from googletrans import Translator

import globals

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

def clean_text(text,reg_expr=r'\n{3,}',replace_str='\n\n'):
    # Replace instances where there are more than two consecutive newlines with just two.
    cleaned_text = re.sub(reg_expr, replace_str, text)
    return cleaned_text

def extract_text_from_file(filepath, doc_type):
    if doc_type == "html":
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            return soup.get_text()
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

def convert_text_to_parachunks(text):
    """Gets optimal sized chunks to run paragraph language detection for"""

    if (globals.verbose > 1):
        verbose_char_len = globals.verbose*100
        print(f"---- process_text_in_chunks() text[:{verbose_char_len}]----")
        print(text[:verbose_char_len])
        print("----")

    cleaned_text = clean_text(text, r'\n{2,}','\n')    
    paras = cleaned_text.splitlines()

    min_para_word_len = globals.config['nlp']['min_para_word_len']

    para_chunks = []
    
    para_cat = ""

    for para in paras:
        para_cat = para_cat + para + '\n'
        para_cat_words = para_cat.split()
        if (len(para_cat_words) > min_para_word_len):
            # enough concatenated words to process
            para_cat = para_cat.strip()            
            para_chunks.append(para_cat)
            para_cat = ""
            
    return para_chunks

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

    if (globals.verbose > 1):
        print("---- process_text_in_chunks() ----")
        print(text[:globals.verbose*100])
        print("----")
        
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
        language = detector.detect_language_of(chunk)
        if language == detect:
            count += 1

    # Calculate the percentage
    percentage = (count / total) * 100 if total > 0 else 0
    return percentage


def detect_para_language_lingua(text, detect_name:Language):
    """Working with (potetially contatenated paragraphs to reach config set min word count) run language detection on paragraphs"""

    para_chunks = convert_text_to_parachunks(text)
    
    # Process each chunk and count paragraphs
    num_para_chunks = len(para_chunks)
    lang_match_count = 0

    #print(f"++++")
    
    for para_chunk in para_chunks:
        language = detector.detect_language_of(para_chunk)
        confidence = detector.compute_language_confidence(para_chunk, language)

        if (globals.verbose > 2):
            print(f"    Para chunk:\n--\n{para_chunk}\n--")
        if (globals.verbose > 1):
            print(f"    Para chunk Predicted language = {language} (confidence={confidence}\n")
    
        if language.name == detect_name:
            lang_match_count += 1

    #print(f"++++")            
    print(f"  Para Chunks: lang_match_count={lang_match_count} out of {num_para_chunks}")
    #print(f"++++")
    
    return lang_match_count, num_para_chunks 



def detect_language_lingua(text,  detect_name:Language, paragraphs=True):
    """Detect language with confidence level using Lingua.py"""

    language = detector.detect_language_of(text)
    confidence = detector.compute_language_confidence(text, language)

    percentage = 0
    if paragraphs:
        lang_match_count,num_para_chunks = detect_para_language_lingua(text,detect_name)
        percentage = (lang_match_count / num_para_chunks) * 100 if num_para_chunks > 0 else 0
      
    name = None
    if language != None:
        name = language.name

    return {
        "lang": name,
        "confidence": round(confidence, 2),
        "percentage": round(percentage, 2),
    }

def run_nlp_algorithms(text, detect_name:Language):
    """Detect language of the text using (for now) lingua method."""
    lingua = detect_language_lingua(text, detect_name)
    
    return {
        "lingua": lingua,
    }
