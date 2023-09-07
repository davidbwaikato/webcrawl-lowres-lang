import os
from extract import extract
from queries import generate_all
from helpers import save_to_json, hash_url, initialize_query, read_file, read_json, read_config, remove_blacklisted
from search import google, google_selenium, google_api
from selenium.webdriver.common.by import By
from selenium import webdriver


def get_all_query_files(directory="queries"):
    """Returns a list of all files in a directory"""
    return [os.path.join(directory, file) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]


def read_and_fetch(filename, type, page=1, **kwargs):
    """Read query file and fetch Google search results and update"""
    data = read_json(filename)
    driver = None
    config = read_config()
    # Get where to save the data
    if type == "google":
        engine = "google"
    elif type == "google_selenium":
        engine = "google"
        driver = webdriver.Chrome(executable_path=config['chromedriver'])
    elif type == "google_api":
        engine = "google_api"
    elif type == "bing":
        engine = "bing"
    elif type == "bing_api":
        engine = "bing_api"
    count = 1
    urls = []
    query = data["query"]
    while count <= page:
        if type == "google":
            temp = google(query, count)
        elif type == "google_selenium":
            temp = google_selenium(query, driver, count)
        elif type == "google_api":
            temp = google_api(query, config['google']['key'],
                              config['google']['cx'], count, **kwargs)
        if not temp:
            break
        urls.extend(temp)
        count += 1
        print(temp)
    # Quit the driver after the loop ends
    if driver:
        driver.quit()
    # Remove blacklisted URLs
    urls = remove_blacklisted(urls, config['blacklist'])
    # Remove duplicates
    existing_hashes = {item["url_hash"] for item in data[engine]["items"]}
    new_urls = [{"url": url, "url_hash": hash_url(url), "unhandled": True}
                for url in urls if hash_url(url) not in existing_hashes]
    # Update data
    data["total"] += len(urls)
    data["unhandled"] += len(urls)
    data[engine]["total"] += len(urls)
    data[engine]["unhandled"] += len(urls)
    data[engine]["items"].extend(new_urls)
    print(data)
    # Save the updated data
    # save_to_json(data, filename)


if __name__ == "__main__":
    # # Get dictionary from UDHR PDFs
    # extract()

    # # Generate queries
    # lang = "Māori"
    # queries = generate_all(lang)

    # # foreach query, save it in a json file
    # unique = 0
    # for query in queries:
    #     unique += initialize_query(query)
    # print(f"Created {unique} unique queries")

    # Search with the queries
    query_files = get_all_query_files()
    for file in query_files:
        read_and_fetch(file, "google_api")
        break

# Todo: Add Bing search
# Todo: Add Bing API search
# Todo: Run NLP on the results
# Todo: Add a console commands
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
