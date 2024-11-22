#!/bin/bash -x

rm -rf querydownload.db downloads \
    && ./lrl-crawler.py --lang MAORI \
			--all \
			--query_count 1 \
			--search_engine google_selenium \
			--download_with_selenium \
			--num_threads 4 --num_pages 2 \
			$@
