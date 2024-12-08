#!/bin/bash

for f in dicts/unigram_words_tongan-phase*.json dicts/unigram_words_tongan.json ; do

    echo "----"
    echo "Phase: $f"
    num_lines=`cat $f | wc -l`
    num_terms=$(expr $num_lines - 2)

    
    echo "  $num_terms"
    echo "----"
done



# After Phase 01 =   5 paras
# After Phase 02 =  16 paras
# After Phase 03 = 107 paras
# Freezing lexicon size

# After Phase 04 = 135 paras


# Continued growth ... but started to shrink as lexicon got bigger

# After Phase 04 = 128 paras
# After Phase 05 =  94 paras
