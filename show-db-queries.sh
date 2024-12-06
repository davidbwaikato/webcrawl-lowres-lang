#!/bin/bash

lang="${1:-maori}"
db_filename="querydownloads-$lang.db"

echo "----"
echo "Displaying table 'queries' from $db_filename"
echo "----"
echo ""

echo -e '.headers on \nselect * from queries;' | sqlite3 "$db_filename"
