#!/bin/bash -x

rm -rf querydownload.db downloads \
    && ./lrl-crawler.py --lang MAORI \
			--all \
			--query_count 1 \
			--search_engine bing \
			--apply_robots_txt \
			--num_threads 1 --num_pages 1 \
			$@
