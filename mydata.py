import json

from .common import userClass, missingFilesForNextClass
from .common import username2uid, uid2username, getDBHandle
from .common import exp_checker_logger

logger = exp_checker_logger()

# Function to get user data
def getMyData(dbh, uid):
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
    res = dbh.execute(sql)
    row = res.fetchone()

    username = uid2username(uid)
    
    if row:
        row = dict(row)
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
def getMyOtherProblems(dbh, uid):
    sql = f"""
        SELECT DISTINCT detail
        FROM qa
        WHERE userid = {uid} AND (problem = 255 OR problem = 1006) AND detail IS NOT NULL
    """
    res = dbh.execute(sql)
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
    dbh = getDBHandle()
    uid = username2uid(username)
    if uid:
        result = getMyData(dbh, uid)
        if result:
            result['problems'] = getMyOtherProblems(dbh, uid)
            return result
        else:
             return "Error: Failed to retrieve user data"
    else:
        return "Error: Failed to get user ID"


if __name__ == "__main__":
    res = main(username='testuser')
    print(json.dumps(res))
