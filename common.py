import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from structlog import get_logger

import sqlite3
from sqlite3 import Connection, Cursor

# Load configuration from config.py
from .config import config

__all__ = ['debug_to_console', 'check_or_abort',
           'setRelease', 'getDBHandle',
           'getNextImage', 'getProblems',
           'getUsername', 'username2uid',
           'getUID', 'getUIDFromSID',
           'numberSuffix', 'userClass',
           'missingFilesForNextClass',
           'getActivity','giveBonusPoints',
           'exp_checker_logger',
]


# Set default timezone if not already set
if not os.getenv('TZ'):
    os.environ['TZ'] = 'GMT'

def debug_to_console(data: any) -> None:
    """Print the given data to the JavaScript console."""
    output = data
    if isinstance(output, list):
        output = ','.join(str(x) for x in output)
    print(f"<script>console.log('Debug Objects: {output}')</script>")

def check_or_abort(dbh: Optional[Connection]) -> Connection:
    """Check if the database handle is valid, otherwise abort the request."""
    if not dbh:
        raise Exception(500, "Internal Server Error")
    return dbh

def GETorPOST(param: str) -> Optional[str]:
    """Get the value of the given parameter from either GET or POST."""
    if param in os.environ.get('QUERY_STRING', ''):
        return os.environ.get(param)
    if param in os.environ.get('REQUEST_METHOD', ''):
        return os.environ.get(param)
    return None

def setRelease() -> None:
    """Set the current release based on the request parameters."""
    global config
    config['release'] = GETorPOST('release')
    if config['release'] is None or config['release'] not in config['releases']:
        config['release'] = config['releases'][-1]

def getDBHandle() -> Connection:
    """Get a database handle for the current release."""
    setRelease()
    global config
    BASE_DIR = Path(__file__).resolve().parent
    db_file = BASE_DIR / config['filedb'][config['release']]
    if not os.path.exists(db_file):
        check_or_abort(None)
    dbh = sqlite3.connect(f'{db_file}')
    dbh.row_factory = sqlite3.Row
    return check_or_abort(dbh)

def getNextImage(dbh: Connection,
                 params: Dict,
                 uid: Optional[int]) -> Optional[Dict[str, any]]:
    """Get the next image to display based on the request parameters."""
    global config
    sql = f'SELECT "{config["release"]}" as release, files.fileid, expname, ccd, band, name FROM files'

    if params.get('expname') and params.get('ccd'):
        sql += ' WHERE ccd = ? AND files.expname = ? LIMIT 1'
        res = dbh.execute(sql, (params['ccd'], params['expname']))
    elif params.get('problem'):
        problem = config['problem_code'][params['problem']]
        sql += f' JOIN qa ON (files.fileid = qa.fileid) WHERE qa.problem = {problem}'
        if params.get('detail'):
            sql += f""" AND detail = '{params["detail"]}'"""
        sql += ' ORDER BY RANDOM() LIMIT 1'
        res = dbh.execute(sql)
    else:
        priority = "1" # ADW: not sure what this does
        # to create redundancy: draw every n-th image from list with existing qa
        nth = 2
        if random.randint(0, nth) < 1:
            fallback = sql
            sql += ' JOIN qa ON (files.fileid = qa.fileid)'
            if uid:
                sql += f' WHERE {priority} AND qa.userid != {uid}'
                sql += ' GROUP BY qa.fileid ORDER BY RANDOM() LIMIT 1'
                res = dbh.execute(sql)
                row = res.fetchone()
                if row:
                    return dict(row)
            sql = fallback
        sql += f" WHERE {priority} ORDER BY RANDOM() LIMIT 1"
        res = dbh.execute(sql)

    row = res.fetchone()

    return dict(row) if row else None

def getProblems(dbh: Connection, fileid: int, qa_id: Optional[int] = None) -> List[Dict[str, any]]:
    """Get the problems associated with the given file ID."""
    global config
    sql = 'SELECT problem, x, y, detail FROM qa WHERE fileid = ?'
    if qa_id is not None:
        sql += ' AND qaid = ?'
    else:
        sql += ' AND problem != 0 AND problem <= 1000'
    res = dbh.execute(sql, (fileid, qa_id) if qa_id else (fileid,))
    problem_code = {v: k for k, v in config['problem_code'].items()}
    problems = []
    for row in res:
        problem, x, y, detail = row
        if problem > 0:
            problem = problem_code[problem]
        else:
            problem = f"-{problem_code[-problem]}"
        problems.append({
            'problem': problem,
            'x': int(x),
            'y': int(y),
            'detail': detail
        })
    return problems

def getUsername() -> str:
    #return $_SERVER['uid'];
    return 'kadrlica';

def username2uid(username: str) -> int:
    uid = 0
    mult = 1
    for c in username.upper():
        uid += (ord(c) - 47) * mult
        mult *= 49
    return uid

def getUID() -> int:
    username = getUsername()
    return username2uid(username)

def getUIDFromSID(dbh: Connection) -> int:
    uid = getUID()
    return uid

def numberSuffix(num: int) -> str:
    """Get the ordinal suffix for the given number."""
    if num == 1:
        return '1st'
    if num == 2:
        return '2nd'
    elif num == 3:
        return '3rd'
    return f'{num}th'

def userClass(total_files: int) -> int:
    """Determine the user class based on the total number of files."""
    global config
    if total_files / config['images_per_fp'] >= 1000:
        return 8
    if total_files / config['images_per_fp'] >= 100:
        return 7
    if total_files / config['images_per_fp'] >= 10:
        return 6
    if total_files / config['images_per_fp'] >= 5:
        return 5
    if total_files / config['images_per_fp'] >= 2:
        return 4
    if total_files / config['images_per_fp'] >= 1:
        return 3
    if total_files >= 100:
        return 2
    if total_files >= 10:
        return 1
    return 0

def missingFilesForNextClass(total_files: int, userclass: int) -> int:
    """Calculate the number of missing files to reach the next user class."""
    global config
    if userclass == 0:
        return 10 - total_files
    if userclass == 1:
        return 100 - total_files
    if userclass == 2:
        return config['images_per_fp'] - total_files
    if userclass == 3:
        return 5 * config['images_per_fp'] - total_files
    if userclass == 4:
        return 10 * config['images_per_fp'] - total_files
    if userclass == 5:
        return 100 * config['images_per_fp'] - total_files
    if userclass == 6:
        return 1000 * config['images_per_fp'] - total_files
    if userclass == 7:
        return 10000 * config['images_per_fp'] - total_files
    return 0

def getActivity(dbh: Connection, uid: int, date: Optional[str] = None) -> Dict[str, int]:
    """Get the user's activity based on the number of files reviewed."""
    activity = {}
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    sql = f"SELECT COUNT(DISTINCT(fileid)) as activity FROM qa WHERE userid={uid} AND timestamp > '{date}'"
    res = dbh.cursor().execute(sql)
    row = res.fetchone()
    activity['today'] = row[0] if row else 0
    sql = f"SELECT total_files FROM submissions WHERE userid={uid}"
    res = dbh.cursor().execute(sql)
    row = res.fetchone()
    activity['alltime'] = row[0] if row else 0
    return activity

def giveBonusPoints(dbh: Connection, uid: int, points: int) -> None:
    """Give bonus points to the user."""
    stmt = dbh.cursor()
    stmt.execute("UPDATE submissions SET total_files = total_files + ? WHERE userid = ?", (points, uid))
    check_or_abort(stmt)

def exp_checker_logger() -> Any:
    logger = get_logger()
    return logger
