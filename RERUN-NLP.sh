#!/bin/bash

lang=${1:-maori}

./lrl-crawler.py -snu $lang  && ./lrl-crawler.py -rn  --num_threads 1 -v 3 $lang
