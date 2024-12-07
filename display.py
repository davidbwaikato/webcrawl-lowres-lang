
#import const
import enums
import globals
import sql

def stats(lang_uc):
    print(f"--- Query Statistics for Language: {lang_uc} ---\n")

    lang_ic = lang_uc.capitalize()

    verbose = globals.verbose
    
    # Print total Queries with their types
    print("--- Query Counts by Type ---")
    queryCount = sql.count_query_types()
    for query, count in queryCount.items():
        print(f"Type: {query}, Count: {count}")
    print("\n")

    # Print Handled and Unhandled Queries
    handled_unhandled = sql.count_handled_unhandled_queries()
    print("--- Handled & Unhandled Queries ---")
    print(f"Handled Queries: {handled_unhandled.get('handled', 0)}")
    print(f"Unhandled Queries: {handled_unhandled.get('unhandled', 0)}\n")
    
    # Print Total Duplicate Queries
    print("--- Total Duplicate Queries ---")
    duplicate_queries = sql.count_duplicate_queries()
    print(f"Total Duplicate Queries: {len(duplicate_queries)}\n")

    # Show count of query types by total URLs found, and total for given lang
    print("--- Query Types by Total URLs and URLs with Given Language ---")
    #query_types_by_total_urls = sql.count_query_types_by_total_urls(lang_uc)
    query_types_by_total_urls = sql.count_query_types_by_total_urls_lrlparalang()
    for query_info in query_types_by_total_urls:
        print(f"Query Type: {query_info['type']}, Total URL Count: {query_info['total_url_count']}, Total URL with {lang_ic} Count: {query_info['total_url_with_lang_count']}\n")

    # Print top queries with most, least and language URLs
    print("--- Top Queries ---")
    #top_queries_most_urls = sql.get_top_queries_with_most_urls(lang_uc)
    top_queries_most_urls = sql.get_top_queries_with_most_urls_lrlparacount()
    print("--- Top Queries with Most URLs ---")
    for query_info in top_queries_most_urls[:5]:
        print(f"Index: {query_info['index']}, Query: {query_info['query']}, Type: {query_info['type']}, URL Count: {query_info['total_url_count']}, {lang_ic} URL Count: {query_info['lang_url_count']}")

    print("\n--- Top Queries with Least URLs ---")
    for query_info in top_queries_most_urls[-5:]:
        print(f"Index: {query_info['index']}, Query: {query_info['query']}, Type: {query_info['type']}, URL Count: {query_info['total_url_count']}, {lang_ic} URL Count: {query_info['lang_url_count']}")
    
    top_queries_most_urls.sort(key=lambda x: x['lang_url_count'], reverse=True)
    print("\n--- Top 5 Queries by Maori URLs ---")
    for query_info in top_queries_most_urls[:5]:
        print(f"Index: {query_info['index']}, Query: {query_info['query']}, Type: {query_info['type']}, URL Count: {query_info['total_url_count']}, {lang_ic} URL Count: {query_info['lang_url_count']}")
    print("\n")


    # Print the top queries with the most URLs for the specified language
    #doc_type_counts_for_language = sql.count_doc_types_for_language_total(lang_uc)
    doc_type_counts_for_language = sql.count_doc_types_for_language_total_lrlparacount()
    print(f"--- Document Type Counts (Total and in {lang_ic}) ---")
    for doc_info in doc_type_counts_for_language:
        print(f"Document Type: {doc_info['doc_type']}, Total Count: {doc_info['total_count']}, {lang_ic} Count: {doc_info['language_count']}")
    print("\n")

    # Print duplicate URL hashes and File Hashes
    print("--- Duplicate Hash Statistics ---")
    duplicate_url_hashes = sql.count_duplicate_url_hashes()
    print(f"Total Duplicate URL Hashes: {duplicate_url_hashes.get('total_duplicate_hashes', 0)}")
    print("Top 5 Duplicate URL Hashes:")
    for hash_info in duplicate_url_hashes.get('top_duplicate_hashes', []):
        for url_hash, count in hash_info.items():
            print(f"Hash: {url_hash}, Count: {count}")
    duplicate_file_hashes = sql.count_duplicate_file_hashes()
    print(f"Total Duplicate File Hashes: {duplicate_file_hashes.get('total_duplicate_file_hashes', 0)}")
    print("Top 5 Duplicate File Hashes:")
    for hash_info in duplicate_file_hashes.get('top_duplicate_file_hashes', []):
        for file_hash, count in hash_info.items():
            print(f"Hash: {file_hash}, Count: {count}")
    print("\n")

    #domain_results = sql.get_domain_counts(lang_uc)
    domain_results = sql.get_domain_counts_lrlparacount()

    # Sort the domains by total URLs and get the top and bottom 10
    sorted_domains = sorted(domain_results['domains'].items(), key=lambda x: x[1], reverse=True)
    top_10_domains = sorted_domains[:10]
    bottom_10_domains = sorted_domains[-10:]

    if verbose > 1:
        print(f"--- Top 10 Domains by Total URLs ---")
        for domain, count in top_10_domains:
            print(f"Domain: {domain}, Total URLs: {count}")

        print(f"\n--- Bottom 10 Domains by Total URLs ---")
        for domain, count in bottom_10_domains:
            print(f"Domain: {domain}, Total URLs: {count}")

        # Sort the language-specific domains by Maori URLs and get the top 10
        sorted_language_domains = sorted(domain_results['language_domains'].items(), key=lambda x: x[1], reverse=True)
        top_10_language_domains = sorted_language_domains[:10]
        bottom_10_language_domains = sorted_language_domains[-10:]
        print(f"\n--- Top 10 Domains by {lang_ic} URLs ---")
        for domain, count in top_10_language_domains:
            print(f"Domain: {domain}, {lang_ic} URLs: {count}")
        print(f"\n--- Bottom 10 Domains by Total URLs ---")
        for domain, count in bottom_10_language_domains:
            print(f"Domain: {domain}, Total URLs: {count}")
        print("\n")

    if verbose > 1:
        # Confidence and Paragraph Analysis
        print("--- Confidence and Paragraph Analysis ---")
        print("--- URLs with Low Confidence ---")
        #low_confidence = sql.count_low_confidence_urls(lang_uc)
        low_confidence = sql.count_low_confidence_urls_lrlparacount()
        print(f"Total URLs with Low Confidence: {low_confidence.get('total_low_confidence', 0)}")
        print("Top 5 Lowest Confidence URLs:")
        for url_info in low_confidence.get('top_5_lowest_confidence', []):
            print(f"URL: {url_info[0]}, Confidence: {url_info[1]}")
        print("\n--- URLs with High Confidence ---")
        #high_confidence = sql.count_high_confidence_urls(lang_uc)
        high_confidence = sql.count_high_confidence_urls_lrlparacount()
        print(f"Total URLs with High Confidence: {high_confidence.get('total_high_confidence', 0)}")
        print("Top 5 Highest Confidence URLs:")
        for url_info in high_confidence.get('top_5_highest_confidence', []):
            print(f"URL: {url_info[0]}, Confidence: {url_info[1]}")
        print("\n--- URLs with Low Paragraph Percentage and Low Confidence ---")
        #low_para_low_conf = sql.count_low_para_percent_low_confidence_urls(lang_uc)
        low_para_low_conf = sql.count_low_para_percent_low_confidence_urls_lrlparacount()
        print(f"Total: {low_para_low_conf.get('total_low_para_percent_low_confidence', 0)}")
        print("Top 5 Lowest Paragraph Percentage and Low Confidence URLs:")
        for url_info in low_para_low_conf.get('top_5_lowest_para_percent_low_confidence', []):
            print(f"URL: {url_info[0]}, Paragraph Percentage: {url_info[1]}, Confidence: {url_info[2]}")
        print("\n--- URLs with High Paragraph Percentage and High Confidence ---")
        #high_para_high_conf = sql.count_high_para_percent_high_confidence_urls(lang_uc)
        high_para_high_conf = sql.count_high_para_percent_high_confidence_urls_lrlparacount()
        print(f"Total: {high_para_high_conf.get('total_high_para_percent_high_confidence', 0)}")
        print("Top 5 Highest Paragraph Percentage and High Confidence URLs:")
        for url_info in high_para_high_conf.get('top_5_highest_para_percent_high_confidence', []):
            print(f"URL: {url_info[0]}, Paragraph Percentage: {url_info[1]}, Confidence: {url_info[2]}")
        print("\n")

        # Confidence Ranges
        print("Confidence Ranges")
        #range_results = sql.count_urls_by_confidence_and_paragraph_percentage_ranges(lang_uc)
        range_results = sql.count_urls_by_confidence_and_paragraph_percentage_ranges_lrlparacount()
        print("--- URL Counts by Confidence Range ---")
        for range, count in range_results['confidence'].items():
            print(f"Confidence Range {range}: {count} URLs")

        print("\n--- URL Counts by Paragraph Percentage Range ---")
        for range, count in range_results['paragraph'].items():
            print(f"Paragraph Percentage Range {range}: {count} URLs")
        print("\n")

    # Search Types Statistics
    print("--- Search Type Statistics ---")
    queries = sql.get_all_queries(lang_uc)
    num_queries = len(queries)
    
    g_urls  = sql.get_url_counts_by_type(lang_uc, enums.SearchEngineType.GOOGLE.value)
    ga_urls = sql.get_url_counts_by_type(lang_uc, enums.SearchEngineType.GOOGLE_API.value)
    b_urls  = sql.get_url_counts_by_type(lang_uc, enums.SearchEngineType.BING.value)
    ba_urls = sql.get_url_counts_by_type(lang_uc, enums.SearchEngineType.BING_API.value)

    total = g_urls["total_count"] + ga_urls["total_count"] + \
        b_urls["total_count"] + ba_urls["total_count"]

    lang_total = g_urls["para_lang_count"] + ga_urls["para_lang_count"] + \
        b_urls["para_lang_count"] + ba_urls["para_lang_count"]

    print(f"--- Google ---")
    print("Total Urls:", g_urls["total_count"])
    print("Not-Downloaded Urls:", g_urls["undownloaded_count"])
    #print("NLP-Unhandled Urls :", g_urls["unhandled_count"])
    print(f"Para {lang_ic} Urls:", g_urls["para_lang_count"])
    print("\n--- Google API ---")
    print("Total Urls:", ga_urls["total_count"])
    print("Not-Downloaded Urls:", ga_urls["undownloaded_count"])
    #print("NLP-Unhandled Urls :", ga_urls["unhandled_count"])
    print(f"Para {lang_ic} Urls:", ga_urls["para_lang_count"])

    print("\n--- Bing ---")
    print("Total Urls:", b_urls["total_count"])
    print("Not-Downloaded Urls:", b_urls["undownloaded_count"])
    #print("NLP-Unhandled Urls :", b_urls["unhandled_count"])
    print(f"Para {lang_ic} Urls:", b_urls["para_lang_count"])
    print("\n--- Bing API ---")
    print("Total Urls:", ba_urls["total_count"])
    print("Not-Downloaded Urls:", ba_urls["undownloaded_count"])
    #print("NLP-Unhandled Urls :", ba_urls["unhandled_count"])
    print(f"Para {lang_ic} Urls:", ba_urls["para_lang_count"])

    print(f"\n--- Overall Total for {lang_ic} ---")
    print("Total Queries:", num_queries)
    print("Total Urls:", total)
    print(f"Total {lang_ic} Urls:", lang_total)
