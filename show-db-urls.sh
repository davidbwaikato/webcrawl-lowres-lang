#!/bin/bash

db_filename="${1:-querydownload.db}"

echo -e '.headers on \nselect * from urls;' | sqlite3 "$db_filename"
