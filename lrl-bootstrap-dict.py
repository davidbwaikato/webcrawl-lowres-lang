#!/usr/bin/env python3

from enum import Enum
import argparse

#import const
import extract
import fileutils
import globals


def get_args():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        prog="lrl-generate-dict.py",
        description="Generate a frequency-count based 'dictionary' for the specified language"
    )

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

    lang = globals.args.lang
    lang_lc = lang.lower()
    lang_uc = lang.upper()
    
    globals.lang    = lang
    globals.lang_lc = lang_lc
    globals.lang_uc = lang_uc
    
    globals.verbose = globals.args.verbose
        
    lang_initialcap = globals.args.lang.capitalize();
    force   = globals.args.force
    verbose = globals.args.verbose
    
    # Generate freqency count 'dictionaries' from UDHR PDF/Text file(s)
    extract.extract_udhr(lang_initialcap,force)
            
