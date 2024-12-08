#!/bin/bash

lang=tongan


./lrl-crawler.py \
    --run_download \
    \
    --word_count 3 \
    --query_count 10 \
    --exclude_english_lexicon \
    --search_engine google \
    --use_selenium \
    --num_pages 1 \
    --num_threads 9 \
    $@ \
    $lang


echo ""
echo "----"
echo "Now take a copy of dicts/unicode_words_$lang.json, as the next phase number"
echo "----"
echo ""
