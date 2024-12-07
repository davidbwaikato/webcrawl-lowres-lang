import json
import random

import fileutils
import globals
import sql


def combined_word_queries(word_dict, word_count=2, query_count=10):
    """Generate combined word queries"""
    words = list(word_dict.keys())
    queries = []
    for _ in range(query_count):
        query = ' '.join(random.sample(words, word_count))
        if word_count == 1:
            queries.append({"query": query, "type": "single"})
        else:
            queries.append({"query": query, "type": "combined"})
    return queries


def phrase_queries(word_dict, phrase_length=2, query_count=10):
    """Generate phrase queries by picking consecutive words from the list"""
    words = list(word_dict.keys())
    queries = []
    for _ in range(query_count):
        start_index = random.randint(0, len(words) - phrase_length)
        query = ' '.join(words[start_index:start_index + phrase_length])
        queries.append({"query": query, "type": "phrase"})
    return queries


def common_uncommon_combinations(word_dict, word_count=2, query_count=10):
    """Combine most common words with least common words based on their frequencies"""
    # Split the words into common and uncommon based on their frequencies
    common_words_list = [word for word, freq in word_dict.items() if freq > 10]
    uncommon_words_list = [word for word,
                           freq in word_dict.items() if freq <= 10]
    queries = []
    for _ in range(query_count):
        # Pick half from the common words and the other half from the uncommon words
        selected_common = random.sample(common_words_list, word_count // 2)
        selected_uncommon = random.sample(
            uncommon_words_list, word_count - (word_count // 2))
        # Combine them to form the query
        query = ' '.join(selected_common + selected_uncommon)
        queries.append({"query": query, "type": "common_uncommon"})
    return queries


def order_and_remove_duplicates(queries):
    """Convert each query to a sorted tuple and remove duplicates"""
    sorted_queries = {
        tuple(sorted(item["query"].split())): item["type"] for item in queries}
    return [{"query": " ".join(query), "type": sorted_queries[query]} for query in sorted_queries]

def exclude_english_lexicon(lrl_word_dict):
    english_word_dict = fileutils.load_english_dictionary_ref()

    if globals.verbose >= 2:
        print(f"  Size of low-resource language word_dict before English exclusion: {len(lrl_word_dict)}")
    
    for en_word in english_word_dict.keys():
        if en_word in lrl_word_dict:
            if globals.verbose >= 3:
                print(f"  Excluding: {en_word}")
            del lrl_word_dict[en_word]

    if globals.verbose >= 2:
        print(f"  Size of low-resource language word_dict after English exclusion: {len(lrl_word_dict)}")


def generate_all(lang_uc, exclude_english_lexicon_option, word_count, query_count):
    """Create all types of queries for a language"""
    lang_lc = lang_uc.lower()
    lang_ic = lang_uc.capitalize()
    
    print(f"  Loading frequency-based dictionary for {lang_ic}")    
    word_dict = fileutils.load_language_dictionary(lang_uc)
    
    if word_dict is None:
        print(f"Unigram frequency dictionary for '{lang_ic}' language not found")
        exit(1)

    if exclude_english_lexicon_option:
        print("  Excluding English lexicon")
        exclude_english_lexicon(word_dict)
        
    print("  Generating  queries")
        
    queries = []
    queries.extend(combined_word_queries(word_dict, 1, query_count))
    queries.extend(combined_word_queries(word_dict, word_count, query_count))
    queries.extend(phrase_queries(word_dict, word_count, query_count))
    queries.extend(common_uncommon_combinations(
        word_dict, word_count, query_count))
    queries = order_and_remove_duplicates(queries)
    # foreach query, save it in the database
    unique = 0
    for query in queries:
        # Insert the query
        print("Inserting", query)
        if sql.insert_query_if_not_exists(query["query"], query["type"], lang_uc):
            unique += 1
    print(f"Created {unique} unique queries")
    return queries
