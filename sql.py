import sqlite3
import time
import fileutils

from contextlib import contextmanager
from urllib.parse import urlparse

dbname = "querydownload.db"

def set_db_filename(filename):
    global dbname
    dbname = filename
    
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
            lang TEXT NOT NULL,
            handled BOOLEAN DEFAULT 0
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
            downloaded BOOLEAN DEFAULT 0,
            handled BOOLEAN DEFAULT 0,
            nlp_full_lang TEXT,
            nlp_full_confidence INTEGER,
            nlp_para_count_lrl INTEGER DEFAULT 0,
            nlp_para_count INTEGER DEFAULT 0,
            nlp_para_perc_lrl INTEGER DEFAULT 0,
            FOREIGN KEY (query_id) REFERENCES queries(id)
        )
        ''')


def insert_query(query, type, lang):
    """Insert a new query into the queries table."""
    with get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO queries (query, type, lang) VALUES (?, ?, ?)", (query, type, lang))


def insert_url(query_id, type, url, doc_type=""):
    """Insert a new URL into the urls table."""
    with get_cursor() as cursor:
        url_hash = fileutils.hash_url(url)
        cursor.execute("""
            INSERT INTO urls (query_id, type, url, url_hash, doc_type)
            VALUES (?, ?, ?, ?, ?)
        """, (query_id, type, url, url_hash, doc_type))


def get_all_queries(lang, handled=None):
    """Retrieve all queries from the queries table."""

    with get_cursor() as cursor:
        if handled is None:
            cursor.execute("SELECT * FROM queries WHERE lang=?", (lang,))
            return cursor.fetchall()
        else:
            cursor.execute(
                "SELECT * FROM queries WHERE lang=? AND handled=?", (lang, handled,))
            return cursor.fetchall()


def get_all_urls(): 
    """Retrieve all URLs from the urls table."""

    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM urls")
        return cursor.fetchall()


def get_all_urls_filter_downloaded(downloaded=True): 
    """Retrieve all URLs from the urls table."""

    with get_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM urls WHERE downloaded=?", (downloaded,))
        return cursor.fetchall()

def get_all_urls_filter_downloaded_handled(downloaded=True, handled=True): 
    """Retrieve all URLs from the urls table."""

    with get_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM urls WHERE downloaded=? AND handled=?", (downloaded,handled,))
        return cursor.fetchall()

def get_all_urls_filter_handled(handled=True): 
    """Retrieve all URLs from the urls table."""

    with get_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM urls WHERE handled=?", (handleed,))
        return cursor.fetchall()

    
def query_exists(query):
    """Check if a query already exists in the queries table."""
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM queries WHERE query=?)", (query,))
        return bool(cursor.fetchone()[0])


def insert_query_if_not_exists(query, type, lang):
    """Insert a query into the queries table if it doesn't already exist."""
    if not query_exists(query):
        insert_query(query, type, lang)
        return True
    return False

def insert_url_if_not_exists(query_id, type, url, doc_type="", downloaded=False, handled=False):
    """Insert a URL into the urls table if it doesn't already exist."""
    with get_cursor() as cursor:
        url_hash = fileutils.hash_url(url)
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM urls WHERE url_hash=?)", (url_hash,))
        if not bool(cursor.fetchone()[0]):
            cursor.execute("""
                INSERT INTO urls (query_id, type, url, url_hash, doc_type, downloaded, handled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (query_id, type, url, url_hash, doc_type, downloaded, handled))
            return True
    return False

def get_url_by_id(id):
    """Retrieve a URL from the urls table by its ID."""
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM urls WHERE id=?", (id,))
        return cursor.fetchone()

def get_url_duplicate_handled_file_hash(url_id, file_hash): 
    """Retrieve a URL from the urls table by its File Hash, where its 'id' is different to 'url_id'"""
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM urls WHERE id!=? AND file_hash=? AND handled=True LIMIT 1",
                       (url_id, file_hash,))
        return cursor.fetchone()

def update_query_handled_by_id(id):
    """Updates the handled value to true for a given query ID in the queries table."""
    with get_cursor() as cursor:
        cursor.execute(
            "UPDATE queries SET handled=? WHERE id=?", (True, id))

def urls_exist(url_hashes, type):
    """Check if URLs with given hashes and type already exist in the database."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT url_hash FROM urls 
            WHERE url_hash IN ({seq}) AND type = ?""".format(seq=','.join(['?']*len(url_hashes))),
                       (*url_hashes, type))
        existing_hashes = {row[0] for row in cursor.fetchall()}
    return existing_hashes

# **** XXXX this would benefit from being refactored to avoid implicit elem[] positions
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
            INSERT INTO urls (query_id, type, url, url_hash, downloaded, handled)
            VALUES (?, ?, ?, ?, ?, ?)
        """, filtered_data)

def set_query_as_handled(query_id):
    """Sets the handled flag of a query to True."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE queries
            SET handled = True
            WHERE id = ?
        """, (query_id,))

def set_url_as_downloaded(url_id):
    """Sets the downloaded flag of a url to True."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE urls
            SET downloaded = True
            WHERE id = ?
        """, (url_id,))

def set_url_as_handled(url_id):
    """Sets the handled flag of a url to True."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE urls
            SET handled = True
            WHERE id = ?
        """, (url_id,))
        
def update_url_fileinfo(url_id, file_hash, doc_type, downloaded=True):
    """Sets multiple values of the URL."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE urls
            SET file_hash  = ?,
                doc_type  = ?,
                downloaded = ?
            WHERE id = ?
        """, (file_hash,doc_type,downloaded, url_id))

def update_url_langinfo(url_id, nlp_full_lang, nlp_full_confidence, nlp_para_count_lrl, nlp_para_count, nlp_para_perc_lrl, handled=True): 
    """Sets multiple values of the URL."""

    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE urls
            SET nlp_full_lang  = ?,
                nlp_full_confidence  = ?,
                nlp_para_count_lrl  = ?,
                nlp_para_count  = ?,
                nlp_para_perc_lrl  = ?,
                handled = ?
            WHERE id = ?
        """, (nlp_full_lang, nlp_full_confidence, nlp_para_count_lrl, nlp_para_count, nlp_para_perc_lrl, handled, url_id))

# **** XXXX
# original, before split in two, above for download and nlp-handled
#def update_url(url_id, file_hash, doc_type, full_lang, confidence, paragraph_lang):
#    """Sets multiple values of the URL."""
#    with get_cursor() as cursor:
#        cursor.execute("""
#            UPDATE urls
#            SET handled = True,
#                file_hash  = ?,
#                doc_type  = ?,
#                full_lang  = ?,
#                confidence  = ?,
#                paragraph_lang  = ?
#            WHERE id = ?
#        """, (file_hash, doc_type, full_lang, confidence, paragraph_lang, url_id,))

        
def set_all_queries_unhandled():
    """Set all queries in the database as unhandled."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE queries
            SET handled = False
        """)

def set_all_urls_undownloaded():
    """Set all urls in the database as unhandled."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE urls
            SET downloaded = False
        """)

def set_all_urls_unhandled():
    """Set all urls in the database as unhandled."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE urls
            SET handled = False
        """)

        
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

#def set_all_queries_lang_to_maori():
#    """Sets the lang field of all queries in the database to 'MAORI'."""
#    with get_cursor() as cursor:
#        cursor.execute("""
#            UPDATE queries
#            SET lang = 'MAORI'
#        """)

# Display
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
    return dict(result)

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
    return dict(result)

# **** XXXX
# Not a thing for *queries* database table!!!
# def count_downloaded_undownloaded_queries():
#     with get_cursor() as cursor:
#         cursor.execute("""
#             SELECT handled, COUNT(*) as count
#             FROM queries
#             GROUP BY downloaded
#         """)
#         results = cursor.fetchall()
#         output = {"undownloaded": 0, "downloaded": 0}
#         for result in results:
#             key = "undownloaded" if result[0] == 0 else "downloaded"
#             output[key] = result[1]
#         return output

def count_handled_unhandled_queries():
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT handled, COUNT(*) as count
            FROM queries
            GROUP BY handled
        """)
        results = cursor.fetchall()
        output = {"unhandled": 0, "handled": 0}
        for result in results:
            key = "unhandled" if result[0] == 0 else "handled"
            output[key] = result[1]
        return output

    
def count_duplicate_queries():
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT query, COUNT(*) as count
            FROM queries
            GROUP BY query
            HAVING COUNT(*) > 1
        """)
        result = cursor.fetchall()
        return result

def count_duplicate_url_hashes():
    with get_cursor() as cursor:
        # Get the total count of all duplicates (not just the number of distinct hashes that have duplicates)
        cursor.execute("""
            SELECT SUM(dup_count) as total_duplicates
            FROM (
                SELECT COUNT(*) as dup_count
                FROM urls
                GROUP BY url_hash
                HAVING COUNT(*) > 1
            ) as duplicates
        """)
        total_duplicates_row = cursor.fetchone()
        total_duplicates = total_duplicates_row[0] if total_duplicates_row else 0

        # Get the top 3 hashes with the most duplicates
        cursor.execute("""
            SELECT url_hash, COUNT(*) as count
            FROM urls
            GROUP BY url_hash
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 5
        """)
        top_hashes = cursor.fetchall()
        
        # Construct the result
        result = {
            "total_duplicate_url_hashes": total_duplicates,
            "top_duplicate_url_hashes": [{hash_row[0]: hash_row[1]} for hash_row in top_hashes]
        }
        return result

def count_duplicate_file_hashes():
    with get_cursor() as cursor:
        # Get the total count of all duplicates (ignoring NULL values)
        cursor.execute("""
            SELECT SUM(dup_count) as total_duplicates
            FROM (
                SELECT file_hash, COUNT(*) as dup_count
                FROM urls
                WHERE file_hash IS NOT NULL
                GROUP BY file_hash
                HAVING COUNT(*) > 1
            ) as duplicates
        """)
        total_duplicates_row = cursor.fetchone()
        total_duplicates = total_duplicates_row[0] if total_duplicates_row else 0
        # Get the top 3 file hashes with the most duplicates (ignoring NULL values)
        cursor.execute("""
            SELECT url, COUNT(*) as count
            FROM urls
            WHERE file_hash IS NOT NULL
            GROUP BY file_hash
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 5
        """)
        top_hashes = cursor.fetchall()
        # Get the total count of NULL file_hash values
        cursor.execute("""
            SELECT COUNT(*)
            FROM urls
            WHERE file_hash IS NULL
        """)
        null_file_hash_count_row = cursor.fetchone()
        null_file_hash_count = null_file_hash_count_row[0] if null_file_hash_count_row else 0
        # Construct the result
        result = {
            "total_duplicate_file_hashes": total_duplicates,
            "top_duplicate_file_hashes": [{hash_row[0]: hash_row[1]} for hash_row in top_hashes],
            "total_null_file_hashes": null_file_hash_count
        }
        return result

    
# Count of Document Types:
def count_doc_types_for_language_total(lang):
    """Returns the count of each document type and the count of each type resulting in a specific language."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT doc_type, 
                   COUNT(*) as total_count, 
                   SUM(CASE WHEN nlp_full_lang = ? THEN 1 ELSE 0 END) as language_count
            FROM urls
            GROUP BY doc_type
        """, (lang,))
        result = cursor.fetchall()
        return [{"doc_type": row[0], "total_count": row[1], "language_count": row[2]} for row in result]

def count_doc_types_for_language_total_lrlparacount():
    """Returns the count of each document type and the count of each type resulting in a specific language."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT doc_type, 
                   COUNT(*) as total_count, 
                   SUM(CASE WHEN nlp_para_count_lrl > 0 THEN 1 ELSE 0 END) as language_count
            FROM urls
            GROUP BY doc_type
        """)
        result = cursor.fetchall()
        return [{"doc_type": row[0], "total_count": row[1], "language_count": row[2]} for row in result]
    

# Count URLs with Low Confidence for a Given Language and get top 5 lowest:
def count_low_confidence_urls(lang, confidence_threshold=0.9):
    with get_cursor() as cursor:
        # Count total URLs with low confidence
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM urls
            WHERE nlp_full_lang = ? AND nlp_full_confidence < ?
        """, (lang, confidence_threshold))
        total_count_row = cursor.fetchone()
        total_count = total_count_row[0] if total_count_row else 0

        # Get top 5 URLs with lowest confidence
        cursor.execute("""
            SELECT url, nlp_full_confidence
            FROM urls
            WHERE nlp_full_lang = ? AND nlp_full_confidence < ?
            ORDER BY nlp_full_confidence ASC
            LIMIT 5
        """, (lang, confidence_threshold))
        lowest = cursor.fetchall()

        result = {
            "total_low_confidence": total_count,
            "top_5_lowest_confidence": lowest
        }
        return result

# Count URLs with Low Confidence for a Given Language and get top 5 lowest:
def count_low_confidence_urls_lrlparacount(confidence_threshold=0.9):
    with get_cursor() as cursor:
        # Count total URLs with low confidence
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM urls
            WHERE nlp_para_count_lrl > 0 AND nlp_full_confidence < ?
        """, (confidence_threshold,))
        total_count_row = cursor.fetchone()
        total_count = total_count_row[0] if total_count_row else 0

        # Get top 5 URLs with lowest confidence
        cursor.execute("""
            SELECT url, nlp_full_confidence
            FROM urls
            WHERE nlp_para_count_lrl > 0 AND nlp_full_confidence < ?
            ORDER BY nlp_full_confidence ASC
            LIMIT 5
        """, (confidence_threshold,))
        lowest = cursor.fetchall()

        result = {
            "total_low_confidence": total_count,
            "top_5_lowest_confidence": lowest
        }
        return result

    
# Count URLs with High Confidence for a Given Language and get top 5 highest:
def count_high_confidence_urls(lang, confidence_threshold=0.9):
    with get_cursor() as cursor:
        # Count total URLs with low confidence
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM urls
            WHERE nlp_full_lang = ? AND nlp_full_confidence >= ?
        """, (lang, confidence_threshold))
        total_count_row = cursor.fetchone()
        total_count = total_count_row[0] if total_count_row else 0

        # Get top 5 URLs with highest confidence
        cursor.execute("""
            SELECT url, nlp_full_confidence
            FROM urls
            WHERE nlp_full_lang = ? AND nlp_full_confidence >= ?
            ORDER BY nlp_full_confidence DESC
            LIMIT 5
        """, (lang, confidence_threshold))
        lowest = cursor.fetchall()

        result = {
            "total_high_confidence": total_count,
            "top_5_highest_confidence": lowest
        }
        return result

# Count URLs with High Confidence for a Given Language and get top 5 highest:
def count_high_confidence_urls_lrlparacount(confidence_threshold=0.9):
    with get_cursor() as cursor:
        # Count total URLs with low confidence
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM urls
            WHERE nlp_para_count_lrl > 0 AND nlp_full_confidence >= ?
        """, (confidence_threshold,))
        total_count_row = cursor.fetchone()
        total_count = total_count_row[0] if total_count_row else 0

        # Get top 5 URLs with highest confidence
        cursor.execute("""
            SELECT url, nlp_full_confidence
            FROM urls
            WHERE nlp_para_count_lrl > 0 AND nlp_full_confidence >= ?
            ORDER BY nlp_full_confidence DESC
            LIMIT 5
        """, (confidence_threshold,))
        lowest = cursor.fetchall()

        result = {
            "total_high_confidence": total_count,
            "top_5_highest_confidence": lowest
        }
        return result
    

# Count URLs with Low Paragraph Percentage and Low Confidence for a Given Language and get top 5 lowest:
def count_low_para_percent_low_confidence_urls(lang, para_threshold=90, confidence_threshold=0.9):
    with get_cursor() as cursor:
        # Count total URLs with low paragraph percentage and low confidence
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM urls
            WHERE nlp_full_lang = ? AND nlp_para_perc_lrl < ? AND nlp_full_confidence < ?
        """, (lang, para_threshold, confidence_threshold))
        total_count_row = cursor.fetchone()
        total_count = total_count_row[0] if total_count_row else 0

        # Get top 5 URLs with lowest paragraph percentage and low confidence
        cursor.execute("""
            SELECT url, nlp_para_perc_lrl, nlp_full_confidence
            FROM urls
            WHERE nlp_full_lang = ? AND nlp_para_perc_lrl < ? AND nlp_full_confidence < ?
            ORDER BY nlp_para_perc_lrl ASC, nlp_full_confidence ASC
            LIMIT 5
        """, (lang, para_threshold, confidence_threshold))
        lowest = cursor.fetchall()

        result = {
            "total_low_para_percent_low_confidence": total_count,
            "top_5_lowest_para_percent_low_confidence": lowest
        }
        return result


# Count URLs with Low Paragraph Percentage and Low Confidence for a Given Language and get top 5 lowest:
def count_low_para_percent_low_confidence_urls_lrlparacount(para_threshold=90, confidence_threshold=0.9):
    with get_cursor() as cursor:
        # Count total URLs with low paragraph percentage and low confidence
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM urls
            WHERE nlp_para_count_lrl > 0 AND nlp_para_perc_lrl < ? AND nlp_full_confidence < ?
        """, (para_threshold, confidence_threshold))
        total_count_row = cursor.fetchone()
        total_count = total_count_row[0] if total_count_row else 0

        # Get top 5 URLs with lowest paragraph percentage and low confidence
        cursor.execute("""
            SELECT url, nlp_para_perc_lrl, nlp_full_confidence
            FROM urls
            WHERE nlp_para_count_lrl > 0 AND nlp_para_perc_lrl < ? AND nlp_full_confidence < ?
            ORDER BY nlp_para_perc_lrl ASC, nlp_full_confidence ASC
            LIMIT 5
        """, (para_threshold, confidence_threshold))
        lowest = cursor.fetchall()

        result = {
            "total_low_para_percent_low_confidence": total_count,
            "top_5_lowest_para_percent_low_confidence": lowest
        }
        return result
    
# Count URLs with High Paragraph Percentage and High Confidence for a Given Language and get top 5 highest:
def count_high_para_percent_high_confidence_urls(lang, para_threshold=90, confidence_threshold=0.9):
    with get_cursor() as cursor:
        # Count total URLs with high paragraph percentage and high confidence
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM urls
            WHERE nlp_full_lang = ? AND nlp_para_perc_lrl >= ? AND nlp_full_confidence >= ?
        """, (lang, para_threshold, confidence_threshold))
        total_count_row = cursor.fetchone()
        total_count = total_count_row[0] if total_count_row else 0

        # Get top 5 URLs with highest paragraph percentage and high confidence
        cursor.execute("""
            SELECT url, nlp_para_perc_lrl, nlp_full_confidence
            FROM urls
            WHERE nlp_full_lang = ? AND nlp_para_perc_lrl >= ? AND nlp_full_confidence >= ?
            ORDER BY nlp_para_perc_lrl DESC, nlp_full_confidence DESC
            LIMIT 5
        """, (lang, para_threshold, confidence_threshold))
        highest = cursor.fetchall()

        result = {
            "total_high_para_percent_high_confidence": total_count,
            "top_5_highest_para_percent_high_confidence": highest
        }
        return result

# Count URLs with High Paragraph Percentage and High Confidence for a Given Language and get top 5 highest:
def count_high_para_percent_high_confidence_urls_lrlparacount(para_threshold=90, confidence_threshold=0.9):
    with get_cursor() as cursor:
        # Count total URLs with high paragraph percentage and high confidence
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM urls
            WHERE nlp_para_count_lrl > 0 AND nlp_para_perc_lrl >= ? AND nlp_full_confidence >= ?
        """, (para_threshold, confidence_threshold))
        total_count_row = cursor.fetchone()
        total_count = total_count_row[0] if total_count_row else 0

        # Get top 5 URLs with highest paragraph percentage and high confidence
        cursor.execute("""
            SELECT url, nlp_para_perc_lrl, nlp_full_confidence
            FROM urls
            WHERE nlp_para_count_lrl > 0 AND nlp_para_perc_lrl >= ? AND nlp_full_confidence >= ?
            ORDER BY nlp_para_perc_lrl DESC, nlp_full_confidence DESC
            LIMIT 5
        """, (para_threshold, confidence_threshold))
        highest = cursor.fetchall()

        result = {
            "total_high_para_percent_high_confidence": total_count,
            "top_5_highest_para_percent_high_confidence": highest
        }
        return result
    
# Not currently called
def get_url_counts_by_query_id(lang, query_id):
    """Returns the total number of URLs, the number of URLs not downloaded, the number of unhandled URLs, and the number of URLs with non-null nlp_full_lang for a given query ID."""
    with get_cursor() as cursor:
        # Total URLs count
        cursor.execute(
            "SELECT COUNT(*) FROM urls WHERE query_id=?", (query_id,))
        total_count = cursor.fetchone()[0]

        # Total unhandled URLs count
        cursor.execute(
            "SELECT COUNT(*) FROM urls WHERE query_id=? AND downloaded=?", (query_id, False))
        undownloaded_count = cursor.fetchone()[0]
        # Total unhandled URLs count
        cursor.execute(
            "SELECT COUNT(*) FROM urls WHERE query_id=? AND handled=?", (query_id, False))
        unhandled_count = cursor.fetchone()[0]        

        # Total URLs with non-null nlp_full_lang
        cursor.execute(
            "SELECT COUNT(*) FROM urls WHERE query_id=? AND nlp_full_lang=?", (query_id, lang))
        full_lang_count = cursor.fetchone()[0]

        # Total URLs with nlp_para_count_lrl > 0
        cursor.execute(
            "SELECT COUNT(*) FROM urls WHERE query_id=? AND nlp_para_count_lrl>0", (query_id))
        para_lang_count = cursor.fetchone()[0]
        
        return {
            "total_count": total_count,
            "undownloaded_count": undownloaded_count,
            "unhandled_count": unhandled_count,
            "full_lang_count": full_lang_count,
            "para_lang_count": para_lang_count # Actually count of how many web pages have at least one lrl para (not the number of paras in total)
        }

def get_url_counts_by_type(lang, search_type):
    """
    Returns the total number of URLs, the number of unhandled URLs, and the number of URLs with a specific nlp_full_lang 
    for all queries of a given language and search type.
    """
    if "_selenium" in search_type:
        search_type = search_type.replace("_selenium", "")
    with get_cursor() as cursor:
        # Join queries and urls tables, then filter by lang and search type
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN u.downloaded = 0 THEN 1 ELSE 0 END) as undownloaded_count,
                SUM(CASE WHEN u.handled = 0 THEN 1 ELSE 0 END) as unhandled_count,
                SUM(CASE WHEN u.nlp_full_lang = ? THEN 1 ELSE 0 END) as full_lang_count,
                SUM(CASE WHEN u.nlp_para_count_lrl > 0 THEN 1 ELSE 0 END) as full_lang_count
            FROM queries q
            JOIN urls u on q.id = u.query_id
            WHERE q.lang = ? AND u.type = ?
        """, (lang, lang, search_type))

        result = cursor.fetchone()
        undownloaded = 0
        if result[1] is not None:
            undownloaded = result[1]
        unhandled = 0
        if result[2] is not None:
            unhandled = result[2]
        full_lang = 0
        if result[3] is not None:
            full_lang = result[3]
        para_lang = 0
        if result[4] is not None:
            para_lang = result[4]
            
        return {
            "total_count": result[0],
            "undownloaded_count": unhandled,
            "unhandled_count": unhandled,
            "full_lang_count": full_lang,
            "para_lang_count": full_lang
        }
    
# def get_top_queries_with_most_urls(lang):
#     """Returns the top queries with the most URLs found and count of Maori URLs."""
#     with get_cursor() as cursor:
#         cursor.execute("""
#             SELECT q.query, COUNT(u.id) as total_count, 
#                    SUM(CASE WHEN u.full_lang = ? THEN 1 ELSE 0 END) as lang_count
#             FROM queries q
#             JOIN urls u ON q.id = u.query_id
#             GROUP BY q.query
#             ORDER BY total_count DESC
#             LIMIT 5
#         """, (lang,))
#         results = cursor.fetchall()
#     return [{"query": row[0], "total_url_count": row[1], "lang_url_count": row[2]} for row in results]


def get_top_queries_with_most_urls(lang):
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT q.query, q.type, COUNT(u.id) as total_count, 
                   SUM(CASE WHEN u.nlp_full_lang = ? THEN 1 ELSE 0 END) as lang_count
            FROM queries q
            JOIN urls u ON q.id = u.query_id
            GROUP BY q.query
            ORDER BY total_count DESC
        """, (lang,))
        results = cursor.fetchall()
        return [{"index": idx, "query": row[0], "type": row[1], "total_url_count": row[2], "lang_url_count": row[3]} 
                for idx, row in enumerate(results, start=1)]

def get_top_queries_with_most_urls_lrlparacount():
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT q.query, q.type, COUNT(u.id) as total_count, 
                   SUM(CASE WHEN u.nlp_para_count_lrl > 0 THEN 1 ELSE 0 END) as lang_count
            FROM queries q
            JOIN urls u ON q.id = u.query_id
            GROUP BY q.query
            ORDER BY total_count DESC
        """)
        results = cursor.fetchall()
        return [{"index": idx, "query": row[0], "type": row[1], "total_url_count": row[2], "lang_url_count": row[3]} 
                for idx, row in enumerate(results, start=1)]    

# def get_top_queries_with_most_urls_for_language(lang):
#     with get_cursor() as cursor:
#         cursor.execute("""
#             SELECT q.query, q.type, COUNT(u.id) as total_count, 
#                    SUM(CASE WHEN u.full_lang = ? THEN 1 ELSE 0 END) as lang_count
#             FROM queries q
#             JOIN urls u ON q.id = u.query_id
#             GROUP BY q.query, q.type
#             ORDER BY lang_count DESC, total_count DESC
#         """, (lang,))
#         results = cursor.fetchall()
#         return [{"index": idx, "query": row[0], "type": row[1], "total_url_count": row[2], "lang_url_count": row[3]} 
#                 for idx, row in enumerate(results, start=1)]
    

# def get_top_queries_with_least_urls(lang):
#     with get_cursor() as cursor:
#         cursor.execute("""
#             SELECT q.query, q.type, COUNT(u.id) as total_count, 
#                    SUM(CASE WHEN u.full_lang = ? THEN 1 ELSE 0 END) as lang_count
#             FROM queries q
#             LEFT JOIN urls u ON q.id = u.query_id
#             GROUP BY q.query, q.type
#             HAVING total_count > 0
#             ORDER BY total_count ASC
#         """, (lang,))
#         results = cursor.fetchall()
#         return [{"index": idx, "query": row[0], "type": row[1], "total_url_count": row[2], "lang_url_count": row[3]} 
#                 for idx, row in enumerate(results, start=1)]


def count_queries_by_type_zero_urls():
    """Returns the count of queries by type for which no URLs have been found."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT q.type, COUNT(*) as count
            FROM queries q
            LEFT JOIN urls u ON q.id = u.query_id
            WHERE u.id IS NULL
            GROUP BY q.type
        """)
        result = cursor.fetchall()
        return dict(result)

def count_query_types_by_total_urls(lang):
    """Returns the count of queries by type for a language."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT q.type,
                   COUNT(u.id) as total_url_count,
                   SUM(CASE WHEN u.nlp_full_lang = ? THEN 1 ELSE 0 END) as total_url_with_lang_count
            FROM queries q
            LEFT JOIN urls u ON q.id = u.query_id
            GROUP BY q.type
        """, (lang,))
        result = cursor.fetchall()
        return [{"type": row[0], "total_url_count": row[1], "total_url_with_lang_count": row[2]} for row in result]

def count_query_types_by_total_urls_lrlparalang():
    """Returns the count of queries by type for a language."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT q.type,
                   COUNT(u.id) as total_url_count,
                   SUM(CASE WHEN u.nlp_para_count_lrl > 0 THEN 1 ELSE 0 END) as total_url_with_lang_count
            FROM queries q
            LEFT JOIN urls u ON q.id = u.query_id
            GROUP BY q.type
        """)
        result = cursor.fetchall()
        return [{"type": row[0], "total_url_count": row[1], "total_url_with_lang_count": row[2]} for row in result]

    
def get_domain_counts(lang):
    """Returns the count of unique domains with their totals for a language."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT url, nlp_full_lang
            FROM urls
        """)
        urls = cursor.fetchall()
        
    domain_counts = {}
    domain_language_counts = {}
    for url, full_lang in urls:
        domain = urlparse(url).netloc
        # Count total domains
        if domain not in domain_counts:
            domain_counts[domain] = 0
        domain_counts[domain] += 1
        if full_lang== lang:
            if domain not in domain_language_counts:
                domain_language_counts[domain] = 0
            domain_language_counts[domain] += 1
    result = {
        'total_domains': len(domain_counts),
        'total_with_language': len(domain_language_counts),
        'domains': domain_counts,
        'language_domains': domain_language_counts
    }
    return result

def get_domain_counts_lrlparacount():
    """Returns the count of unique domains with their totals for a language."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT url, nlp_para_count_lrl
            FROM urls
        """)
        urls = cursor.fetchall()
        
    domain_counts = {}
    domain_language_counts = {}
    for url, para_count_lrl in urls:
        domain = urlparse(url).netloc
        # Count total domains
        if domain not in domain_counts:
            domain_counts[domain] = 0
        domain_counts[domain] += 1
        if para_count_lrl > 0:
            if domain not in domain_language_counts:
                domain_language_counts[domain] = 0
            domain_language_counts[domain] += 1
    result = {
        'total_domains': len(domain_counts),
        'total_with_language': len(domain_language_counts),
        'domains': domain_counts,
        'language_domains': domain_language_counts
    }
    return result


def count_urls_by_confidence_and_paragraph_percentage_ranges(lang):
    confidence_ranges = [(i/10, (i+1)/10) for i in range(0, 10)]  # 0.0-0.1, 0.1-0.2, ..., 0.9-1.0
    paragraph_ranges = [(i, i+10) for i in range(0, 100, 10)]  # 0-10%, 10-20%, ..., 90-100%

    results = {'confidence': {}, 'paragraph': {}}

    with get_cursor() as cursor:
        # Count URLs in confidence ranges, excluding 1.0
        for lower, upper in confidence_ranges:
            upper_bound = upper if upper < 1.0 else 0.99
            cursor.execute("""
                SELECT COUNT(*) 
                FROM urls
                WHERE nlp_full_lang = ? AND nlp_full_confidence >= ? AND nlp_full_confidence < ?
            """, (lang, lower, upper_bound))
            count = cursor.fetchone()[0]
            range_key = f'{lower}-{upper_bound}'
            results['confidence'][range_key] = count

        # Count URLs with exactly 1.0 confidence
        cursor.execute("""
            SELECT COUNT(*)
            FROM urls
            WHERE nlp_full_lang = ? AND nlp_full_confidence = 1.0
        """, (lang,))
        count_1 = cursor.fetchone()[0]
        results['confidence']['1.0'] = count_1

        # Count URLs in paragraph percentage ranges, excluding 100%
        for lower, upper in paragraph_ranges:
            upper_bound = upper if upper < 100 else 99
            cursor.execute("""
                SELECT COUNT(*) 
                FROM urls
                WHERE nlp_full_lang = ? AND nlp_para_perc_lrl >= ? AND nlp_para_perc_lrl < ?
            """, (lang, lower, upper_bound))
            count = cursor.fetchone()[0]
            range_key = f'{lower}-{upper_bound}%'
            results['paragraph'][range_key] = count

        # Count URLs with exactly 100% paragraph percentage
        cursor.execute("""
            SELECT COUNT(*)
            FROM urls
            WHERE nlp_full_lang = ? AND nlp_para_perc_lrl = 100
        """, (lang,))
        count_100 = cursor.fetchone()[0]
        results['paragraph']['100%'] = count_100

    return results


def count_urls_by_confidence_and_paragraph_percentage_ranges_lrlparacount():
    confidence_ranges = [(i/10, (i+1)/10) for i in range(0, 10)]  # 0.0-0.1, 0.1-0.2, ..., 0.9-1.0
    paragraph_ranges = [(i, i+10) for i in range(0, 100, 10)]  # 0-10%, 10-20%, ..., 90-100%

    results = {'confidence': {}, 'paragraph': {}}

    with get_cursor() as cursor:
        # Count URLs in confidence ranges, excluding 1.0
        for lower, upper in confidence_ranges:
            upper_bound = upper if upper < 1.0 else 0.99
            cursor.execute("""
                SELECT COUNT(*) 
                FROM urls
                WHERE nlp_para_count_lrl > 0 AND nlp_full_confidence >= ? AND nlp_full_confidence < ?
            """, (lower, upper_bound))
            count = cursor.fetchone()[0]
            range_key = f'{lower}-{upper_bound}'
            results['confidence'][range_key] = count

        # Count URLs with exactly 1.0 confidence
        cursor.execute("""
            SELECT COUNT(*)
            FROM urls
            WHERE nlp_para_count_lrl > 0 AND nlp_full_confidence = 1.0
        """)
        count_1 = cursor.fetchone()[0]
        results['confidence']['1.0'] = count_1

        # Count URLs in paragraph percentage ranges, excluding 100%
        for lower, upper in paragraph_ranges:
            upper_bound = upper if upper < 100 else 99
            cursor.execute("""
                SELECT COUNT(*) 
                FROM urls
                WHERE nlp_para_count_lrl > 0 AND nlp_para_perc_lrl >= ? AND nlp_para_perc_lrl < ?
            """, (lower, upper_bound))
            count = cursor.fetchone()[0]
            range_key = f'{lower}-{upper_bound}%'
            results['paragraph'][range_key] = count

        # Count URLs with exactly 100% paragraph percentage
        cursor.execute("""
            SELECT COUNT(*)
            FROM urls
            WHERE nlp_para_count_lrl > 0 AND nlp_para_perc_lrl = 100
        """)
        count_100 = cursor.fetchone()[0]
        results['paragraph']['100%'] = count_100

    return results


