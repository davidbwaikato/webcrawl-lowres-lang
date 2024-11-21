
# One time only setup

If needing to install a version of python3 without admin rights,
run ./ get-selfcontained-python3.sh and follow the instructions there.
If following this option, then there is no need to set up a virtual
python env.

Otherwise:

```
  python3 -mvenv python3-for-lrl
  source ./python3-for-lrl/bin/activate
```

Optionally bring your pip3 is up-to-date, and install the
supporting python packages:

```
  pip3 install --upgrade pip

  pip3 install -r requirements-toplevel.txt
```

Now setup (and edit accordingly) _config.json_:
```
  /bin/cp config.json.in config.json
  emacs config.json
```

If you are going to be using the official Google or Bing API calls,
then you will need to add the relevant key(s) here.

## Working with Selenium

If looking to use Selenium to download weg page URLs then you will
need to install a driver such as geckodriver or chromedrive.
This in turn needs to be matched to the version of the web browser
you have installed (respectively) _firefox_ and _chrome_ in
the case of the two example drivers mentioned.

For example, for to work with Firefox on Linux:

1. Get a self-contained firefox (tarball)

  https://www.mozilla.org/en-GB/firefox/new/
```
    wget -O firefox-latest-ssl_linux64.tar.bz2 \
      "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-GB"
```

2. Get a version of geckodriver that is matched to you version of Firefox


  https://github.com/mozilla/geckodriver/releases/download/v0.35.0/
``` 
    wget https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux64.tar.gz
```

# Understanding the role of the sqlite3 database

A database is used to store the generated Low-Resource Language (LRL)
queries.  It is also used to store the URL information of the
pages, identified by the LRL queries.

The table name of LRL queries is _queries_ and the table name for the
identified web pages to download, _urls_.  In the case of the latter
a variety of information is held, in addition to the basic URL:

  * A marker to indicate whether or not the URL has been successfull download
  * A hash of the URL
  * A hash of the downloaded content
  * The document type (currently HTML of PDF)
  * The identified lanuage of the page, as determined by NLP analysis

Various metrics produced by the NLP tool are held:
full-page identified language; majority paragraph-by-paragraph language
identification; and confidence rating.

A version of the database produced during the original ENGEN582 project
is included.  This can be inspected with the following commands:

```
  echo -e '.headers on \n select * from queries;' | sqlite3 querydownload-sulhan.db  | less
  echo -e '.headers on \n select * from urls;' | sqlite3 querydownload-sulhan.db  | less
```    

# Running the code

To get command-line usage:

```
  source ./SETUP.bash

  python3 ./lrl-crawler.py --help
```

```
  # json files in dict/ already committed to git, so no need to run:
  #   python3 ./lrl-crawler.py --extract_dict

  # If you do, the hashmap can write out words with same frequency
  # in slightly different order, so git status will how the file
  # has changed
```


So for one of the provided low-resource language 'dictionary' (frequency count)
JSON files, you're all set to run all of the the remained stages:

For a minimal example that will take only a few minutes to run:

```
  ./lrl-crawler.py --lan MAORI --query_count 1 --search_type google --threads 1 --pages 1 --all
```

This generates the queries, performs the search, runs NLP over the downloaded
results and then displays some summary information.

And to test out your ability to work with Selenium to control your browser:

```
  ./lrl-crawler.py --lan MAORI --query_count 1 --search_type google_selenium --threads 1 --pages 1 --all
```

Operating more on default, designed to be more comprehensive web crawl:

```
  python3 ./lrl-crawler.py --all --search_type google
```


====
# Extra notes on what gets installed
====

## Some things that are typically already installed
pip3 install wheel
pip3 install requests

pip3 install bs4 selenium
pip3 install pdfminer.six webdriver-manager fake_useragent spacy nltk PyPDF2 python-docx 
pip3 install lingua-language-detector

pip3 freeze | \
    egrep '(bs4|selenium|pdfminer.six|webdriver-manager|fake-useragent|spacy|nltk|PyPDF2|python-docx|lingua-language-detector)'


At time of writing (2 Feb 2024), 'top-level' pip3 install packages came out as:

  bs4==0.0.2
  fake-useragent==1.4.0
  lingua-language-detector==2.0.2
  nltk==3.8.1
  pdfminer.six==20231228
  PyPDF2==3.0.1
  python-docx==1.1.0
  requests==2.31.0
  selenium==4.17.2
  spacy==3.7.2
  webdriver-manager==4.0.1

The following were skipped, as Sulhan said they were'nt used:

langdetect==1.0.7
spacy-langdetect==0.1.2
langid==1.1.6


# Additional Note(s):

Consider streamlining working with Gecko/Selenium/Firefox with:

  https://pypi.org/project/get-gecko-driver/
