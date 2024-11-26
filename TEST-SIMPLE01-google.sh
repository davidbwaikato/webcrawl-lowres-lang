#!/bin/bash -x

#	   --apply_robots_txt \

rm -rf querydownload.db downloads \
    && ./lrl-crawler.py \
	   --all \
	   --query_count 1 \
	   --search_engine google \
	   --num_threads 1 --num_pages 1 \
	   $@ \
	   MAORI
