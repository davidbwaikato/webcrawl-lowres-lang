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


# Import 'ssl' and disable default certificate verification for https URLs
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# LRL specific modules

import const
import globals

import display
import fileutils
import nlp
import queries
import sql
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

    parser.add_argument("-ra", "--run_all", action="store_true",
                        default=False, help="flag to run all stages: query generation, perform web searches, download result sets, and run NLP over the downloaded files")
    parser.add_argument("-rqg", "--run_querygen", action="store_true",
                        default=False, help="flag to run the create query stage")
    parser.add_argument("-rws", "--run_websearch", action="store_true",
                        default=False, help="flag to run the search queries stage")
    parser.add_argument("-rd", "--run_download", action="store_true",
                        default=False, help="flag to run the download stage")
    parser.add_argument("-rn", "--run_nlp", action="store_true",
                        default=False, help="flag to run the NLP stage on the downloaded pages")

    parser.add_argument("-ds", "--display_stats", action="store_true",
                        default=False, help="flag to show details")

    parser.add_argument("-squ", "--set_queries_unhandled", action="store_true",
                        default=False, help="Flag to mark all generated queries in the database as unhandled")
    parser.add_argument("-sdu", "--set_downloads_unhandled", action="store_true",
                        default=False, help="Flag to mark all urls in the database as not downloaded")
    parser.add_argument("-snu", "--set_nlp_unhandled", action="store_true",
                        default=False, help="Flag to mark all urls in the database as not nlp-processed")

    # Positional argument
    parser.add_argument("lang",
                        help=f"language used for generating queries")
    
    return parser.parse_args()



def set_nlp_values_from_existing(url_id, file_hash):
    # Only interested in a previous 'file_hash' in the database if it has
    # been nlp-handled (i.e. langinfo values computed)
    existing = sql.get_url_duplicate_handled_file_hash(url_id, file_hash)

    if existing is None:
        return 0

    # **** XXXX
    # Clone across the values for 'doc_type', 'full_lang', 'confidence', 'paragraph_lan'
    #sql.update_url(url_id, file_hash, existing[6], existing[9], existing[11], existing[10])

    doc_type      = existing[6]
    full_lang     = existing[9]
    confidence    = existing[11]
    paragraph_lan = existing[10]

    # Clone the entry, based on the duplicate entry's values
    update_url_fileinfo(url_id, file_hash, doc_type, downloaded=True)
    update_url_langinfo(url_id, full_lang, confidence, paragraph_lan, handled=True)
    
    return 1


_gecko_service = None

def init_driver(driver_name):
    global _gecko_service

    # For working with webdriver-manager, see
    #   https://pypi.org/project/webdriver-manager/
    from selenium import webdriver

    driver = None

    ua = UserAgent()
    user_agent = ua.random

    if driver_name == "geckodriver":
        
        # **** XXXX
        #from webdriver_manager.firefox import GeckoDriverManager
        #executable_path = GeckoDriverManager().install()
        
        from selenium.webdriver.firefox.service import Service as FirefoxService
        from webdriver_manager.firefox import GeckoDriverManager

        from selenium.webdriver.firefox.options import Options

        if _gecko_service == None:
            # **** XXXX
            # For now control the version, so it doesn't keep hitting the http://api.github.com/.../latest URL,
            # as this turns out to be rate limited
            _gecko_service = FirefoxService(GeckoDriverManager(version="v0.35.0").install())
                    
        options = Options()
        options.add_argument(f'--user-agent={user_agent}')
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options, service=_gecko_service)
    elif driver_name == "chromedriver":
        # From Sulan's earlier work:
        #   https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/win64/chromedriver-win64.zip
        
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument(f'--user-agent={user_agent}')

        # Assume sourcing SETUP.bash puts the chromedriver on PATH, so no longer need to explicitly set this
        #driver = webdriver.Chrome(chrome_options=options, executable_path=globals.config['chromedriver'])
        driver = webdriver.Chrome(chrome_options=options)
    
    return driver


def download_and_save(url_id, url, download_with_selenium,apply_robots_txt, downloads_dir, url_timeout=10):

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

        filepath,rejected_filepath = fileutils.get_download_filename_pair(downloads_dir,file_hash,doc_type)

        if not os.path.exists(filepath) or os.path.exists(rejected_filepath):
                    
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
    
def search_and_fetch(query_row, search_engine_type, num_pages=1, **kwargs):
    """Fetch Google search results and update"""
    # **** XXXX YYYY
    #query_id = query_row[0]
    #query_terms = query_row[1]
    query_id = query_row['id']
    query_terms = query_row['query']

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
            temp = search.google(query_terms, count)
        elif search_engine_type == const.GOOGLE_SELENIUM:
            temp = search.google_selenium(query_terms, driver, count)
        elif search_engine_type == const.BING:
            temp = search.bing(query_terms, count)
        elif search_engine_type == const.BING_SELENIUM:
            temp = search.bing_selenium(query_terms, driver, count)
        elif search_engine_type == const.GOOGLE_API:
            temp = search.google_api(query_terms, globals.config['google']['key'],globals.config['google']['cx'], count, **kwargs)
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

    # Remove URLs from domains on the exclusion-list
    num_unfiltered_urls = len(urls)
    urls = fileutils.remove_excluded_domains(urls, globals.config['excluded_domains'])
    num_filtered_urls = len(urls)

    num_removed_urls = num_unfiltered_urls - num_filtered_urls
    if num_removed_urls > 0:
        print(f"  {num_removed_urls} URL(s) filtered out by applying exclusion-list")

    if num_filtered_urls == 0:
        return

    # Prepare the URL data for insertion
    # => not currently downloaded, so url downloaded=False and (nlp) handle=False

    # **** XXXX YYYY
    #url_data = [(query_id, engine, url, fileutils.hash_url(url), False, False) for url in urls]
    url_data = [{'query_id':query_id, 'type':engine, 'url':url, 'url_hash':fileutils.hash_url(url), 'downloaded':False, 'handled':False} for url in urls]

    # Insert URLs into the database (only the new ones)
    sql.insert_urls_many(url_data)

def search_worker(sub_tablequeries_rows, search_engine_type, num_pages, tcount):
    for query_row in sub_tablequeries_rows:
        # Check if the stop event is set
        if stop_event.is_set():
            return

        now = datetime.now()
        print(f"Thread {tcount} ============ Search Stage @ {now.strftime('%H:%M:%S')} ============")
        print(f"Storing DB query row: {[query_row[key] for key in query_row.keys()]}")
        search_and_fetch(query_row, search_engine_type, num_pages)

        sleep_delay = globals.config['sleep_delay']
        randomized_sleep_delay = sleep_delay + random.randint(0,sleep_delay)
        print(f"  [pausing for {randomized_sleep_delay} secs]")
        time.sleep(randomized_sleep_delay)

        
def download_worker(sub_tableurls_rows, download_with_selenium,apply_robots_txt, tcount):
    for url_row in sub_tableurls_rows:
        #url_id         = url_row[0]
        #url_href       = url_row[3]
        #url_downloaded = url_row[7]
        ##url_handled    = url_row[8]

        # **** XXXX YYYY
        url_id         = url_row['id']
        url_href       = url_row['url']
        url_downloaded = url_row['downloaded']
        #url_handled    = url_row['handled']
        
        if url_downloaded == 1: # already downloaded
            print(f"Thread {tcount}: Skipping as already downloaded URL {url_href}")
            continue
        
        now = datetime.now()
        print(f"Thread {tcount} ============ Download Stage @ {now.strftime('%H:%M:%S')} ============ URL id {url_id}")
        try:
            # Check if the stop event is set
            if stop_event.is_set():
                return
            
            result = download_and_save(url_id, url_href, download_with_selenium,apply_robots_txt,
                                       globals.config['downloads_dir'], globals.config['url_timeout'])
            if result == 1:
                print(f"Thread {tcount} ============ ============ EXISTING URL id {url_id}")
                continue
            if result == 0:
                sql.set_url_as_handled(url_id)
                continue

            # If here, then result return is of the form
            #   {"path": filepath, "hash": file_hash, "doc_type": doc_type}

            url_filehash = result["hash"]
            url_doctype  = result["doc_type"]
            sql.update_url_fileinfo(url_id, url_filehash, url_doctype, downloaded=True) 
            
        except FileNotFoundError as e:
            sql.set_url_as_handled(url_id)
            print(f"Thread {tcount} File not found")
        except Exception as e:
            sql.set_url_as_handled(url_id)
            print(f"Thread {tcount} Error in NLP: {e}")
            if (globals.verbose > 2):
                print(traceback.format_exc())


def nlp_reject_downloaded_file(url_id,downloads_dir,url_filehash,url_doctype,reason):
    sql.set_url_as_handled(url_id)
    url_filepath_downloaded,url_filepath_rejected = fileutils.get_download_filename_pair(downloads_dir,url_filehash,url_doctype)
    print(f"Thread {tcount} xxxxxxxxxxxx rejecting ({reason}) xxxxxxxxxxxx")
    fileutils.move_file(url_filepath_downloaded,url_filepath_rejected)
    
def nlp_worker(sub_tableurls_rows, lang_dict_termvec_rec, detect_name, tcount):

    downloads_dir = globals.config['downloads_dir']
    
    for url_row in sub_tableurls_rows:

        #url_id         = url_row[0]
        #url_href       = url_row[3]
        #url_filehash   = url_row[5]
        #url_doctype    = url_row[6]
        #url_handled    = url_row[8]

        url_id         = url_row['id']
        url_href       = url_row['url']
        url_filehash   = url_row['file_hash']
        url_doctype    = url_row['doc_type']        
        url_handled    = url_row['handled']
        
        if url_handled == 1: # already handled it
            print(f"Thread {tcount}: Skipping as already NLP-processed (handled) URL {url_href}")
            continue

        url_filepath,rejected_url_filepath = fileutils.get_download_filename_pair(downloads_dir,url_filehash,url_doctype)

        if (os.path.exists(rejected_url_filepath)):
            # It's been processed on a previous run, but this run with different config NLP settings
            # might lead to a different outcome
            fileutils.move_file(rejected_url_filepath,url_filepath)
            
        now = datetime.now()
        print(f"Thread {tcount} ============ NLP Stage @ {now.strftime('%H:%M:%S')} ============ URL id {url_id}")
        try:
            # Check if the stop event is set
            if stop_event.is_set():
                return

            print(f"  NLP being applied to url_id={url_id} filehash={url_filehash}")
            print(f"  url={url_href}")
            
            if set_nlp_values_from_existing(url_id, url_filehash) == 1:
                # Found another entry in the database that:
                #   (i) has the same file_hash but a differnt url_id, and
                #  (ii) been nlp-handled
                #
                # As a result of calling this rountine, the existing NLP fields
                # have been copied to the database entry for this url_id
                return
            
            extracted_text = nlp.extract_text_from_file(url_filepath, url_doctype)
            if extracted_text == None:
                nlp_reject_downloaded_file(url_id,downloads_dir,url_filehash,url_doctype,"no extracted text")
                continue
            cleaned_extracted_text = nlp.clean_text(extracted_text)
            # Guard against the cleaned text now being nothing but 100% whitespace
            if cleaned_extracted_text.isspace():
                nlp_reject_downloaded_file(url_id,downloads_dir,url_filehash,url_doctype,"text all whitespace")
                continue            

            langs = nlp.run_nlp_algorithms(cleaned_extracted_text,globals.lang_uc, lang_dict_termvec_rec)
            if langs["lingua"]["full_lang"] == None:
                nlp_reject_downloaded_file(url_id,downloads_dir,url_filehash,url_doctype,"NLP failed to detect language")
                continue

            # If reached this point, then NLP has made a language prediction (full page and per para)
            # => Store answer in database

            nlp_fulllang       = langs["lingua"]["full_lang"]
            nlp_fullconf       = langs["lingua"]["full_conf"]
            nlp_para_count     = langs["lingua"]["para_count"]
            nlp_para_count_lrl = langs["lingua"]["para_count_lrl"]
            nlp_para_perc_lrl  = langs["lingua"]["para_perc_lrl"] 

            sql.update_url_langinfo(url_id, nlp_fulllang, nlp_fullconf,
                                    nlp_para_count_lrl, nlp_para_count, nlp_para_perc_lrl)
            
            # We are interested in downloaded files that have at least one para of our low-resource-lang
            # => if not, then rename downloaded file to rejected

            # Previous test from Sulhan
            #if langs["lingua"]["full_lang"] != detect_name:
            #    nlp_reject_downloaded_file(url_id,downloads_dir,url_filehash,url_doctype,
            #                               f"detected {langs['lingua']['full_lang'].capitalize()} != {detect_name.capitalize()}")
            
            if nlp_para_count_lrl == 0:
                # No lrl language text                
                nlp_reject_downloaded_file(url_id,downloads_dir,url_filehash,url_doctype,
                                           f"NLP did not detected any paragraphs in {detect_name.capitalize()} language")            

        except FileNotFoundError as e:
            sql.set_url_as_handled(url_id)
            print(f"Thread {tcount} File not found")
        except Exception as e:
            sql.set_url_as_handled(url_id)
            print(f"Thread {tcount} Error in NLP: {e}")
            if (globals.verbose > 2):
                print(traceback.format_exc())
        
def validate_args(args):
    try:        
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


if __name__ == "__main__":
    globals.config = fileutils.read_config()
    globals.args = get_args()

    lang = globals.args.lang
    lang_lc = lang.lower()
    lang_uc = lang.upper()
    lang_ic = lang_lc.capitalize() # initial capital letter
    
    globals.lang    = lang
    globals.lang_lc = lang_lc
    globals.lang_uc = lang_uc
    globals.lang_ic = lang_ic
    
    globals.verbose = globals.args.verbose

    globals.config['downloads_dir'] = globals.config['downloads_dir_root'] + "-" + lang_lc
    globals.config['database_file'] = globals.config['database_file_root'] + "-" + lang_lc + ".db"

    database_filename = globals.config.get('database_file')
    print(f"Setting database name: {database_filename}")        
    sql.set_db_filename(database_filename)        
    
    if globals.args.set_queries_unhandled:
        sql.set_all_queries_unhandled()
        print("Marked all generated queries as unhandled.")
        exit(0)

    if globals.args.set_downloads_unhandled:
        sql.set_all_urls_undownloaded()
        print("Marked all URL downloads as unhandled.")
        exit(0)

    if globals.args.set_nlp_unhandled:
        sql.set_all_urls_unhandled()
        print("Marked al URLs NLP application as unhandled.")
        exit(0)
        
    try:
        validate_args(globals.args)

        # The following are now explicitly set to their config defaults if not give on CLI
        word_count    = globals.args.word_count
        query_count   = globals.args.query_count
        search_engine = globals.args.search_engine
        num_threads   = globals.args.num_threads
        num_pages     = globals.args.num_pages

        # Ensure the downloads directory exists
        downloads_dir = globals.config.get('downloads_dir')
        if not os.path.exists(downloads_dir):
            print(f"Creating download directory: {downloads_dir}")
            os.makedirs(downloads_dir)
        
        # Create the database
        sql.create(reset=False)
        
        if globals.args.display_stats:
            display.stats(lang_uc)
            exit(0)
                
        # Queries
        if globals.args.run_querygen or globals.args.run_all:
            print("Generating Queries.")
            queries_array = queries.generate_all(lang_uc, word_count, query_count)
            
        # Search
        if globals.args.run_websearch or globals.args.run_all:
            print("Running Search.")
            # Get all relevant queries from the database
            tablequeries_rows = sql.get_all_queries(lang_uc, handled=False)
            # Split queries into sub-lists for each thread
            split_tablequeries_rows = [tablequeries_rows[i::num_threads] for i in range(num_threads)]
            # Create and start threads
            threads = []
            print("Starting search threads.")
            tcount = 1
            
            for sub_tablequeries_rows in split_tablequeries_rows:
                t = threading.Thread(target=search_worker, args=(sub_tablequeries_rows, search_engine, num_pages, tcount))
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
            for tablequeries_row in tablequeries_rows:
                # **** XXXX YYYY
                #sql.set_query_as_handled(query[0])
                sql.set_query_as_handled(tablequeries_row['id'])
            print("All Search-threads have finished.")

        # Download
        if globals.args.run_download or globals.args.run_all:
            # Get all relevant queries from the database
            tableurls_rows = sql.get_all_urls_filter_downloaded(downloaded=False)
            print(f"Number of urls to be downloaded: {len(tableurls_rows)}")
            # Split queries into sub-lists for each thread
            split_tableurls_rows = [tableurls_rows[i::num_threads] for i in range(num_threads)]

            # Create and start threads
            threads = []
            print("Starting nlp threads.")
            tcount = 1
            for sub_tableurls_rows in split_tableurls_rows:
                t = threading.Thread(target=download_worker, args=(
                    sub_tableurls_rows, globals.args.download_with_selenium,globals.args.apply_robots_txt,tcount))
                threads.append(t)
                t.start()
                tcount += 1

            # Wait for all threads to finish
            for t in threads:
                if stop_event.is_set():
                    exit(0)
                t.join()
            print("All Download-threads have finished.")

        # NLP
        if globals.args.run_nlp or globals.args.run_all:
            lang_dict_termvec_rec = fileutils.load_language_dictionary_vector(lang)
            
            # Get all relevant queries from the database
            tableurls_rows = sql.get_all_urls_filter_downloaded_handled(downloaded=True,handled=False) 
            print(f"Number of urls to be processed by NLP: {len(tableurls_rows)}")

            # Split queries into sub-lists for each thread
            split_tableurls_rows = [tableurls_rows[i::num_threads] for i in range(num_threads)]

            # Create and start threads
            threads = []
            print("Starting nlp threads.")
            tcount = 1
            for sub_tableurls_rows in split_tableurls_rows:
                t = threading.Thread(target=nlp_worker, args=(sub_tableurls_rows, lang_dict_termvec_rec, globals.lang_uc, tcount))
                threads.append(t)
                t.start()
                tcount += 1
            # Wait for all threads to finish
            for t in threads:
                if stop_event.is_set():
                    exit(0)
                t.join()

            print("All NLP-threads have finished.")
            
        if globals.args.run_all:
            display.stats(lang_uc)
            
    except KeyboardInterrupt:
        print("Stopping all threads")
        # Signal all threads to stop
        stop_event.set()
        # Wait for all threads to finish
        for t in threads:
            t.join()
        print("All threads have been stopped.")
