#!/bin/bash

lang=${1:-maori}

if [ "x$EXTRA_ARGS" = "x" ] ; then
    echo "----"
    echo "To provide additional command-line arguments, Set the variable EXTRA_ARGS"
    echo "----"
fi

./lrl-crawler.py -snu $lang  && ./lrl-crawler.py --run_nlp  --num_threads 1 $EXTRA_ARGS $lang
