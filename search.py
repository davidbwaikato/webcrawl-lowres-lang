
import base64
import re
import requests

import bs4
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from urllib.parse import urlparse, parse_qs

import globals

# Normal request = Will get blocked, no proxy, can't scrape dynamic pages and can't solve a captcha
# Selenium = Won't get blocked as it simulates a real user, allows scraping dynamic pages but can't solve a captcha and is slower

def display_resultset_info(url,num_result_items,full_text):

    if (num_result_items > 0):
        print(f"  {num_result_items} result-set blocks extracted from returned search-engine result page")
    else:
        print(f"  0 result-set blocks extracted from the result page returned by the search-engine query")
        print(f"      Query Url: {url}")
        if (globals.verbose > 1):
            print("----")
            print(full_text[:globals.verbose*100])
            print("----")

def display_resultlink_info(url,link_items):

    num_link_items = len(link_items)
    if (num_link_items > 0):
        print(f"  {num_link_items} document link(s) extracted from returned search-engine result page")
    else:
        print(f"  0 documents links extracted from the result page returned by the search-engine query")
        print(f"      Query URL: {url}")
            
            
def google(query,  page=1):
    """Fetch results from Google"""

    print(f"Running Google Search for: {query}, page {page}")

    query_encoded = re.sub(r' ','+',query)
    
    start = (page - 1) * 10
    url = f"https://www.google.com/search?q={query_encoded}&start={start}"

    ua = UserAgent()
    user_agent = ua.random
    header = {'User-Agent': user_agent}

    response = requests.get(url, headers=header)
    if response.status_code != 200:
        return []

    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    result_items = soup.find_all('div',  {'class': 'g'})

    num_result_items = len(result_items)
    display_resultset_info(url,num_result_items,soup.get_text(separator=" "))
    
    urls = []
    for g in result_items:
        anchors = g.find_all('a')
        if anchors:
            # It was found that, occassionaly, the link in the returned results
            # didn't have a 'href' (e.g., just an anchor-name link)
            if anchors[0].has_attr("href"):
                link = anchors[0]['href']
                urls.append(str(link))
            else:
                print(f"  Skipping extracted anchor, as it had no 'href' link")

    if (num_result_items > 0):
        display_resultlink_info(url,urls)
    
    return urls


def google_selenium(query, driver, page=1):
    """Fetch results from Google using selenium"""

    print(f"Running Google Selenium Search for: {query}, page {page}")

    query_encoded = re.sub(r' ','+',query)
    
    start = (page - 1) * 10
    url = f"https://www.google.com/search?q={query_encoded}&start={start}"
    try:
        driver.get(url)

        full_text = driver.find_element(By.XPATH, "/html/body").text        
        result_divs = driver.find_elements(By.CSS_SELECTOR, "div.g")

        num_result_divs = len(result_divs)
        display_resultset_info(url,num_result_divs,full_text)
        
        urls = []

        for result_div in result_divs:
            anchor = result_div.find_elements(By.CSS_SELECTOR, "a")
            link = anchor[0].get_attribute("href")
            urls.append(str(link))
            
        if (num_result_divs > 0):            
            display_resultlink_info(url,urls)
            
        return urls
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def google_api(query, api_key, cx, page, **kwargs):
    """Fetch results from Google using the API"""

    if (re.match(r'^\?+$',api_key)):
        print(f"google_api(): 'api_key' is set to '{api_key}'. Have you edit config.json to provide your Google key?")
        return []
    
    if (re.match(r'^\?$',cx)):
        print(f"google_api(): 'cx' credentials is set of '{cx}'. Have you edit config.json to provide your Google credentials?")
        return []

    print(f"Running Google API for: {query_encoded}, page {page}")
    start = (page - 1) * 10 + 1 # ChatGPT indicated the '+1' was needed
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': api_key,
        'cx': cx,
        'start': start,
        'num': 10,
        ** kwargs  # Additional parameters
    }
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        if response.status_code == 429:
            return 429
        return []
    urls = []
    items = response.json().get('items', [])
    for item in items:
        urls.append(item['link'])
    return urls


def bing_base64_decode(urls):

    # Bing can, at times, generate URL links that are base64 encoded, with the
    # URL going through bing.com/xxxx to be resolved to the actual URL
    #
    # This routine looks for these, and docodes them, allowig the destiniation
    # URL to be stored in the database, not the bing base64 encoded one

    # Found it a bit tricky to find definitive details about how the encoding/decoding
    # works.  Basically base64 encoded, but need to strip off the first two chars (a1)
    # and append '=='.
    #
    # Following up on some exceptions the occurred when trying to decode the binary
    # string returned to utf-8, I found the following project:
    #   https://greasyfork.org/en/scripts/464094-bing-url-decoder
    # that also maps:
    #   _ => /, - => +
    # before decoding the base64 string
    
    processed_urls = []
    
    # Try to decode URL if final URL is encoded
    for url in urls:
        parsed_url = urlparse(url)        
        if parsed_url.netloc == 'www.bing.com':
            query_params = parse_qs(parsed_url.query)
            try:
                if 'u' in query_params:
                    encoded_url = query_params['u'][0]
                    # print(f"**** encoded_url={encoded_url}, len={len(encoded_url)}")

                    temp = "{0}{1}".format(encoded_url[2:], "==")
                    temp = temp.replace('_','/').replace('-','+')
                    
                    processed_url = base64.b64decode(temp).decode("utf-8")
                    processed_urls.append(processed_url)
                
            except Exception as e:
                print(f"Failed to base64 decode URL: {url}, thrown exception was: {e}")
                processed_urls.append(url)
                continue
        else:
            processed_urls.append(url)

    return processed_urls

        
def bing(query,  page=1):
    """Fetch results from Bing"""
    print(f"Running Bing Search for: {query}, page {page}")

    query_encoded = re.sub(r' ','+',query)
    
    start = (page - 1) * 10
    if (page>1):
        # From empirial testing, found the first=11, first=21 to be how it works
        start = start +1
    
    url = f"https://www.bing.com/search?q={query_encoded}&first={start}"

    ua = UserAgent()
    user_agent = ua.random
    header = {'User-Agent': user_agent}

    response = requests.get(url, headers=header)
    if response.status_code != 200:
        return []
    
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    result_items = [h2 for h2 in (li.find('h2') for li in soup.find_all('li', {'class': 'b_algo'})) if h2]

    num_result_items = len(result_items)    
    display_resultset_info(url,num_result_items,soup.get_text(separator=" "))
            
    urls = []
    for g in result_items:
        anchors = g.find_all('a')
        if anchors:
            # Have similar guard to goggle() case above
            if anchors[0].has_attr("href"):
                link = anchors[0]['href']
                urls.append(str(link))
            else:
                print(f"  Skipping extracted anchor, as it had no 'href' link")

    if (num_result_items > 0):
        display_resultlink_info(url,urls)

    processed_urls = bing_base64_decode(urls)
    
    return processed_urls


def bing_selenium(query, driver, page=1):
    """Fetch results from Bing using Selenium"""
    print(f"Running Bing Selenium for {query}, page {page}")    

    query_encoded = re.sub(r' ','+',query)
    
    start = (page - 1) * 10
    if (page>1):
        # From empirial testing, found the first=11, first=21 to be how it works
        start = start +1
        
    url = f"https://www.bing.com/search?q={query_encoded}&first={start}"
    try:
        driver.get(url)
        
        full_text = driver.find_element(By.XPATH, "/html/body").text        
        #result_divs = driver.find_elements(By.CSS_SELECTOR, "div.tpcn")
        result_divs = driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2")

        num_result_divs = len(result_divs)
        display_resultset_info(url,num_result_divs,full_text)
        
        urls = []
        for result_div in result_divs:
            anchor = result_div.find_elements(By.CSS_SELECTOR, "a")
            link = anchor[0].get_attribute("href")
            urls.append(str(link))
            
        if (num_result_divs > 0):
            display_resultlink_info(url,urls)

        processed_urls = bing_base64_decode(urls)
        
        return processed_urls
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    

def bing_api(query, api_key, page, **kwargs):
    """Fetch results from Bing using the API."""

    # The following is based on the google_api function, using ChatGPT to produce the Bing API search version
    
    # Validate API key
    if re.match(r'^\?+$', api_key):
        print(f"bing_api(): 'api_key' is set to '{api_key}'. Have you updated config.json to provide your Bing API key?")
        return []
    
    # Encode the query
    query_encoded = query.replace(' ', '+')
    print(f"Running Bing API for: {query_encoded}, page {page}")
    
    # Calculate offset for pagination
    count = 10  # Bing returns 10 results per page by default
    offset = (page - 1) * count
    
    # Base URL for Bing Search API
    base_url = "https://api.bing.microsoft.com/v7.0/search"
    
    # Request parameters
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    params = {
        'q': query,
        'count': count,
        'offset': offset,
        **kwargs  # Additional parameters
    }
    
    # Send request
    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []
    
    # Parse results
    urls = []
    items = response.json().get('webPages', {}).get('value', [])
    for item in items:
        urls.append(item.get('url'))  # Use `.get()` to avoid KeyError
    return urls

