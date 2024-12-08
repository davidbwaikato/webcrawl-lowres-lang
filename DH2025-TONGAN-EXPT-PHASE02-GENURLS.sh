#!/bin/bash

lang=tongan

if [ -f querydownloads-$lang.db ] || [ -d downloads-$lang ] ; then
   
    echo ""
    read -p "Remove '$lang' previous database and downloaded files? " -n 1 -r
    echo ""   #  move to a new line

    if [[ $REPLY =~ ^[Yy]$ ]] ; then
	rm -rf querydownloads-$lang.db downloads-$lang
    fi
fi

# double query_count

./lrl-crawler.py \
    --run_querygen \
    --run_websearch \
    \
    --word_count 3 \
    --query_count 20 \
    --exclude_english_lexicon \
    --search_engine google \
    --use_selenium \
    --num_pages 1 \
    --num_threads 4 \
    $@ \
    $lang
