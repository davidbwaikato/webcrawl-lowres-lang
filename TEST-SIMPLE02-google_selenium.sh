#!/bin/bash

rm -rf querydownload.db downloads \
    && ./lrl-crawler.py --lang MAORI \
			--query_count 1 --search_type google_selenium \
			--threads 4 --pages 1 --all
