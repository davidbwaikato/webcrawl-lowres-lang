#!/bin/bash

lang=maori

./lrl-crawler.py --set_nlp_unhandled $lang

./lrl-crawler.py \
    --run_nlp \
    \
    --word_count 3 \
    --query_count 100 \
    --exclude_english_lexicon \
    --search_engine google \
    --use_selenium \
    --num_pages 2 \
    --num_threads 1 \
    $@ \
    $lang
