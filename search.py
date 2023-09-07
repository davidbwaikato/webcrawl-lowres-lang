import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
# Normal request = Will get blocked, no proxy, can't scrape dynamic pages and can't solve a captcha
# Selenium = Won't get blocked as it simulates a real user, allows scraping dynamic pages but can't solve a captcha and is slower


def google(query,  page=1):
    """Fetch results from Google"""
    start = (page - 1) * 10
    url = f"https://www.google.com/search?q={query}&start={start}"
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}
    response = requests.get(url, headers=header)
    if response.status_code != 200:
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    urls = []
    for g in soup.find_all('div',  {'class': 'g'}):
        anchors = g.find_all('a')
        if anchors:
            link = anchors[0]['href']
            urls.append(str(link))
    return urls


def google_selenium(query, driver, page=1):
    """Fetch results from Google using selenium"""
    # https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/win64/chromedriver-win64.zip
    start = (page - 1) * 10
    url = f"https://www.google.com/search?q={query}&start={start}"
    try:
        driver.get(url)
        urls = []
        result_divs = driver.find_elements(By.CSS_SELECTOR, "div.g")
        for result_div in result_divs:
            anchor = result_div.find_elements(By.CSS_SELECTOR, "a")
            link = anchor[0].get_attribute("href")
            urls.append(str(link))
        return urls
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def google_api(query, api_key, cx, page, **kwargs):
    """Fetch results from Google using the API"""
    start = (page - 1) * 10
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': api_key,
        'cx': cx,
        'start': start,
        'num': 1,
        ** kwargs  # Additional parameters
    }
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        return []
    urls = []
    items = response.json().get('items', [])
    for item in items:
        urls.append(item['link'])
    return urls
