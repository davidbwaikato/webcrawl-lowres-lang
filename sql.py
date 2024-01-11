import sqlite3
import time
from contextlib import contextmanager
from helpers import hash_url

dbname = "mydb.db"


@contextmanager
def get_cursor():
    """Context manager for SQLite database cursor."""
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        conn.commit()
        conn.close()


def create(reset=False):
    """Initialize the database and create required tables."""
    with get_cursor() as cursor:
        if reset:
            cursor.execute('DROP TABLE IF EXISTS urls')
            cursor.execute('DROP TABLE IF EXISTS queries')
        # Create the queries table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY,
            query TEXT NOT NULL,
            type TEXT NOT NULL,
            lan TEXT NOT NULL,
            unhandled BOOLEAN DEFAULT 1
        )
        ''')
        # Create the urls table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY,
            query_id INTEGER,
            type TEXT NOT NULL,
            url TEXT NOT NULL,
            url_hash TEXT NOT NULL,
            file_hash TEXT,
            doc_type TEXT,
            unhandled BOOLEAN DEFAULT 1,
            full_lan TEXT,
            paragraph_lan INTEGER DEFAULT 0,
            FOREIGN KEY (query_id) REFERENCES queries(id)
        )
        ''')


def insert_query(query, type, lan):
    """Insert a new query into the queries table."""
    with get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO queries (query, type, lan) VALUES (?, ?, ?)", (query, type, lan))


def insert_url(query_id, type, url, doc_type=""):
    """Insert a new URL into the urls table."""
    with get_cursor() as cursor:
        url_hash = hash_url(url)
        cursor.execute("""
            INSERT INTO urls (query_id, type, url, url_hash, doc_type)
            VALUES (?, ?, ?, ?, ?)
        """, (query_id, type, url, url_hash, doc_type))


def get_all_queries(lan, unhandled=None):
    """Retrieve all queries from the queries table."""
    with get_cursor() as cursor:
        if unhandled is None:
            cursor.execute("SELECT * FROM queries WHERE lan=?", (lan,))
            return cursor.fetchall()
        else:
            cursor.execute(
                "SELECT * FROM queries WHERE lan=? AND unhandled=?", (lan, unhandled,))
            return cursor.fetchall()


def get_all_urls(unhandled=None):
    """Retrieve all URLs from the urls table."""
    with get_cursor() as cursor:
        if unhandled is None:
            cursor.execute("SELECT * FROM urls")
            return cursor.fetchall()
        else:
            cursor.execute(
                "SELECT * FROM urls WHERE unhandled=?", (unhandled,))
            return cursor.fetchall()


# def get_all_urls_nlp(unhandled=None, include_null_file_hash=False):
#     """Retrieve all URLs from the urls table."""
#     with get_cursor() as cursor:
#         if unhandled is None:
#             if include_null_file_hash:
#                 cursor.execute("SELECT * FROM urls WHERE file_hash IS NULL")
#             else:
#                 cursor.execute("SELECT * FROM urls")
#             return cursor.fetchall()
#         else:
#             if include_null_file_hash:
#                 cursor.execute(
#                     "SELECT * FROM urls WHERE unhandled=? LIMIT 100", (unhandled,))
#             else:
#                 cursor.execute(
#                     "SELECT * FROM urls WHERE unhandled=? AND full_lan IS NULL LIMIT 100", (unhandled,))
#             return cursor.fetchall()

        
def query_exists(query):
    """Check if a query already exists in the queries table."""
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM queries WHERE query=?)", (query,))
        return bool(cursor.fetchone()[0])


def insert_query_if_not_exists(query, type, lan):
    """Insert a query into the queries table if it doesn't already exist."""
    if not query_exists(query):
        insert_query(query, type, lan)
        return True
    return False

def save_bing_url(url_id, final_url):
    """Insert a URL into the urls table if it doesn't already exist."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE urls
            SET url=?, unhandled=True
            WHERE id=?
        """, (final_url, url_id))

def insert_url_if_not_exists(query_id, type, url, doc_type=""):
    """Insert a URL into the urls table if it doesn't already exist."""
    with get_cursor() as cursor:
        url_hash = hash_url(url)
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM urls WHERE url_hash=?)", (url_hash,))
        if not bool(cursor.fetchone()[0]):
            cursor.execute("""
                INSERT INTO urls (query_id, type, url, url_hash, doc_type, unhandled)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (query_id, type, url, url_hash, doc_type))
            return True
    return False


def get_url_by_id(id):
    """Retrieve a URL from the urls table by its ID."""
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM urls WHERE id=?", (id,))
        return cursor.fetchone()

def get_url_file_hash(url_id, file_hash):
    """Retrieve a URL from the urls table by its File Hash."""
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM urls WHERE id!=? AND file_hash=? AND unhandled=False LIMIT 1", (url_id, file_hash,))
        return cursor.fetchone()

def update_url_by_id(id, file_hash, doc_type, full_lan, paragraph_lan):
    """Update a URL's attributes in the urls table by its ID."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE urls
            SET file_hash=?, doc_type=?, full_lan=?, paragraph_lan=?, unhandled=0
            WHERE id=?
        """, (file_hash, doc_type, full_lan, paragraph_lan, id))


def update_query_unhandled_by_id(id):
    """Updates the unhandled value to false for a given query ID in the queries table."""
    with get_cursor() as cursor:
        cursor.execute(
            "UPDATE queries SET unhandled=? WHERE id=?", (False, id))


def get_url_counts_by_query_id(lan, query_id):
    """Returns the total number of URLs, the number of unhandled URLs, and the number of URLs with non-null full_lan for a given query ID."""
    with get_cursor() as cursor:
        # Total URLs count
        cursor.execute(
            "SELECT COUNT(*) FROM urls WHERE query_id=?", (query_id,))
        total_count = cursor.fetchone()[0]
        # Total unhandled URLs count
        cursor.execute(
            "SELECT COUNT(*) FROM urls WHERE query_id=? AND unhandled=?", (query_id, True))
        unhandled_count = cursor.fetchone()[0]
        # Total URLs with non-null full_lan
        cursor.execute(
            "SELECT COUNT(*) FROM urls WHERE query_id=? AND full_lan=?", (query_id, lan))
        full_lan_count = cursor.fetchone()[0]
        return {
            "total_count": total_count,
            "unhandled_count": unhandled_count,
            "full_lan_count": full_lan_count
        }


def get_url_counts_by_type(lan, search_type):
    """
    Returns the total number of URLs, the number of unhandled URLs, and the number of URLs with a specific full_lan 
    for all queries of a given language and search type.
    """
    if "_selenium" in search_type:
        search_type = search_type.replace("_selenium", "")
    with get_cursor() as cursor:
        # Join queries and urls tables, then filter by lan and search type
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN u.unhandled = 1 THEN 1 ELSE 0 END) as unhandled_count,
                SUM(CASE WHEN u.full_lan = ? THEN 1 ELSE 0 END) as full_lan_count
            FROM queries q
            JOIN urls u on q.id = u.query_id
            WHERE q.lan = ? AND u.type = ?
        """, (lan, lan, search_type))

        result = cursor.fetchone()
        unhandled = 0
        if result[1] is not None:
            unhandled = result[1]
        full_lan = 0
        if result[2] is not None:
            full_lan = result[2]
        return {
            "total_count": result[0],
            "unhandled_count": unhandled,
            "lan_count": full_lan
        }


def urls_exist(url_hashes, type):
    """Check if URLs with given hashes and type already exist in the database."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT url_hash FROM urls 
            WHERE url_hash IN ({seq}) AND type = ?""".format(seq=','.join(['?']*len(url_hashes))),
                       (*url_hashes, type))
        existing_hashes = {row[0] for row in cursor.fetchall()}
    return existing_hashes


def insert_urls_many(url_data):
    """Inserts multiple URLs at once into the database after filtering existing ones."""
    # Separate hashes for existing check
    hashes_to_check = [item[3] for item in url_data]
    type_to_check = url_data[0][1]
    existing_hashes = urls_exist(hashes_to_check, type_to_check)
    # Filter out the URLs that already exist based on hash and type
    filtered_data = [item for item in url_data if item[3]
                     not in existing_hashes]
    if not filtered_data:  # If all URLs already exist, return early
        return
    with get_cursor() as cursor:
        cursor.executemany("""
            INSERT INTO urls (query_id, type, url, url_hash, unhandled)
            VALUES (?, ?, ?, ?, ?)
        """, filtered_data)

def set_query_as_handled(query_id):
    """Sets the unhandled flag of a query to False."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE queries
            SET unhandled = False
            WHERE id = ?
        """, (query_id,))

def set_url_as_handled(url_id):
    """Sets the unhandled flag of a url to False."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE urls
            SET unhandled = False
            WHERE id = ?
        """, (url_id,))

def update_url(url_id, file_hash, doc_type, full_lan, confidence, paragraph_lan):
    """Sets multiple values of the URL."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE urls
            SET unhandled = False,
                file_hash  = ?,
                doc_type  = ?,
                full_lan  = ?,
                confidence  = ?,
                paragraph_lan  = ?
            WHERE id = ?
        """, (file_hash, doc_type, full_lan, confidence, paragraph_lan, url_id,))

def set_all_queries_unhandled():
    """Set all queries in the database as unhandled."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE queries
            SET unhandled = True
        """)

def set_all_urls_unhandled():
    """Set all urls in the database as unhandled."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE urls
            SET unhandled = False
        """)

def count_query_types():
    """Returns a dictionary of each query type and its count in the queries table."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM queries
            GROUP BY type
        """)
        result = cursor.fetchall()
    # Convert the result to a dictionary
    return {row[0]: row[1] for row in result}


def count_urls_per_query_type():
    """Returns a dictionary of each query type and the count of URLs associated with it."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT q.type, COUNT(u.id) as count
            FROM queries q
            JOIN urls u ON q.id = u.query_id
            GROUP BY q.type
        """)
        result = cursor.fetchall()
    return {row[0]: row[1] for row in result}


def get_top_3_queries_with_most_urls():
    """Returns the top 3 queries with the most URLs found."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT q.query, COUNT(u.id) as count
            FROM queries q
            JOIN urls u ON q.id = u.query_id
            GROUP BY q.query
            ORDER BY count DESC
            LIMIT 3
        """)
        results = cursor.fetchall()
    return [{"query": row[0], "count": row[1]} for row in results]


def query_with_least_urls():
    """Returns the query with the least URLs found."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT q.query, q.type, COUNT(u.id) as count
            FROM queries q
            LEFT JOIN urls u ON q.id = u.query_id
            GROUP BY q.id
            ORDER BY count ASC
            LIMIT 1
        """)
        result = cursor.fetchone()
    return {
        "query": result[0],
        "type": result[1],
        "count": result[2]
    }


def count_queries_with_zero_urls_by_type():
    """Returns the count of queries by type for which no URLs have been found."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT q.type, COUNT(DISTINCT q.id) 
            FROM queries q
            LEFT JOIN urls u ON q.id = u.query_id
            WHERE u.id IS NULL
            GROUP BY q.type
        """)
        results = cursor.fetchall()

    return {row[0]: row[1] for row in results}


# def get_most_common_urls():
    # """Returns the last three URLs with their occurrences and unique query counts."""
    # with get_cursor() as cursor:
    #     cursor.execute("""
    #         SELECT
    #             url,
    #             COUNT(url) as url_count,
    #             COUNT(DISTINCT query_id) as query_count
    #         FROM urls
    #         GROUP BY url
    #         ORDER BY query_count DESC, url_count DESC
    #         LIMIT 3
    #     """)
    #     results = cursor.fetchall()

    # # Convert results to a list of dictionaries for easier interpretation
    # return [{"url": row[0], "url_count": row[1], "unique_queries": row[2]} for row in results]

def get_most_common_urls():
    """Count the number of URLs grouped by their unique query counts."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT url) as url_count, 
                COUNT(DISTINCT query_id) as query_count
            FROM urls
            GROUP BY url
            ORDER BY query_count DESC
        """)
        results = cursor.fetchall()

    # Create a dictionary to store the final breakdown
    breakdown = {}
    for row in results:
        unique_queries = row[1]
        if unique_queries not in breakdown:
            breakdown[unique_queries] = 0
        breakdown[unique_queries] += 1

    return breakdown


def hash_exists_in_db(file_hash):
    """Check if a given hash exists in the database."""
    with get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM urls WHERE file_hash = ?", (file_hash,))
        count = cursor.fetchone()[0]
    return count > 0