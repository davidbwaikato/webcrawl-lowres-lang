#!/bin/bash -x

rm -rf querydownload-maori.db downloads-maori \
    && ./lrl-crawler.py \
			--run_all \
			--query_count 1 \
			--search_engine google_selenium \
			--download_with_selenium \
			--num_threads 4 --num_pages 2 \
			$@ \
			maori
