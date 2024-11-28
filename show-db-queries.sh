#!/bin/bash

lang="${1:-maori}"
db_filename="querydownloads-$lang.db"

echo -e '.headers on \nselect * from queries;' | sqlite3 "$db_filename"
