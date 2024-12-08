#!/bin/bash

lang=maori

echo ""
read -p "Remove previous database and downloaded files? " -n 1 -r
echo ""   #  move to a new line

if [[ $REPLY =~ ^[Yy]$ ]] ; then
    rm -rf querydownloads-$lang.db downloads-$lang
fi

./lrl-crawler.py \
    --run_querygen \
    --run_websearch \
    \
    --word_count 3 \
    --query_count 100 \
    --exclude_english_lexicon \
    --search_engine google \
    --use_selenium \
    --num_pages 2 \
    --num_threads 4 \
    $@ \
    $lang
