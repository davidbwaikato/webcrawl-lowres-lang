#!/bin/bash -x

#	   --apply_robots_txt \

rm -rf querydownloads-maori.db downloads-maori \
    && ./lrl-crawler.py \
	   --run_all \
	   --query_count 1 \
	   --search_engine google \
	   --num_threads 1 --num_pages 1 \
	   $@ \
	   maori
