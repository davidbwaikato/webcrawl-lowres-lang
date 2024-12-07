#!/bin/bash


lang=${1:-maori}

if [ "x$EXTRA_ARGS" = "x" ] ; then
    echo "----"
    echo "To provide additional command-line arguments, Set the variable EXTRA_ARGS"
    echo "----"
fi

#    --apply_robots_txt \

rm -rf querydownloads-$lang.db downloads-$lang \
    && ./lrl-crawler.py \
			--run_all \
			--query_count 1 \
			--search_engine bing \
			--num_threads 1 --num_pages 1 \
			$EXTRA_ARGS \
			$lang
