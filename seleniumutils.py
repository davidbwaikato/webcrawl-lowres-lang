
from fake_useragent import UserAgent
from selenium import webdriver

#_webdriver_cache_dir = "./webdriver_cache"

_webdriver_path_lookup    = {}
_webdriver_service_lookup = {}

def init_service(driver_name):

    if driver_name == "geckodriver":
        from webdriver_manager.firefox import GeckoDriverManager                
        from selenium.webdriver.firefox.service import Service as FirefoxService
        
        ## Keep cached for 30 days
        #manager = GeckoDriverManager(cache_valid_range=30, path=_webdriver_cache_dir)
        # Looks to now use a DownloadManager and CacheManager class
        
        manager = GeckoDriverManager()

        # Returns the path to the installed webdriver
        # (whether installing, or already installed in cache)
        driver_path = manager.install()
        
        service = FirefoxService(driver_path)

        _webdriver_path_lookup[driver_name]   = driver_path
        _webdriver_service_lookup[driver_name] = service
                
def create_driver(driver_name):

    driver = None
    
    ua = UserAgent()
    user_agent = ua.random

    if driver_name == "geckodriver":
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        
        service = _webdriver_service_lookup[driver_name]
        
        options = FirefoxOptions()
        options.add_argument(f'--user-agent={user_agent}')
        options.add_argument("--headless")

        driver = webdriver.Firefox(service=service,options=options)
    elif driver_name == "chromedriver":        
        # From Sulan's earlier work:
        #   https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/win64/chromedriver-win64.zip

        print(f"***** selenliumutils.create_driver() currently code to work with manually installed driver")
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument(f'--user-agent={user_agent}')

        # Assume sourcing SETUP.bash puts the chromedriver on PATH, so no longer need to explicitly set this
        #driver = webdriver.Chrome(chrome_options=options, executable_path=globals.config['chromedriver'])
        driver = webdriver.Chrome(chrome_options=options)
    else:
        raise ValueError(f"Driver of type {driver_name} not currently supported")
                
    return driver


    
