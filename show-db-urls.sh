#!/bin/bash

lang="${1:-maori}"
db_filename="querydownloads-$lang.db"

# Pur URL at end, deliberately skip of url_hash
echo -e '.headers on \nselect query_id, type, file_hash, doc_type, downloaded, handled, nlp_full_lang, nlp_full_confidence, nlp_para_count_lrl, nlp_para_count, nlp_para_perc_lrl, url from urls;' | sqlite3 "$db_filename"
