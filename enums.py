
from enum import Enum

class LangDetect(Enum):
    lingua = 'lingua'
    cossim = 'cossim'

    def __str__(self):
        return self.value

