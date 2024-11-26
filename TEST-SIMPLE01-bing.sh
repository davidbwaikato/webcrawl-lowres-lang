#!/bin/bash -x

rm -rf querydownload.db downloads \
    && ./lrl-crawler.py \
			--all \
			--query_count 1 \
			--search_engine bing \
			--num_threads 1 --num_pages 1 \
			$@ \
			maori
