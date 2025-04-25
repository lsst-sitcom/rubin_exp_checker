import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from structlog import get_logger

import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import Engine

# Load configuration from config.py
from .config import config

__all__ = ['debug_to_console',
           'getDBHandle',
           'getNextImage', 'getProblems',
           'username2uid', 'uid2username',
           'numberSuffix', 'userClass',
           'missingFilesForNextClass',
           'getActivity','giveBonusPoints',
           'exp_checker_logger',
]

logger = get_logger()

# Set default timezone if not already set
if not os.getenv('TZ'):
    os.environ['TZ'] = 'GMT'

def debug_to_console(data: Any) -> None:
    """Print the given data to the JavaScript console."""
    output = data
    if isinstance(output, list):
        output = ','.join(str(x) for x in output)
    print(f"<script>console.log('Debug Objects: {output}')</script>")

def getDBHandle() -> Engine:
    """Get a database handle for the current release."""

    db_url = sqlalchemy.URL.create(config.db_engine,
                                   username=config.db_username,
                                   password=config.db_password,
                                   host=config.db_host,
                                   database=config.db_dbname)
    db_engine = sqlalchemy.create_engine(db_url)
    if not db_engine:
        raise Exception(500, "Internal Server Error")
    return db_engine

def getNextImage(
        engine: Engine,
        params: Dict,
        uid: Optional[int]
) -> Optional[Dict[str, Any]]:
    """Get the next image to display based on the request parameters."""
    params_dict = {"release": config["release"]}

    # Initial image column selection
    sql = f"SELECT :release as release, files.fileid, expname, ccd, band, name FROM files"

    if params.get('expname') and params.get('ccd'):
        sql += ' WHERE ccd = :ccd AND files.expname = :expname LIMIT 1'
        params_dict.update({"ccd": params['ccd'], "expname": params['expname']})
        # res = dbh.execute(text(sql), {"ccd": params['ccd'], "expname": params['expname']})

    elif params.get('expname'):
        sql += ' WHERE files.expname = :expname ORDER BY RANDOM() LIMIT 1'
        params_dict.update({"expname": params['expname']})
        #res = dbh.execute(text(sql), {"expname": params['expname']})

    elif params.get('ccd'):
        sql += ' WHERE ccd = ? ORDER BY RANDOM() LIMIT 1'
        # res = dbh.execute(text(sql), {"ccd": params['ccd']})
        params_dict.update({"ccd": params['ccd']})

    elif params.get('problem'):
        problem = config['problem_code'][params['problem']]
        sql += ' JOIN qa ON (files.fileid = qa.fileid) WHERE qa.problem = :problem'
        params_dict.update({"problem": problem})

        if params.get('detail'):
            sql += " AND detail = :detail"
            params_dict.update({"detail": params["detail"]})

        sql += ' ORDER BY RANDOM() LIMIT 1'

    else:
        logger.warn("In confusing block of getNextImage()")
        # ADW: I think this block is randomizing with a higher weight
        # given to images that have been viewed before.
        
        # ADW: This allows an empty where statement
        priority = "1" 

        # to create redundancy: draw every n-th image from list with existing qa
        #nth = 2
        #if random.randint(0, nth) < 1:
        #    fallback = sql
        #    sql += ' JOIN qa ON (files.fileid = qa.fileid)'
        #    if uid:
        #        sql += f' WHERE {priority} AND qa.userid != {uid}'
        #        sql += ' GROUP BY qa.fileid ORDER BY RANDOM() LIMIT 1'
        #        res = dbh.execute(sql)
        #        row = res.fetchone()
        #        if row:
        #            return dict(row)
        #    sql = fallback

        sql += f" WHERE {priority} ORDER BY RANDOM() LIMIT 1"

    logger.info(f"getNextImage sending SQL: {sql}; with params {params_dict}")
    with engine.connect() as connection:
        res = connection.execute(text(sql), params_dict)

    row = res.fetchone()

    return row._asdict() if row else None

def getProblems(engine: Engine, fileid: int, qa_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get the problems associated with the given file ID."""
    sql = 'SELECT problem, x, y, detail FROM qa WHERE fileid = :fileid'
    if qa_id is not None:
        sql += ' AND qaid = :qaid'
    else:
        sql += ' AND problem != 0 AND problem <= 1000'

    with engine.connect() as connection:
        res = connection.execute(text(sql), {"fileid": fileid, "qaid": qa_id} if qa_id else {"fileid": fileid})


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

def username2uid(username: str) -> int:
    """ Hash username as integer. """
    uid = 0
    mult = 1
    for c in username.upper():
        uid += (ord(c) - 47) * mult
        mult *= 49
    return uid

def uid2username(uid):
    """ Reverse hash to convert integer to username. """
    arr = []
    while uid > 0:
        arr.append(uid % 49 + 47)
        uid = uid // 49
    return ''.join(chr(char) for char in arr).lower()

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

def getActivity(engine: Engine, uid: int, date: Optional[str] = None) -> Dict[str, int]:
    """Get the user's activity based on the number of files reviewed."""
    activity = {}
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    sql = f"SELECT COUNT(DISTINCT(fileid)) as activity FROM qa WHERE userid={uid} AND timestamp > '{date}'"

    with engine.connect() as connection:
        res = connection.execute(text(sql))

        row = res.fetchone()
        activity['today'] = row[0] if row else 0
        sql = f"SELECT total_files FROM submissions WHERE userid={uid}"

        res = connection.execute(text(sql))
        row = res.fetchone()

    activity['alltime'] = row[0] if row else 0
    return activity

def giveBonusPoints(engine: Engine, uid: int, points: int) -> None:
    """Give bonus points to the user."""
    with engine.connect() as connection:
        connection.execute(text("UPDATE submissions SET total_files = total_files + :points "
                                "WHERE userid = :userid"), {"points": points, "uid": uid})

def filenameToDataId(filename: str):
    basename = os.path.basename(filename)
    junk, visit, band, det = os.path.splitext(basename)[0].rsplit('_',3)
    dataId = dict(instrument='LSSTComCam', visit=int(visit), detector=int(det))
    return dataId

def dataIdToFilename(dataId: Dict):
    filename = f"{dataId['instrument'].lower()}_{dataId['visit']}_{dataId['band']}_{dataId['detector']:03d}.fits"
    return filename
    
def exp_checker_logger() -> Any:
    logger = get_logger()
    return logger
