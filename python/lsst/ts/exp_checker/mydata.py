import json

from .common import userClass, missingFilesForNextClass
from .common import username2uid, uid2username, getDBHandle
from .common import exp_checker_logger

logger = exp_checker_logger()

from sqlalchemy import text

# Function to get user data
def getMyData(engine, uid):
    sql = f"""
        SELECT
            COALESCE(SUM(total_files), 0) AS total_files,
            COALESCE(SUM(flagged_files), 0) AS flagged_files,
            (SELECT COUNT(*) + 1 
             FROM submissions 
             WHERE total_files > (SELECT COALESCE((SELECT total_files FROM submissions WHERE userid = {uid}), 0))) AS rank
        FROM submissions
        WHERE userid = {uid}
    """
    with engine.connect() as connection:
        res = connection.execute(text(sql))
        row = res.fetchone()

    username = uid2username(uid)

    if row:
        row = row._asdict()
        row['total_files'] = int(row['total_files'])
        row['flagged_files'] = int(row['flagged_files'])
        row['rank'] = int(row['rank'])
        row['userclass'] = userClass(row['total_files'])
        row['missingfiles'] = missingFilesForNextClass(row['total_files'], row['userclass'])
        row['username'] = username
        return row
    else:
        return False

# Function to get other problems
def getMyOtherProblems(engine, uid):
    sql = f"""
        SELECT DISTINCT detail
        FROM qa
        WHERE userid = {uid} AND (problem = 255 OR problem = 1006) AND detail IS NOT NULL
    """
    with engine.connect() as connection:
        res = connection.execute(text(sql))

    return [row[0] for row in res.fetchall()]

# Main function
def main(username):
    """ Get user data.

    Parameters
    ----------
    username : the username

    Returns
    -------
    result : the result
    """
    engine = getDBHandle()
    uid = username2uid(username)
    if uid:
        result = getMyData(engine, uid)
        if result:
            result['problems'] = getMyOtherProblems(engine, uid)
            return result
        else:
             return "Error: Failed to retrieve user data"
    else:
        return "Error: Failed to get user ID"

