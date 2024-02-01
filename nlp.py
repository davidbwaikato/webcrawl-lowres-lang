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

def clean_text(text):
    # Replace instances where there are more than two consecutive newlines with just two.
    cleaned_text = re.sub(r'\n{3,}', '\n\n', text)
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

def process_text_in_chunks(text, detect:Language):
    """Gets an optimal chunk size to run paragraph language detection for"""
    words = text.split()
    num_words = len(words)
    short_text_threshold = 50
    medium_text_threshold = 200
    size = 500
    if num_words <= short_text_threshold:
        size = 50
    elif num_words <= medium_text_threshold:
        size = 200
    # Split the text into chunks
    paragraphs = [text[i:i + size] for i in range(0, len(text), size)]
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

def detect_language_lingua(text,  detect:Language, paragraphs=True):
    """Detect language with confidence level using Lingua.py"""
    language = detector.detect_language_of(text)
    confidence = detector.compute_language_confidence(text, language)
    percentage = 0
    if paragraphs:
        percentage = process_text_in_chunks(text, detect)
    name = None
    if language != None:
        name = language.name
    return {
        "lang": name,
        "condifence": round(confidence, 2),
        "percentage": round(percentage, 2),
    }

def run_nlp_algorithms(text, detect:Language):
    """Detect language of the text using multiple methods."""
    lingua = detect_language_lingua(text, detect)
    return {
        "lingua": lingua,
    }
