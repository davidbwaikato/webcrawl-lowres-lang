
from enum import Enum

class SearchEngineType(Enum):
    GOOGLE          = "google"
    GOOGLE_SELENIUM = "google_selenium"
    GOOGLE_API      = "google_api"
    BING            = "bing"
    BING_API        = "bing_api"
    BING_SELENIUM   = "bing_selenium"
    
    def __str__(self):
        return self.value

class LangDetect(Enum):
    lingua = 'lingua'
    cossim = 'cossim'

    def __str__(self):
        return self.value

class DictOutputMode(Enum):
    merge = 'merge'
    replace = 'replace'

    def __str__(self):
        return self.value

    
