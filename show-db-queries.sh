#!/bin/bash

db_filename="${1:-querydownload.db}"

echo 'select * from queries;' | sqlite3 "$db_filename"
