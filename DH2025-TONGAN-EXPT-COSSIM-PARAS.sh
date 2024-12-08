#!/bin/bash

./RERUN-NLP.sh tongan \
    | egrep "^CosSim-TONGAN:" \
    | awk -v FS='\t' '{ printf("%s\n\n",$2) }'

