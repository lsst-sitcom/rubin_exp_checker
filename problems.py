import json
import sqlite3
from sqlite3 import Connection
from typing import Dict, List, Optional, Tuple

from .common import getDBHandle, getProblems, exp_checker_logger
from .config import config

logger = exp_checker_logger()

def getCountOfProblem(
        dbh: Connection,
        problem: str,
        uid: Optional[int] = None
) -> List[Dict]:
    """Retrieves the count of problems from the 'qa' table.

    Args:
        dbh (Connection): Database connection.
        problem (str): The problem to search for.
        uid (int, optional): The user ID to filter the results by.

    Returns:
        List[Dict]: A list of dictionaries containing the problem, detail, and count.
    """
    problems: List[Dict] = []
    if problem in config['problem_code']:
        code = config['problem_code'][problem]
        sql = "SELECT problem, detail, COUNT(DISTINCT(qa.fileid)) AS count FROM qa JOIN files ON (qa.fileid = files.fileid) WHERE problem = ?"
        if uid is not None:
            sql += f" AND userid = {uid}"
        if code == 255:
            sql += " AND detail IS NOT NULL GROUP BY detail ORDER BY `count` DESC, detail"

        res = dbh.execute(sql, (code,))
        for row in res.fetchall():
            problems.append({"problem": problem, "detail": row[1], "count": row[2]})

    return problems


def main(params: Dict) -> Dict:
    logger.info(f'problems.main: {params}')
    dbh = getDBHandle()
    if params.get("fileid"):
        problems = getProblems(dbh, params["fileid"])
    elif params.get("problem"):
        uid = params["uid"] if params.get("my_problems") else None
        problems = getCountOfProblem(dbh, params["problem"], uid)
    return problems

if __name__ == "__main__":
    params = {"problem": "Dark halo"}
    problems = [main({"problem": k}) for k in config['problem_code']]
    print(json.dumps(problems))

