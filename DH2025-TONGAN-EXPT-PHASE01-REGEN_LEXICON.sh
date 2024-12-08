#!/bin/bash

lang=tongan

./lrl-regenerate-dict.py \
    --lang_detect cossim \
    --output_mode merge \
    $@ \
    $lang
