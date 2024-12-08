#!/usr/bin/env python3

import sys
import argparse

#import const
import enums
import extract
import fileutils
import globals
import nlp



    
def get_args():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        prog="lrl-generate-dict.py",
        description="Generate a frequency-count based 'dictionary' for the specified language"
    )

    parser.add_argument("-ld", "--lang_detect", type=enums.LangDetect, choices=list(enums.LangDetect), default=enums.LangDetect.lingua,
                        help=f"Algorithm used to detect low-resourced language: 'cossim' performs the Cosine Similarity measure on term-vectors of text and is always guaranteed to be available;  'lingua' uses the Python NLP package Lingua, as long as the language is one of the languages the package supports (75 languages at the time of writing)  [Default=lingua]")

    parser.add_argument("-om", "--output_mode", type=enums.DictOutputMode, choices=list(enums.DictOutputMode), default=enums.DictOutputMode.merge,
                        help=f"Control how the new frequency-count based dictionary file is generated [Default=merge]")
    
    parser.add_argument("-v", "--verbose", type=int, default=1,
                        help=f"level of verbosity used for output [Default=1]")
    
    parser.add_argument("-f", "--force", action="store_true", default=False,
                        help=f"force regeneration of frequency count 'dictionaries', overriding existing JSON file(s)")
        
    # Positional argument
    parser.add_argument("lang",
                        help=f"the language of the frequency-count based 'dictionary' to generate (if 'all' then all languages in config.json are processed)")
    
    return parser.parse_args()


if __name__ == "__main__":

    globals.config = fileutils.read_config()
    globals.args = get_args()

    lang_detect_algorithm = globals.args.lang_detect
    
    lang = globals.args.lang
    lang_lc = lang.lower()
    lang_uc = lang.upper()
    
    globals.lang    = lang
    globals.lang_lc = lang_lc
    globals.lang_uc = lang_uc
    
    globals.verbose = globals.args.verbose
    
    force   = globals.args.force
    verbose = globals.args.verbose

    globals.config['downloads_dir'] = globals.config['downloads_dir_root'] + "-" + lang_lc
    globals.config['database_file'] = globals.config['database_file_root'] + "-" + lang_lc + ".db"

    lang_initialcap = globals.args.lang.capitalize();

    nlp_lang_supported = nlp.is_lingua_supported_lang(lang_uc)
    
    if lang_detect_algorithm == enums.LangDetect.lingua and not nlp_lang_supported:
        print( "----",file=sys.stderr)
        #print(f"NLP Language Detection does not support '{lang_initialcap}, switching to using 'cossim' (Cosine Similarity)",file=sys.stderr)
        print(f"Error: NLP Language Detection does not support '{lang_initialcap}'. Consider switching to using --lang_detect cossim (Cosine Similarity)",file=sys.stderr)
        print( "----",file=sys.stderr)
        exit(1)
                            
    # Generate freqency count 'dictionaries' from downloaded web pages,
    # targetting the para that are in the NLP lrl-detected language

    extract.extract_database_downloaded(lang_initialcap,force, nlp_lang_supported,lang_detect_algorithm)
            
