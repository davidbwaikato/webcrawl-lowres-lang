#!/usr/bin/env python3

import spacy
from spacy.language import Language
from spacy.pipeline import Sentencizer

def read_file(filename):
    """Read file in UTF-8 format"""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

    
# Load a blank SpaCy model
nlp = spacy.blank("xx")  # "xx" is a blank multilingual language model

# Add a sentencizer to the pipeline
sentencizer = Sentencizer(punct_chars=[".", "!", "?"])
nlp.add_pipe("sentencizer")

# Example text
text_paras = read_file("TONGAN-PARAS.txt")


# Process text
doc = nlp(text_paras)

# Print sentences
for sent in doc.sents:
    print(sent.text)
    
