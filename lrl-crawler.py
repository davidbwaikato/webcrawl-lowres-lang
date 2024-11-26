#!/usr/bin/env python3

import argparse
import base64
import hashlib
import os
import random
import requests
import shutil
import threading
import time
import traceback

from fake_useragent import UserAgent
from selenium import webdriver

from lingua import Language
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

from datetime import datetime
from requests.exceptions import Timeout
from urllib.parse import urlparse, parse_qs

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import sql

# Import 'ssl' and disable default certificate verification for https URLs
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# LRL specific modules

import const
import globals

import utils
import nlp
import queries
import search


stop_event = threading.Event()

# If needing to accent-fold a string, see
#   https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string

def get_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="lrl-carwler.py",
        description="Focused web crawler for dowloading pages in low-resourced languages"
    )
    #parser.add_argument("lang", default=Language.MAORI.name,
    #                    help=f"language used for generating queries [Default={Language.MAORI.name}]")
    parser.add_argument("-v", "--verbose", type=int,
                        default=1, help=f"level of verbosity used for output [Default=1]")

    parser.add_argument("-wc", "--word_count", type=int, default=globals.config['word_count'],
                        help=f"how many words are used in a 'combined', 'phrase', and 'common_uncommon' generated query [Config Default={globals.config['word_count']}]")
    parser.add_argument("-qc", "--query_count", type=int, default=globals.config['query_count'],
                        help=f"how many queries of each type (single, combine, phrase, common_uncommon) are generated [Config Default={globals.config['query_count']}]")
    parser.add_argument("-se", "--search_engine", default=globals.config['search_engine'],
                        help=f"search engine used [Config Default={globals.config['search_engine']}]")
    parser.add_argument("-dws", "--download_with_selenium", action="store_true",
                        default=False, help=f"use Selenium-controlled web browser for page downloads [Default=False]")
    parser.add_argument("-art", "--apply_robots_txt", action="store_true",
                        default=False, help=f"use this option to turn on the robots.txt check (note: as the pages 'lrl-crawler.py' detects have been located via a web search engine, the identified download page has already been crawled, making it a reasonable assumption for 'lrl-crawler.pl' to skip this check, which is why it off by default) [Default=False]")

    parser.add_argument("-nt", "--num_threads", type=int, default=globals.config['num_threads'],
                        help=f"the number of threads that are used to run the querying and NLP processsing stages [Config Default={globals.config['num_threads']}]")

# The following is not currently supported
#    parser.add_argument("-sp", "--start_page", type=int, default=0,
#                        help=f"effectively, how many search result pages to skip over before processing results [Default=0]")
    parser.add_argument("-np", "--num_pages", type=int, default=globals.config['num_pages'],
                        help=f"number of pages of search results to process (x 4, for each query type) [Config Default={globals.config['num_pages']}]")

    parser.add_argument("-uh", "--unhandled", action="store_true",
                        default=False, help="flag to reprocess unhandled queries or urls")

    parser.add_argument("-a",  "--all", action="store_true",
                        default=False, help="flag to create queries, search and run NLP")
    parser.add_argument("-oq", "--only_querygen", action="store_true",
                        default=False, help="flag to only create queries")
    parser.add_argument("-os", "--only_search", action="store_true",
                        default=False, help="flag to only search queries")
    parser.add_argument("-on", "--only_nlp", action="store_true",
                        default=False, help="flag to only run NLP on URLs")

    parser.add_argument("-d",  "--display_stats", action="store_true",
                        default=False, help="flag to show details")

    parser.add_argument("-squ", "--set_queries_unhandled", action="store_true",
                        default=False, help="Flag to set all queries as unhandled")
    parser.add_argument("-cu", "--clean_urls", action="store_true",
                        default=False, help="Testing flag")
    parser.add_argument("-test", "--test", action="store_true",
                        default=False, help="Testing flag")

    parser.add_argument("lang",
                        help=f"language used for generating queries")
    
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

# Consider working with web-driver!!!
#  https://www.geeksforgeeks.org/get-all-text-of-the-page-using-selenium-in-python/

# From Sulan's earlier work:
#   https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/win64/chromedriver-win64.zip

def init_driver(driver_name):
    driver = None

    ua = UserAgent()
    user_agent = ua.random

    if driver_name == "geckodriver":
        from selenium.webdriver.firefox.options import Options
    
        options = Options()
        options.add_argument(f'--user-agent={user_agent}')
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
    elif driver_name == "chromedriver":
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument(f'--user-agent={user_agent}')

        # Assume sourcing SETUP.bash puts the chromedriver on PATH, so no longer need to explicitly set this
        #driver = webdriver.Chrome(chrome_options=options, executable_path=globals.config['chromedriver'])
        driver = webdriver.Chrome(chrome_options=options)
    
    return driver


def download_and_save(url_id, url, download_with_selenium,apply_robots_txt, save_dir='downloads', url_timeout=10):

    try:
        # Extract root domain from URL
        print(f"  download_and_save(), url_id={url_id}")
        print(f"  url={url}")
        
        parsed_url = urlparse(url)
        root_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        if (root_domain == "://"):
            print(f"URL is a relative link (from the search engine result set page) => skipping")
            return 0

        # Found some examples where RobotFileParser() returned False, but a manual check
        # of the robots.txt file for that site show the URL to be OK for downloading
        #
        # ?? Maybe something to do with Crawl-Rate field (??), however a specially built
        #    test case with sleep() also failed
        #
        # => As all URLs we access have been found by a web search, support a config setting
        #    option for skipping the test
        
        if (apply_robots_txt):
            
            rp = RobotFileParser()
            rp.set_url(root_domain+'/robots.txt')
            rp.read()

            # Return if not allowed to crawl this URL
            if not rp.can_fetch("*", url):
                print(f"Crawling forbidden by robots.txt for URL: {url}")
                return 0

        # **** XXXX
        # Ensure the save directory exists
        #if not os.path.exists(save_dir):
        #    os.makedirs(save_dir)

        # Fetch the content with a timeout and allow redirects
        #print(f"Away to get URL {url}")

        driver = None
        
        response = requests.get(url, verify=False, timeout=url_timeout, allow_redirects=True)
        if response.status_code != 200:
            return 0
        
        response_content = None

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

        if doc_type == "html" and download_with_selenium:
            driver = init_driver(globals.config['driver'])
            driver.get(url)

            # Working on the assumption that driver.get() only returns
            # when page is loaded into browser

            # If this turns out not to be the case, then ...
            # Consider putting in some form of wait, either time.sleep(5) or
            #    https://stackoverflow.com/questions/5868439/wait-for-page-load-in-selenium

            # StackOverflow articles discuss that driver returns content in UTF8            
            # where it can, however (emperically) it is still a binary string
            # at this point and needs to be encoded for hashlib.sha256() to work
            response_content = driver.page_source.encode("utf-8")
            # print(f"Selenium encoded: {response_content[:300]}")
            driver.quit();
        else:
            response_content = response.content
            
        # Hash the content
        sha256_hash = hashlib.sha256()
        sha256_hash.update(response_content)
        file_hash = sha256_hash.hexdigest()

        filename = file_hash + "." + doc_type
        filepath = os.path.join(save_dir, filename)

        # Save the content if the hash does not exist in the database
        if os.path.exists(filepath):
            # Try to search and assign database value first
            if set_values_from_existing(url_id, file_hash) == 1:
                return 1
            print(f"File with hash {file_hash} already exists in downloads.")
            return {"path": filepath, "hash": file_hash, "doc_type": doc_type}

        #print("----")
        #print(f"filepath = {filepath}")
        #print(response_content[:100])
        
        with open(filepath, 'wb') as f:
            f.write(response_content)
            
        return {"path": filepath, "hash": file_hash, "doc_type": doc_type}

    except requests.exceptions.Timeout:
        print("Request timed out: ", url)
        return 0
    except Exception as e:
        print(f"Error getting file for {url}: {e}")        
        return 0
    
def search_and_fetch(query, search_engine_type, num_pages=1, **kwargs):
    """Fetch Google search results and update"""
    query_id = query[0]
    text = query[1]
    driver = None

    # Get where to save the data
    if search_engine_type == const.GOOGLE_SELENIUM or search_engine_type == const.BING_SELENIUM:
        driver = init_driver(globals.config['driver'])        

    if search_engine_type == const.GOOGLE_SELENIUM:
        engine = const.GOOGLE
    elif search_engine_type == const.BING_SELENIUM:
        engine = const.BING
    else:
        engine = search_engine_type

    count = 1
    urls = []
    while count <= num_pages:
        if search_engine_type == const.GOOGLE:
            temp = search.google(text, count)
        elif search_engine_type == const.GOOGLE_SELENIUM:
            temp = search.google_selenium(text, driver, count)
        elif search_engine_type == const.BING:
            temp = search.bing(text, count)
        elif search_engine_type == const.BING_SELENIUM:
            temp = search.bing_selenium(text, driver, count)
        elif search_engine_type == const.GOOGLE_API:
            temp = search.google_api(text, globals.config['google']['key'],
                              globals.config['google']['cx'], count, **kwargs)
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
    urls = utils.remove_blacklisted(urls, globals.config['blacklist'])
    if len(urls) == 0:
        return
    # Prepare the URL data for insertion => not currently downloaded, so url handle=False
    url_data = [(query_id, engine, url, utils.hash_url(url), False) for url in urls]
    # Insert URLs into the database (only the new ones)
    # print(url_data)
    sql.insert_urls_many(url_data)

def search_worker(sub_queries, search_engine_type, num_pages, tcount):
    for query in sub_queries:
        # Check if the stop event is set
        if stop_event.is_set():
            return

        now = datetime.now()
        print(f"Thread {tcount} ============ Search Stage @ {now.strftime('%H:%M:%S')} ============ query: {query}")
        search_and_fetch(query, search_engine_type, num_pages)

        sleep_delay = globals.config['sleep_delay']
        randomized_sleep_delay = sleep_delay + random.randint(0,sleep_delay)
        print(f"  pausing for {randomized_sleep_delay} secs")
        time.sleep(randomized_sleep_delay)

def nlp_worker(sub_urls, download_with_selenium,apply_robots_txt,  detect:Language, tcount):
    for url in sub_urls:
        if url[7] == 1: # already handled it
            #print("{0}".format(url))
            #print("{0} {1}".format(url[0], url[7]))
            continue
        now = datetime.now()
        print(f"Thread {tcount} ============ NLP Stage @ {now.strftime('%H:%M:%S')} ============ URL id {url[0]}")
        try:
            # Check if the stop event is set
            if stop_event.is_set():
                return
            result = download_and_save(url[0], url[3], download_with_selenium,apply_robots_txt,
                                       globals.config['downloads_dir'], globals.config['url_timeout'])
            if result == 1:
                print(f"Thread {tcount} ============ ============ EXISTING URL id {url[0]}")
                continue
            if result == 0:
                sql.set_url_as_handled(url[0])
                continue

            extracted_text = nlp.extract_text_from_file(result["path"], result["doc_type"])
            if extracted_text == None:
                sql.set_url_as_handled(url[0])
                print(f"Thread {tcount} xxxxxxxxxxxx deleting (no extracted text) xxxxxxxxxxxx")
                delete_file(result["path"])                
                continue
            cleaned_extracted_text = nlp.clean_text(extracted_text)
            # Guard against the cleaned text now being nothing but 100% whitespace
            if cleaned_extracted_text.isspace():
                sql.set_url_as_handled(url[0])
                print(f"Thread {tcount} xxxxxxxxxxxx deleting (text all whitespace) xxxxxxxxxxxx")
                delete_file(result["path"])                                
                continue            

            langs = nlp.run_nlp_algorithms(cleaned_extracted_text, globals.lang_uc) # **** XXXX
            if langs["lingua"]["lang"] == None:
                sql.set_url_as_handled(url[0])
                print(f"Thread {tcount} xxxxxxxxxxxx deleting (NLP failed to detect language) xxxxxxxxxxxx")
                delete_file(result["path"])                                
                continue
            if langs["lingua"]["lang"] != detect.name:
                print(f"Thread {tcount} xxxxxxxxxxxx deleting (detected {langs['lingua']['lang'].capitalize()} != {detect.name.capitalize()}) xxxxxxxxxxxx")
                delete_file(result["path"])
                
            sql.update_url(url[0], result["hash"], result["doc_type"], langs["lingua"]["lang"], langs["lingua"]["confidence"], langs["lingua"]["percentage"])
            # print("{0} {1} {2} HANDLED".format(tcount, url[0], @ now.strftime('%H:%M:%S')))

        except FileNotFoundError as e:
            # print("{0} {1} {2} HANDLED".format(tcount, url[0], @ now.strftime('%H:%M:%S')))
            sql.set_url_as_handled(url[0])
            print(f"Thread {tcount} File not found")
        except Exception as e:
            sql.set_url_as_handled(url[0])
            print(f"Thread {tcount} Error in NLP: {e}")
            if (globals.verbose > 2):
                print(traceback.format_exc())
        
def validate_args(args):
    try:
        # Validate lang
        valid_langs = [Language.MAORI.name] # **** XXXX
        if globals.lang_uc not in valid_langs:
            raise ValueError(f"Invalid language provided. Valid languages are: {valid_langs}")
        
        # Validate word_count, query_count, num_threads, num_pages
        for arg in [globals.args.word_count, globals.args.query_count, globals.args.num_threads, globals.args.num_pages]:
            if arg and not isinstance(arg, int) and arg <= 0:
                raise ValueError(
                    f"Expected a positive integer, but got: {arg}")
            
        # Validate search_engine
        valid_search_engine_types = [const.GOOGLE, const.GOOGLE_API, const.GOOGLE_SELENIUM,
                                     const.BING,   const.BING_API,   const.BING_SELENIUM]
        if globals.args.search_engine and globals.args.search_engine not in valid_search_engine_types:
            raise ValueError(
                f"Invalid search type provided: {globals.args.search_engine}. Valid options are: {valid_search_engine_types}")
    except Exception as e:
        print(e)
        exit(0)

def display_stats(lang_uc):
    print(f"--- Query Statistics for Language: {lang_uc} ---\n")

    # Print total Queries with their types
    print("--- Query Counts by Type ---")
    queryCount = sql.count_query_types()
    for query, count in queryCount.items():
        print(f"Type: {query}, Count: {count}")
    print("\n")

    # Print Handled and Unhandled Queries
    # **** XXXX
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
    query_types_by_total_urls = sql.count_query_types_by_total_urls(lang_uc)
    for query_info in query_types_by_total_urls:
        print(f"Query Type: {query_info['type']}, Total URL Count: {query_info['total_url_count']}, Total URL with {lang_uc} Count: {query_info['total_url_with_lan_count']}\n")

    # Print top queries with most, least and language URLs
    print("--- Top Queries ---")
    top_queries_most_urls = sql.get_top_queries_with_most_urls(lang_uc)
    print("--- Top Queries with Most URLs ---")
    for query_info in top_queries_most_urls[:5]:
        print(f"Index: {query_info['index']}, Query: {query_info['query']}, Type: {query_info['type']}, URL Count: {query_info['total_url_count']}, {lang_uc} URL Count: {query_info['lan_url_count']}")

    print("\n--- Top Queries with Least URLs ---")
    for query_info in top_queries_most_urls[-5:]:
        print(f"Index: {query_info['index']}, Query: {query_info['query']}, Type: {query_info['type']}, URL Count: {query_info['total_url_count']}, {lang_uc} URL Count: {query_info['lan_url_count']}")
    
    top_queries_most_urls.sort(key=lambda x: x['lan_url_count'], reverse=True)
    print("\n--- Top 5 Queries by Maori URLs ---")
    for query_info in top_queries_most_urls[:5]:
        print(f"Index: {query_info['index']}, Query: {query_info['query']}, Type: {query_info['type']}, URL Count: {query_info['total_url_count']}, {lang_uc} URL Count: {query_info['lan_url_count']}")
    print("\n")


    # Print the top queries with the most URLs for the specified language
    doc_type_counts_for_language = sql.count_doc_types_for_language_total(lang_uc)
    print(f"--- Document Type Counts (Total and in {lang_uc}) ---")
    for doc_info in doc_type_counts_for_language:
        print(f"Document Type: {doc_info['doc_type']}, Total Count: {doc_info['total_count']}, {lang_uc} Count: {doc_info['language_count']}")
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

    domain_results = sql.get_domain_counts(lang_uc)
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
    print(f"\n--- Top 10 Domains by {lang_uc} URLs ---")
    for domain, count in top_10_language_domains:
        print(f"Domain: {domain}, {lang_uc} URLs: {count}")
    print(f"\n--- Bottom 10 Domains by Total URLs ---")
    for domain, count in bottom_10_language_domains:
        print(f"Domain: {domain}, Total URLs: {count}")
    print("\n")

    # Confidence and Paragraph Analysis
    print("--- Confidence and Paragraph Analysis ---")
    print("--- URLs with Low Confidence ---")
    low_confidence = sql.count_low_confidence_urls(lang_uc)
    print(f"Total URLs with Low Confidence: {low_confidence.get('total_low_confidence', 0)}")
    print("Top 5 Lowest Confidence URLs:")
    for url_info in low_confidence.get('top_5_lowest_confidence', []):
        print(f"URL: {url_info[0]}, Confidence: {url_info[1]}")
    print("\n--- URLs with High Confidence ---")
    high_confidence = sql.count_high_confidence_urls(lang_uc)
    print(f"Total URLs with High Confidence: {high_confidence.get('total_high_confidence', 0)}")
    print("Top 5 Highest Confidence URLs:")
    for url_info in high_confidence.get('top_5_highest_confidence', []):
        print(f"URL: {url_info[0]}, Confidence: {url_info[1]}")
    print("\n--- URLs with Low Paragraph Percentage and Low Confidence ---")
    low_para_low_conf = sql.count_low_para_percent_low_confidence_urls(lang_uc)
    print(f"Total: {low_para_low_conf.get('total_low_para_percent_low_confidence', 0)}")
    print("Top 5 Lowest Paragraph Percentage and Low Confidence URLs:")
    for url_info in low_para_low_conf.get('top_5_lowest_para_percent_low_confidence', []):
        print(f"URL: {url_info[0]}, Paragraph Percentage: {url_info[1]}, Confidence: {url_info[2]}")
    print("\n--- URLs with High Paragraph Percentage and High Confidence ---")
    high_para_high_conf = sql.count_high_para_percent_high_confidence_urls(lang_uc)
    print(f"Total: {high_para_high_conf.get('total_high_para_percent_high_confidence', 0)}")
    print("Top 5 Highest Paragraph Percentage and High Confidence URLs:")
    for url_info in high_para_high_conf.get('top_5_highest_para_percent_high_confidence', []):
        print(f"URL: {url_info[0]}, Paragraph Percentage: {url_info[1]}, Confidence: {url_info[2]}")
    print("\n")
    # Confidence Ranges
    print("Confidence Ranges")
    range_results = sql.count_urls_by_confidence_and_paragraph_percentage_ranges(lang_uc)
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
    g_urls = sql.get_url_counts_by_type(lang_uc, const.GOOGLE)
    ga_urls = sql.get_url_counts_by_type(lang_uc, const.GOOGLE_API)
    b_urls = sql.get_url_counts_by_type(lang_uc, const.BING)
    ba_urls = sql.get_url_counts_by_type(lang_uc, const.BING_API)
    total = g_urls["total_count"] + ga_urls["total_count"] + \
        b_urls["total_count"] + ba_urls["total_count"]
    lan_total = g_urls["lan_count"] + ga_urls["lan_count"] + \
        b_urls["lan_count"] + ba_urls["lan_count"]
    print(f"--- Google ---")
    print("Total Urls:", g_urls["total_count"])
    print("Unhandled Urls:", g_urls["unhandled_count"])
    print(f"{lang_uc} Urls:", g_urls["lan_count"])
    print("\n--- Google API ---")
    print("Total Urls:", ga_urls["total_count"])
    print("Unhandled Urls:", ga_urls["unhandled_count"])
    print(f"{lang_uc} Urls:", ga_urls["lan_count"])
    print("\n--- Bing ---")
    print("Total Urls:", b_urls["total_count"])
    print("Unhandled Urls:", b_urls["unhandled_count"])
    print(f"{lang_uc} Urls:", b_urls["lan_count"])
    print("\n--- Bing API ---")
    print("Total Urls:", ba_urls["total_count"])
    print("Unhandled Urls:", ba_urls["unhandled_count"])
    print(f"{lang_uc} Urls:", ba_urls["lan_count"])
    print(f"\n--- Overall Total for {lang_uc} ---")
    print("Total Queries:", len(queries))
    print("Total Urls:", total)
    print(f"Total {lang_uc} Urls:", lan_total)
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
    globals.config = utils.read_config()
    globals.args = get_args()

    lang = globals.args.lang
    lang_lc = lang.lower()
    lang_uc = lang.upper()
    
    globals.lang    = lang
    globals.lang_lc = lang_lc
    globals.lang_uc = lang_uc
    
    globals.verbose = globals.args.verbose
    
    if globals.args.test:
        test()
    if globals.args.set_queries_unhandled:
        sql.set_all_queries_unhandled()
        print("Set all queries as unhandled.")
    if globals.args.clean_urls:
        print("Cleaning URLs in database (this might take a while).")
        urls = sql.get_all_urls()
        final_urls = clean_urls(urls)
        print("Finished cleaning URLs in database.")
        exit(0)
    try:

        validate_args(globals.args)

        # **** XXXX
        # This shouldn't be a minus arg => always needed!
        lang_uc          = globals.lang_uc
        
        #word_count    = globals.args.word_count    or globals.config.get('word_count')
        #query_count   = globals.args.query_count   or globals.config.get('query_count')
        #search_engine = globals.args.search_engine or globals.config.get('search_engine')
        #num_threads   = globals.args.num_threads   or globals.config.get('num_threads')
        #num_pages     = globals.args.num_pages     or globals.config.get('num_pages')

        # The following are now explicitly set to their config defaults if not give on CLI
        word_count    = globals.args.word_count
        query_count   = globals.args.query_count
        search_engine = globals.args.search_engine
        num_threads   = globals.args.num_threads
        num_pages     = globals.args.num_pages

        # Only controlable from the commandline
        unhandled_flag = globals.args.unhandled

        # Ensure the downloads directory exists
        downloads_dir = globals.config.get('downloads_dir')
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)
        
        # Create the database
        sql.create(reset=False)
        if globals.args.display_stats:
            display_stats(lang_uc)
            exit(0)
#        # Get dictionary from UDHR PDFs
#        if extract_dictionary:
#            extractOrig(reset=False)

        # Queries
        if globals.args.only_querygen or globals.args.all:
            print("Generating Queries.")
            queries = queries.generate_all(lang_uc, word_count, query_count)
        # Search
        if globals.args.only_search or globals.args.all:
            print("Running Search.")
            # Get all relevant queries from the database
            queries = sql.get_all_queries(lang_uc, True) # **** XXXX Want to get all the unhandled ones
            # Split queries into sub-lists for each thread
            split_queries = [queries[i::num_threads]
                             for i in range(num_threads)]
            # Create and start threads
            threads = []
            print("Starting search threads.")
            tcount = 1
            
            for sub_queries in split_queries:
                t = threading.Thread(target=search_worker, args=(
                    sub_queries, search_engine, num_pages, tcount))
                threads.append(t)
                t.start()
                tcount += 1
                
            # Wait for all threads to finish
            for t in threads:
                if stop_event.is_set():
                    exit(0)
                t.join()

            # Set query as handled
            print("Setting queries as handled.")
            for query in queries:
                sql.set_query_as_handled(query[0])
            print("All Search-threads have finished.")
        # NLP
        if globals.args.only_nlp or globals.args.all:
            # Get all relevant queries from the database
            urls = sql.get_all_urls(True) # **** XXXX unhandled_flag ??
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
                    sub_urls, globals.args.download_with_selenium,globals.args.apply_robots_txt,  Language.MAORI, tcount)) # **** XXXX hard-wire MAORI, but passing object, note name!!!
                threads.append(t)
                t.start()
                tcount += 1
            # Wait for all threads to finish
            for t in threads:
                if stop_event.is_set():
                    exit(0)
                t.join()
            # **** XXXX why is this block commented out???
            # Set query as handled
            # print("Setting urls as handled.")
            # for url in urls:
            #     set_url_as_handled(url[0])
            print("All Download+NLP-threads have finished.")

        if globals.args.all:
            display_stats(lang_uc)
        
    except KeyboardInterrupt:
        print("Stopping all threads")
        # Signal all threads to stop
        stop_event.set()
        # Wait for all threads to finish
        for t in threads:
            t.join()
        print("All threads have been stopped.")
