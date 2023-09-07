import json
import random


def load_language_dictionary(language):
    try:
        """Load the dictionary for a specific language from its JSON file"""
        filename = f"dicts/common_words_{language.lower()}.json"
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except:
        print(f"Dictionary for {language} not found")
        return None


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


def generate_all(lang, word_count=3, query_count=5):
    """Generate all types of queries for a language"""
    word_dict = load_language_dictionary(lang)
    if word_dict is None:
        exit()
    queries = []
    queries.extend(combined_word_queries(word_dict, 1, query_count))
    queries.extend(combined_word_queries(word_dict, word_count, query_count))
    queries.extend(phrase_queries(word_dict, word_count, query_count))
    queries.extend(common_uncommon_combinations(
        word_dict, word_count, query_count))
    queries = order_and_remove_duplicates(queries)
    return queries
