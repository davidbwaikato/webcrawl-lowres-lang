
####
# One time only setup
####

  python3 -mvenv my-python3
  source ./my-python3/bin/activate

  python3 -m pip3 install --upgrade pip

  pip3 install -r requirements-toplevel.txt

  /bin/cp config.json.in config.json
  # And then open in an editor, and adjust as needed
  # such as added in keys to use web searching APIs

  emacs config.json

####
# Ready to run the code
####

source ./SETUP.bash

python3 ./app.py --help

# json files in dict/ already committed to git, so no need to run:
#   python3 ./app.py --extract_dict

# If you do, the hashmap can write out words with same frequency
# in slightly different order, so git status will how the file
# has changed

# So you're all set to run the subsequent stages:
#   generate query, search, NLP and display
# with the command:

  python3 ./app.py --all --search_type google


====
####
# Extra notes on what gets installed
####

# Some things that are typically already installed
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
