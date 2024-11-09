import sys
import json
from typing import Dict, List, Optional
import sqlite3

from .config import config
from .common import getDBHandle

def api_handler(problem: str, short: bool = False) -> List[Dict]:
    """Handle API requests for problem data.

    Args:
        problem: The problem identifier to query
        short: Whether to return shortened results
    
    Returns:
        Query results
    """
    if problem not in config['problem_code']:
        return "Problem unknown!"
    
    dbh = getDBHandle()
    code = config['problem_code'][problem]

    # Build the SQL query
    sql = "SELECT qa.qaid as qa_id, ccd, band, problem, x, y"
    if short:
        sql += ", detail"
    sql += " FROM qa JOIN files ON (files.fileid=qa.fileid)"
    sql += f" WHERE problem={code} OR problem=-{code}"
    sql += " ORDER BY expname, ccd ASC"

    res = dbh.execute(sql)

    # Convert to list of dictionaries
    results = []
    for row in res.fetchall():
        row_dict = dict(row)

        # Convert specific fields
        row_dict['qa_id'] = int(row_dict['qa_id'])
        row_dict['problem'] = int(row_dict['problem'])

        # good exposure don't have locations
        if row_dict['problem'] != 0:
            ### correct for downsampling of factor 4
            #row['x'] = int(row['x'])*4
            #row['y'] = int(row['y'])*4

            # return raw pixel value
            row_dict['x'] = int(row_dict['x'])
            row_dict['y'] = int(row_dict['y'])

        if short:
            row_dict.pop('problem', None)
        else:
            row_dict['false_positive'] = row_dict['problem'] < 0
            row_dict['problem'] = problem
            row_dict['release'] = config['release']

        results.append(row_dict)
    # Close the connection
    dbh.close()
    return results

def main(params: Dict):
    return api_handler(params['problem'], params.get('short', False))

if __name__ == "__main__":
    params = {"problem": "Cosmic ray"}
    results = main(params)
    print(json.dumps(results))
