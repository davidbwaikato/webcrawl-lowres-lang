#!/usr/bin/env python3

import os
import time
import random
import shutil
import hashlib
import argparse
import requests
from extract import extract
from queries import generate_all
from helpers import hash_url, read_config, remove_blacklisted
from search import google, google_selenium, google_api, bing, bing_selenium
from selenium import webdriver
import threading
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from nlp import extract_text_from_file, run_nlp_algorithms, clean_text
from lingua import Language
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
# pip install -r requirements.txt
stop_event = threading.Event()
import datetime
from requests.exceptions import Timeout
from urllib.parse import urlparse, parse_qs
import base64
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import sql
import const

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# py app.py -nlp -nt 20


# def get_all_query_files(directory="queries"):
#     """Returns a list of all files in a directory"""
#     return [os.path.join(directory, file) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]


def get_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Arguments that can be used")
    parser.add_argument("-lan", "--lan", default=Language.MAORI.name,
                        help="Language for queries")
    parser.add_argument("-w", "--word_count", type=int,
                        default=3, help="Word count")
    parser.add_argument("-q", "--query_count", type=int,
                        default=5, help="Query count")
    parser.add_argument("-st", "--search_type",
                        default=const.BING_SELENIUM, help="Search type")
    parser.add_argument("-nt", "--threads", type=int,
                        default=5, help="Number of threads")
    parser.add_argument("-p", "--pages", type=int, default=5,
                        help="Number of pages to search")
    parser.add_argument("-e", "--extract_dictionary",
                        action="store_true", help="Flag to extract dictionary")
    parser.add_argument("-uh", "--handled", action="store_true",
                        default=True, help="Flag to get use handled queries or urls")
    parser.add_argument("-a", "--all", action="store_true",
                        default=False, help="Flag to create queries, search and run NLP")
    parser.add_argument("-cq", "--create_queries", action="store_true",
                        default=False, help="Flag to only create queries")
    parser.add_argument("-s", "--search", action="store_true",
                        default=False, help="Flag to only search queries")
    parser.add_argument("-nlp", "--nlp", action="store_true",
                        default=False, help="Flag to only run NLP on URLs")
    parser.add_argument("-d", "--display", action="store_true",
                        default=False, help="Flag to show details")
    parser.add_argument("-sau", "--set_queries_unhandled", action="store_true",
                        default=False, help="Flag to set all queries as unhandled")
    parser.add_argument("-cu", "--clean_urls", action="store_true",
                        default=False, help="Testing flag")
    parser.add_argument("-test", "--test", action="store_true",
                        default=False, help="Testing flag")
    return parser.parse_args()

def delete_file(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        print(f"File not found: {path}")
    except Exception as e:
        print(f"Error deleting file: {e}")

def set_values_from_existing(url_id, file_hash):
    existing = sql.get_url_file_hash(url_id, file_hash)
    if existing is None or existing[7] == 1:
        return 0
    sql.update_url(url_id, file_hash, existing[6], existing[8], existing[10], existing[9])
    return 1

def download_and_save(url_id, url, save_dir='downloads', timeout=10):
    try:
        # Extract root domain from URL
        parsed_url = urlparse(url)
        root_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        # Check robots.txt for the site
        rp = RobotFileParser()
        rp.set_url(os.path.join(root_domain, 'robots.txt'))
        rp.read()
        # Return if not allowed to crawl this URL
        if not rp.can_fetch("*", url):
            print(f"Crawling forbidden by robots.txt for URL: {url}")
            return 0
        # Ensure the save directory exists
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        # Fetch the content with a timeout and allow redirects
        print(f"Away to get URL {url}")
        response = requests.get(url, verify=False, timeout=timeout, allow_redirects=True)
        if response.status_code != 200:
            return 0
        # Hash the content
        sha256_hash = hashlib.sha256()
        sha256_hash.update(response.content)
        file_hash = sha256_hash.hexdigest()
        # Identify the content type
        content_type = response.headers.get('content-type')
        if "html" in content_type:
            doc_type = "html"
        elif "pdf" in content_type:
            doc_type = "pdf"
        elif "msword" in content_type or "vnd.openxmlformats-officedocument" in content_type:
            doc_type = "docx"
        else:
            print("Unknown content type: ", content_type)
            return 0
        filename = file_hash + "." + doc_type
        filepath = os.path.join(save_dir, filename)
        # Save the content if the hash does not exist in the database
        if os.path.exists(filepath):
            # Try to search and assign database value first
            if set_values_from_existing(url_id, file_hash) == 1:
                return 1
            print(f"File with hash {file_hash} already exists in downloads.")
            return {"path": filepath, "hash": file_hash, "doc_type": doc_type}
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return {"path": filepath, "hash": file_hash, "doc_type": doc_type}
    except requests.exceptions.Timeout:
        print("Request timed out: ", url)
        return 0
    except Exception as e:
        print(f"Error getting file for {url}: {e}")        
        return 0
    
def search_and_fetch(query, type, page=1, **kwargs):
    """Fetch Google search results and update"""
    query_id = query[0]
    text = query[1]
    driver = None
    config = read_config()
    # Get where to save the data
    if type == const.GOOGLE_SELENIUM or type == const.BING_SELENIUM:
        options = Options()
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f'--user-agent={user_agent}')
        #driver = webdriver.Chrome(
        #    chrome_options=options, executable_path=config['chromedriver'])
        #driver = webdriver.Firefox(
        #    gecko_options=options, executable_path=config['geckodriver'])
        driver = webdriver.Firefox()
    if type == const.GOOGLE_SELENIUM:
        engine = const.GOOGLE
    elif type == const.BING_SELENIUM:
        engine = const.BING
    else:
        engine = type
    count = 1
    urls = []
    while count <= page:
        if type == const.GOOGLE:
            temp = google(text, count)
        elif type == const.GOOGLE_SELENIUM:
            temp = google_selenium(text, driver, count)
        elif type == const.BING:
            temp = bing(text, count)
        elif type == const.BING_SELENIUM:
            temp = bing_selenium(text, driver, count)
        elif type == const.GOOGLE_API:
            temp = google_api(text, config['google']['key'],
                              config['google']['cx'], count, **kwargs)
            if temp == 429:
                print("Google API rate limit reached, exiting.")
                stop_event.set()
                return
        if not temp:
            break
        urls.extend(temp)
        count += 1
    # Quit the driver after the loop ends
    if driver:
        driver.quit()
    # Remove blacklisted URLs
    urls = remove_blacklisted(urls, config['blacklist'])
    if len(urls) == 0:
        return
    # Prepare the URL data for insertion
    url_data = [(query_id, engine, url, hash_url(url), True) for url in urls]
    # Insert URLs into the database (only the new ones)
    # print(url_data)
    sql.insert_urls_many(url_data)

def search_worker(sub_queries, search_type, pages):
    for query in sub_queries:
        # Check if the stop event is set
        if stop_event.is_set():
            return
        search_and_fetch(query, search_type, pages)
        time.sleep(5)

def nlp_worker(sub_urls, detect:Language, tcount):
    for url in sub_urls:
        if url[7] == 0:
            #print("{0}".format(url))
            #print("{0} {1}".format(url[0], url[7]))
            continue
        now = datetime.datetime.now()
        print(f"{tcount} ============ {now.time()} ============ {url[0]}")
        try:
            # Check if the stop event is set
            if stop_event.is_set():
                return
            result = download_and_save(url[0], url[3])
            if result == 1:
                print(f"{tcount} ============ ============ EXISTING {url[0]}")
                continue
            if result == 0:
                sql.set_url_as_handled(url[0])
                continue
            extracted_text = extract_text_from_file(result["path"], result["doc_type"])
            #extracted_text = extract_text_from_file("downloads\\test.pdf", "pdf")
            if extracted_text == None:
                sql.set_url_as_handled(url[0])
                continue
            cleaned_extracted_text = clean_text(extracted_text)
            langs = run_nlp_algorithms(cleaned_extracted_text, Language.MAORI.name)
            if langs["lingua"]["lang"] == None:
                sql.set_url_as_handled(url[0])
                continue
            if langs["lingua"]["lang"] != detect.name:
                delete_file(result["path"])
            sql.update_url(url[0], result["hash"], result["doc_type"], langs["lingua"]["lang"], langs["lingua"]["condifence"], langs["lingua"]["percentage"])
            # print("{0} {1} {2} HANDLED".format(tcount, url[0], now.time()))
        except FileNotFoundError as e:
            # print("{0} {1} {2} HANDLED".format(tcount, url[0], now.time()))
            sql.set_url_as_handled(url[0])
            print(f"{tcount} File not found")
        except Exception as e:
            sql.set_url_as_handled(url[0])
            print(f"{tcount} Error in NLP: {e}")
        
def validate_args(args):
    try:
        # Validate lang
        valid_langs = [Language.MAORI.name]
        if args.lan and args.lan not in valid_langs:
            raise ValueError("Invalid language provided.")
        # Validate word_count, query_count, threads, pages
        for arg in [args.word_count, args.query_count, args.threads, args.pages]:
            if arg and not isinstance(arg, int) and arg <= 0:
                raise ValueError(
                    f"Expected a positive integer, but got: {arg}")
        # Validate search_type
        valid_search_types = [const.GOOGLE, const.GOOGLE_API,
                              const.GOOGLE_SELENIUM, const.BING, const.BING_API, const.BING_SELENIUM]
        if args.search_type and args.search_type not in valid_search_types:
            raise ValueError(
                f"Invalid search type provided: {args.search_type}")
    except Exception as e:
        print(e)
        exit(0)

def display(lan):
    print(f"--- Query Statistics for Language: {lan} ---\n")

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

    # Show count of query types by total URLs found, and total for given lan
    print("--- Query Types by Total URLs and URLs with Given Language ---")
    query_types_by_total_urls = sql.count_query_types_by_total_urls(lan)
    for query_info in query_types_by_total_urls:
        print(f"Query Type: {query_info['type']}, Total URL Count: {query_info['total_url_count']}, Total URL with {lan} Count: {query_info['total_url_with_lan_count']}\n")

    # Print top queries with most, least and language URLs
    print("--- Top Queries ---")
    top_queries_most_urls = sql.get_top_queries_with_most_urls(lan)
    print("--- Top Queries with Most URLs ---")
    for query_info in top_queries_most_urls[:5]:
        print(f"Index: {query_info['index']}, Query: {query_info['query']}, Type: {query_info['type']}, URL Count: {query_info['total_url_count']}, {lan} URL Count: {query_info['lan_url_count']}")

    print("\n--- Top Queries with Least URLs ---")
    for query_info in top_queries_most_urls[-5:]:
        print(f"Index: {query_info['index']}, Query: {query_info['query']}, Type: {query_info['type']}, URL Count: {query_info['total_url_count']}, {lan} URL Count: {query_info['lan_url_count']}")
    
    top_queries_most_urls.sort(key=lambda x: x['lan_url_count'], reverse=True)
    print("\n--- Top 5 Queries by Maori URLs ---")
    for query_info in top_queries_most_urls[:5]:
        print(f"Index: {query_info['index']}, Query: {query_info['query']}, Type: {query_info['type']}, URL Count: {query_info['total_url_count']}, {lan} URL Count: {query_info['lan_url_count']}")
    print("\n")


    # Print the top queries with the most URLs for the specified language
    doc_type_counts_for_language = sql.count_doc_types_for_language_total(lan)
    print(f"--- Document Type Counts (Total and in {lan}) ---")
    for doc_info in doc_type_counts_for_language:
        print(f"Document Type: {doc_info['doc_type']}, Total Count: {doc_info['total_count']}, {lan} Count: {doc_info['language_count']}")
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

    domain_results = sql.get_domain_counts(lan)
    # Sort the domains by total URLs and get the top and bottom 10
    sorted_domains = sorted(domain_results['domains'].items(), key=lambda x: x[1], reverse=True)
    top_10_domains = sorted_domains[:10]
    bottom_10_domains = sorted_domains[-10:]

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
    print(f"\n--- Top 10 Domains by {lan} URLs ---")
    for domain, count in top_10_language_domains:
        print(f"Domain: {domain}, {lan} URLs: {count}")
    print(f"\n--- Bottom 10 Domains by Total URLs ---")
    for domain, count in bottom_10_language_domains:
        print(f"Domain: {domain}, Total URLs: {count}")
    print("\n")

    # Confidence and Paragraph Analysis
    print("--- Confidence and Paragraph Analysis ---")
    print("--- URLs with Low Confidence ---")
    low_confidence = sql.count_low_confidence_urls(lan)
    print(f"Total URLs with Low Confidence: {low_confidence.get('total_low_confidence', 0)}")
    print("Top 5 Lowest Confidence URLs:")
    for url_info in low_confidence.get('top_5_lowest_confidence', []):
        print(f"URL: {url_info[0]}, Confidence: {url_info[1]}")
    print("\n--- URLs with High Confidence ---")
    high_confidence = sql.count_high_confidence_urls(lan)
    print(f"Total URLs with High Confidence: {high_confidence.get('total_high_confidence', 0)}")
    print("Top 5 Highest Confidence URLs:")
    for url_info in high_confidence.get('top_5_highest_confidence', []):
        print(f"URL: {url_info[0]}, Confidence: {url_info[1]}")
    print("\n--- URLs with Low Paragraph Percentage and Low Confidence ---")
    low_para_low_conf = sql.count_low_para_percent_low_confidence_urls(lan)
    print(f"Total: {low_para_low_conf.get('total_low_para_percent_low_confidence', 0)}")
    print("Top 5 Lowest Paragraph Percentage and Low Confidence URLs:")
    for url_info in low_para_low_conf.get('top_5_lowest_para_percent_low_confidence', []):
        print(f"URL: {url_info[0]}, Paragraph Percentage: {url_info[1]}, Confidence: {url_info[2]}")
    print("\n--- URLs with High Paragraph Percentage and High Confidence ---")
    high_para_high_conf = sql.count_high_para_percent_high_confidence_urls(lan)
    print(f"Total: {high_para_high_conf.get('total_high_para_percent_high_confidence', 0)}")
    print("Top 5 Highest Paragraph Percentage and High Confidence URLs:")
    for url_info in high_para_high_conf.get('top_5_highest_para_percent_high_confidence', []):
        print(f"URL: {url_info[0]}, Paragraph Percentage: {url_info[1]}, Confidence: {url_info[2]}")
    print("\n")
    # Confidence Ranges
    print("Confidence Ranges")
    range_results = sql.count_urls_by_confidence_and_paragraph_percentage_ranges(lan)
    print("--- URL Counts by Confidence Range ---")
    for range, count in range_results['confidence'].items():
        print(f"Confidence Range {range}: {count} URLs")

    print("\n--- URL Counts by Paragraph Percentage Range ---")
    for range, count in range_results['paragraph'].items():
        print(f"Paragraph Percentage Range {range}: {count} URLs")
    print("\n")

    # Search Types Statistics
    print("--- Search Type Statistics ---")
    queries = sql.get_all_queries(lan)
    g_urls = sql.get_url_counts_by_type(lan, const.GOOGLE)
    ga_urls = sql.get_url_counts_by_type(lan, const.GOOGLE_API)
    b_urls = sql.get_url_counts_by_type(lan, const.BING)
    ba_urls = sql.get_url_counts_by_type(lan, const.BING_API)
    total = g_urls["total_count"] + ga_urls["total_count"] + \
        b_urls["total_count"] + ba_urls["total_count"]
    lan_total = g_urls["lan_count"] + ga_urls["lan_count"] + \
        b_urls["lan_count"] + ba_urls["lan_count"]
    print(f"--- Google ---")
    print("Total Urls:", g_urls["total_count"])
    print("Unhandled Urls:", g_urls["unhandled_count"])
    print(f"{lan} Urls:", g_urls["lan_count"])
    print("\n--- Google API ---")
    print("Total Urls:", ga_urls["total_count"])
    print("Unhandled Urls:", ga_urls["unhandled_count"])
    print(f"{lan} Urls:", ga_urls["lan_count"])
    print("\n--- Bing ---")
    print("Total Urls:", b_urls["total_count"])
    print("Unhandled Urls:", b_urls["unhandled_count"])
    print(f"{lan} Urls:", b_urls["lan_count"])
    print("\n--- Bing API ---")
    print("Total Urls:", ba_urls["total_count"])
    print("Unhandled Urls:", ba_urls["unhandled_count"])
    print(f"{lan} Urls:", ba_urls["lan_count"])
    print(f"\n--- Overall Total for {lan} ---")
    print("Total Queries:", len(queries))
    print("Total Urls:", total)
    print(f"Total {lan} Urls:", lan_total)
    exit(0)

def clean_urls(urls):
    for url in urls:
        if 'bing.com' in url[3]:
            query_params = parse_qs(urlparse(url[3]).query)
            if 'u' in query_params:
                encoded_url = query_params['u'][0]
                try:
                    temp = "{0}{1}".format(encoded_url[2:], "==")
                    final_url = base64.b64decode(temp).decode("utf-8")
                    print("Saving {0}".format(url[0]))
                    sql.save_bing_url(url[0], final_url)
                except Exception:
                    continue

def test():
    num_files = 100
    source_dir = 'downloads'
    destination_dir = 'test'
    # Ensure the destination directory exists
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    # Get a list of all files in the source directory
    all_files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
    # Initialize an empty list to keep track of files copied
    copied_files = []
    while len(copied_files) < num_files and all_files:
        # Randomly select a file
        file_to_copy = random.choice(all_files)
        all_files.remove(file_to_copy)
        # Construct full file path
        source_file_path = os.path.join(source_dir, file_to_copy)
        destination_file_path = os.path.join(destination_dir, file_to_copy)
        # If the file does not exist in the destination directory, copy it
        if not os.path.exists(destination_file_path):
            shutil.copy(source_file_path, destination_file_path)
            copied_files.append(file_to_copy)
    print(f"Copied {len(copied_files)} files from {source_dir} to {destination_dir}.")
    exit(0)

if __name__ == "__main__":
    args = get_args()
    if args.test:
        test()
    if args.set_queries_unhandled:
        sql.set_all_queries_unhandled()
        print("Set all queries as unhandled.")
    if args.clean_urls:
        print("Cleaning URLs in database (this might take a while).")
        urls = sql.get_all_urls()
        final_urls = clean_urls(urls)
        print("Finished cleaning URLs in database.")
        exit(0)
    try:
        config = read_config()
        validate_args(args)
        lan = args.lan
        word_count = args.word_count or config.get('word_count')
        query_count = args.query_count or config.get('query_count')
        search_type = args.search_type or config.get('search_type')
        num_threads = args.threads or config.get('num_threads')
        pages = args.pages or config.get('pages')
        create_queries = args.create_queries
        extract_dictionary = args.extract_dictionary
        handled = args.handled
        # Create the database
        sql.create(reset=False)
        if args.display:
            display(lan)
            exit(0)
        # Get dictionary from UDHR PDFs
        if extract_dictionary:
            extract(reset=False)
        # Queries
        if args.create_queries or args.all:
            print("Running Queries.")
            queries = generate_all(lan, word_count, query_count)
        # Search
        if args.search or args.all:
            print("Running Search.")
            # Get all relevant queries from the database
            queries = sql.get_all_queries(lan, handled)
            # Split queries into sub-lists for each thread
            split_queries = [queries[i::num_threads]
                             for i in range(num_threads)]
            # Create and start threads
            threads = []
            print("Starting search threads.")
            for sub_queries in split_queries:
                t = threading.Thread(target=search_worker, args=(
                    sub_queries, search_type, pages))
                threads.append(t)
                t.start()
            # Wait for all threads to finish
            for t in threads:
                if stop_event.is_set():
                    exit(0)
                t.join()
            # Set query as handled
            print("Setting queries as handled.")
            for query in queries:
                sql.set_query_as_handled(query[0])
            print("All threads have finished.")
        # NLP
        if args.nlp or args.all:
            # Get all relevant queries from the database
            urls = sql.get_all_urls(handled)
            print(f"Number of urls to be processed by NLP: {len(urls)}")
            # Split queries into sub-lists for each thread
            split_urls = [urls[i::num_threads]
                             for i in range(num_threads)]
            # Create and start threads
            threads = []
            print("Starting nlp threads.")
            tcount = 1
            for sub_urls in split_urls:
                t = threading.Thread(target=nlp_worker, args=(
                    sub_urls, Language.MAORI, tcount))
                threads.append(t)
                t.start()
                tcount += 1
            # Wait for all threads to finish
            for t in threads:
                if stop_event.is_set():
                    exit(0)
                t.join()
            # Set query as handled
            # print("Setting urls as handled.")
            # for url in urls:
            #     set_url_as_handled(url[0])
            print("All threads have finished.")
        display(lan)
    except KeyboardInterrupt:
        print("Stopping all threads")
        # Signal all threads to stop
        stop_event.set()
        # Wait for all threads to finish
        for t in threads:
            t.join()
        print("All threads have been stopped.")
