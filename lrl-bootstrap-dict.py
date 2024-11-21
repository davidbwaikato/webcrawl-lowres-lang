#!/usr/bin/env python3

#import os

import argparse

from extract import extractNew

import const


def get_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Arguments that can be used")
    parser.add_argument("-l", "--lang", default="all",
                        help=f"language used for generating queries [Default=all]")
    parser.add_argument("-f", "--force", action="store_true",
                        default=False, help=f"force regeneration of frequency count 'dictionaries', overriding existing JSON file(s)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        default=False, help=f"verbose output")

    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    
    lang    = args.lang.capitalize();
    force   = args.force
    verbose = args.verbose
    
    # Generate freqency count 'dictionaries' from UDHR PDFs
    extractNew(lang,force,verbose)
            
