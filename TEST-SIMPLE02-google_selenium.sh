#!/bin/bash

lang=${1:-maori}

if [ "x$EXTRA_ARGS" = "x" ] ; then
    echo "----"
    echo "To provide additional command-line arguments, Set the variable EXTRA_ARGS"
    echo "----"
fi
   
rm -rf querydownloads-$lang.db downloads-$lang \
    && ./lrl-crawler.py \
			--run_all \
			--query_count 1 \
			--search_engine google \
			--use_selenium \
			--num_threads 4 --num_pages 2 \
			$EXTRA_ARGS \
			$lang
