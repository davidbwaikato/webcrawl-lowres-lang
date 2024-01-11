import os
import time
import hashlib
import argparse
import requests
from const import GOOGLE, GOOGLE_SELENIUM, GOOGLE_API, BING, BING_API, BING_SELENIUM, TOTAL, TOTAL, UNHANDLED, ITEMS, URL, URL_HASH, QUERY
from extract import extract
from queries import generate_all
from helpers import hash_url, read_config, remove_blacklisted
from search import google, google_selenium, google_api, bing, bing_selenium
from selenium import webdriver
import threading
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from sql import get_url_file_hash, get_url_by_id, save_bing_url, create, insert_query_if_not_exists, get_all_queries, get_url_counts_by_query_id, insert_urls_many, get_all_urls, get_url_counts_by_type, set_query_as_handled, hash_exists_in_db, set_url_as_handled, set_all_queries_unhandled, update_url
from sql import count_query_types, count_urls_per_query_type, get_top_3_queries_with_most_urls, query_with_least_urls, count_queries_with_zero_urls_by_type, get_most_common_urls
from nlp import extract_text_from_file, run_nlp_algorithms, clean_text
from lingua import Language
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
# pip install -r requirements.txt
stop_event = threading.Event()
import datetime
from requests.exceptions import Timeout
from urllib.parse import urlparse, parse_qs
import base64

# py app.py -nlp -nt 20


# def get_all_query_files(directory="queries"):
#     """Returns a list of all files in a directory"""
#     return [os.path.join(directory, file) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]


def get_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Arguments that can be used")
    parser.add_argument("-lan", "--lan", default="Māori",
                        help="Language for queries")
    parser.add_argument("-w", "--word_count", type=int,
                        default=3, help="Word count")
    parser.add_argument("-q", "--query_count", type=int,
                        default=5, help="Query count")
    parser.add_argument("-st", "--search_type",
                        default=GOOGLE_SELENIUM, help="Search type")
    parser.add_argument("-nt", "--num_threads", type=int,
                        default=5, help="Number of threads")
    parser.add_argument("-p", "--pages", type=int, default=5,
                        help="Number of pages to search")
    parser.add_argument("-e", "--extract_dictionary",
                        action="store_true", help="Flag to extract dictionary")
    parser.add_argument("-u", "--unhandled_queries", action="store_true",
                        default=True, help="Flag to get unhandled queries")
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
    parser.add_argument("-sau", "--set_all_unhandled", action="store_true",
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
    existing = get_url_file_hash(url_id, file_hash)
    if existing is None or existing[7] == 1:
        return 0
    update_url(url_id, file_hash, existing[6], existing[8], existing[10], existing[9])
    return 1

def download_and_save(url_id, url, save_dir='downloads', timeout=10):
    try:
        # Ensure the save directory exists
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        # Fetch the content with a timeout and allow redirects
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
            doc_type = "unknown"
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
        print(f"Error getting file: {e}")
        return 0
    
def search_and_fetch(query, type, page=1, **kwargs):
    """Fetch Google search results and update"""
    query_id = query[0]
    text = query[1]
    driver = None
    config = read_config()
    # Get where to save the data
    if type == GOOGLE_SELENIUM or type == BING_SELENIUM:
        options = Options()
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f'--user-agent={user_agent}')
        driver = webdriver.Chrome(
            chrome_options=options, executable_path=config['chromedriver'])
    if type == GOOGLE_SELENIUM:
        engine = GOOGLE
    elif type == BING_SELENIUM:
        engine = BING
    else:
        engine = type
    count = 1
    urls = []
    while count <= page:
        if type == GOOGLE:
            temp = google(text, count)
        elif type == GOOGLE_SELENIUM:
            temp = google_selenium(text, driver, count)
        elif type == BING_SELENIUM:
            temp = bing_selenium(text, driver, count)
        elif type == GOOGLE_API:
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
    insert_urls_many(url_data)

def search_worker(sub_queries, search_type, pages):
    for query in sub_queries:
        # Check if the stop event is set
        if stop_event.is_set():
            return
        search_and_fetch(query, search_type, pages)
        time.sleep(5)
# 400
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
                set_url_as_handled(url[0])
                continue
            extracted_text = extract_text_from_file(result["path"], result["doc_type"])
            #extracted_text = extract_text_from_file("downloads\\test.pdf", "pdf")
            if extracted_text == None:
                set_url_as_handled(url[0])
                continue
            cleaned_extracted_text = clean_text(extracted_text)
            langs = run_nlp_algorithms(cleaned_extracted_text, Language.MAORI)
            if langs["lingua"]["lang"] == None:
                set_url_as_handled(url[0])
                continue
            if langs["lingua"]["lang"] != detect.name:
                delete_file(result["path"])
            update_url(url[0], result["hash"], result["doc_type"], langs["lingua"]["lang"], langs["lingua"]["condifence"], langs["lingua"]["percentage"])
            # print("{0} {1} {2} HANDLED".format(tcount, url[0], now.time()))
        except FileNotFoundError as e:
            # print("{0} {1} {2} HANDLED".format(tcount, url[0], now.time()))
            set_url_as_handled(url[0])
            print(f"{tcount} File not found")
        except Exception as e:
            set_url_as_handled(url[0])
            print(f"{tcount} Error in NLP: {e}")
        
def validate_args(args):
    try:
        # Validate lang
        valid_langs = ["Māori"]
        if args.lan and args.lan not in valid_langs:
            raise ValueError("Invalid language provided.")
        # Validate word_count, query_count, num_threads, pages
        for arg in [args.word_count, args.query_count, args.num_threads, args.pages]:
            if arg and not isinstance(arg, int) and arg <= 0:
                raise ValueError(
                    f"Expected a positive integer, but got: {arg}")
        # Validate search_type
        valid_search_types = [GOOGLE, GOOGLE_API,
                              GOOGLE_SELENIUM, BING, BING_API, BING_SELENIUM]
        if args.search_type and args.search_type not in valid_search_types:
            raise ValueError(
                f"Invalid search type provided: {args.search_type}")
    except Exception as e:
        print(e)
        exit(0)

def display(lan):
    queries = get_all_queries(lan)
    g_urls = get_url_counts_by_type(lan, GOOGLE)
    ga_urls = get_url_counts_by_type(lan, GOOGLE_API)
    b_urls = get_url_counts_by_type(lan, BING)
    ba_urls = get_url_counts_by_type(lan, BING_API)
    total = g_urls["total_count"] + ga_urls["total_count"] + \
        b_urls["total_count"] + ba_urls["total_count"]
    lan_total = g_urls["lan_count"] + ga_urls["lan_count"] + \
        b_urls["lan_count"] + ba_urls["lan_count"]
    print(f"--- Google ---")
    print("Total Urls:", g_urls["total_count"])
    print("Unhandled Urls:", g_urls["unhandled_count"])
    print(f"{lan} Urls:", g_urls["lan_count"])
    print(f"--- Google API ---")
    print("Total Urls:", ga_urls["total_count"])
    print("Unhandled Urls:", ga_urls["unhandled_count"])
    print(f"{lan} Urls:", ga_urls["lan_count"])
    print(f"--- Bing ---")
    print("Total Urls:", b_urls["total_count"])
    print("Unhandled Urls:", b_urls["unhandled_count"])
    print(f"{lan} Urls:", b_urls["lan_count"])
    print(f"--- Bing API ---")
    print("Total Urls:", ba_urls["total_count"])
    print("Unhandled Urls:", ba_urls["unhandled_count"])
    print(f"{lan} Urls:", ba_urls["lan_count"])
    print(f"--- {lan} ---")
    print("Total Queries:", len(queries))
    print("Total Urls:", total)
    print(f"Total {lan}:", lan_total)
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
                    save_bing_url(url[0], final_url)
                except Exception:
                    continue

if __name__ == "__main__":
    args = get_args()
    if args.test:
        # result = count_query_types()
        # print(result)
        # result = count_urls_per_query_type()
        # print(result)
        # result = get_top_3_queries_with_most_urls()
        # print(result)
        # result = query_with_least_urls()
        # print(result)
        # result = count_queries_with_zero_urls_by_type()
        # print(result)
        result = count_queries_with_zero_urls_by_type()
        print(result)
        exit(0)
    if args.set_all_unhandled:
        set_all_queries_unhandled()
        print("Set all queries as unhandled.")
    if args.clean_urls:
        print("Cleaning URLs in database (this might take a while).")
        urls = get_all_urls()
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
        num_threads = args.num_threads or config.get('num_threads')
        pages = args.pages or config.get('pages')
        create_queries = args.create_queries
        extract_dictionary = args.extract_dictionary
        unhandled_queries = args.unhandled_queries
        # Create the database
        create(reset=False)
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
            # foreach query, save it in the database
            unique = 0
            for query in queries:
                # Insert the query
                print("Inserting", query)
                if insert_query_if_not_exists(query["query"], query["type"], lan):
                    unique += 1
            print(f"Created {unique} unique queries")
        # Search
        if args.search or args.all:
            print("Running Search.")
            # Get all relevant queries from the database
            queries = get_all_queries(lan, unhandled_queries)
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
                set_query_as_handled(query[0])
            print("All threads have finished.")
        # NLP
        if args.nlp or args.all:
            # Get all relevant queries from the database
            urls = get_all_urls(unhandled_queries)
            # Split queries into sub-lists for each thread
            split_urls = [urls[i::num_threads]
                             for i in range(num_threads)]
            # Create and start threads
            threads = []
            print("Starting nlp threads.")
            tcount = 1
            for sub_urls in split_urls:
                t = threading.Thread(target=nlp_worker, args=(
                    sub_urls,Language.MAORI, tcount))
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

# Todo: Add Bing API search
# Todo: Run NLP on the results
# Todo: Add console commands
# Todo: Add file structure to support other languages
# Some websites contain previews to documents which should be downloaded instead
# https://atojs.natlib.govt.nz/cgi-bin/atojs?a=d&d=AJHR1891-II.2.2.5.3&e=-------10--1------0--
# def get_pdf_link_from_webpage(url):
#     response = requests.get(url)
#     soup = BeautifulSoup(response.content, 'html.parser')
#     # List of potential patterns to search for
#     patterns = ["Download a printable PDF version", "download pdf", "download document"]
#     for pattern in patterns:
#         pdf_link_tag = soup.find("a", string=lambda text: pattern.lower() in text.lower())
#         if pdf_link_tag:
#             return pdf_link_tag['href']
#     return None
