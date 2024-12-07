
from fake_useragent import UserAgent
from selenium import webdriver

# Consider refactoring to control the location where the webdriver is downloaded to
#_webdriver_cache_dir = "./webdriver_cache"

_webdriver_path_lookup    = {}

def init_manager(driver_type):

    if driver_type == "geckodriver":
        from webdriver_manager.firefox import GeckoDriverManager                
        
        ## Keep cached for 30 days
        #manager = GeckoDriverManager(cache_valid_range=30, path=_webdriver_cache_dir)
        # Looks to now use a DownloadManager and CacheManager class
        
        manager = GeckoDriverManager()
        # If wanting to avoid the https://api.github.com/... API call to check what the latest
        # version is, then can specify a fixed version, for example:
        #  GeckoDriverManager(version="v0.35.0")
        # Look in your ~/.wdm/drivers/geckodriver/ to see what has already been downloaded
        
        # Returns the path to the installed webdriver (whether installing, or already installed in cache)
        driver_path = manager.install()
        
        _webdriver_path_lookup[driver_type] = driver_path

    elif driver_type == "chromedriver":
        # Based on:
        #  https://pypi.org/project/webdriver-manager/
        # for selenium4, and assuming Chromium is pre-installed
        
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType

        manager = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM)
        driver_path = manager.install()
        
        _webdriver_path_lookup[driver_type] = driver_path        
    else:
        raise ValueError(f"Driver of type {driver_type} not currently supported")

    
def create_driver(driver_type):

    driver = None
    
    ua = UserAgent()
    user_agent = ua.random

    if driver_type == "geckodriver":
        from selenium.webdriver.firefox.service import Service as FirefoxService        
        from selenium.webdriver.firefox.options import Options as FirefoxOptions

        driver_path = _webdriver_path_lookup[driver_type]
        service = FirefoxService(driver_path)
        
        options = FirefoxOptions()
        options.add_argument(f'--user-agent={user_agent}')
        options.add_argument("--headless")

        driver = webdriver.Firefox(service=service,options=options)
    elif driver_type == "chromedriver":
        from selenium.webdriver.chrome.service import Service as ChromiumService
        from selenium.webdriver.chrome.options import Options as ChromiumOptions

        driver_path = _webdriver_path_lookup[driver_type]
        service = ChromiumService(driver_path)
                
        options = ChromiumOptions()
        options.add_argument(f'--user-agent={user_agent}')

        driver = webdriver.Chrome(service=service,options=options)
    else:  
        raise ValueError(f"Driver of type {driver_type} not currently supported")
                
    return driver


    
