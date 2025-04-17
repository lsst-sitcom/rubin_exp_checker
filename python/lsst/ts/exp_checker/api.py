import sys
import json
from typing import Dict, List, Optional

from sqlalchemy import text

from .config import config
from .common import getDBHandle, uid2username, exp_checker_logger

logger = exp_checker_logger()

def api_handler(problem: str, short: bool = False) -> List[Dict]:
    """Handle API requests for problem data.

    Args:
        problem: The problem identifier to query
        short: Whether to return shortened results
    
    Returns:
        Query results
    """
    if problem not in config['problem_code']:
        logger.warn(f"Problem code {problem} not configured")
        return []
    
    engine = getDBHandle()
    code = config['problem_code'][problem]

    # Build the SQL query
    sql = "SELECT qa.qaid as qa_id, userid as uid, expname as visit, ccd as detector, band, problem, x, y"
    if not short:
        sql += ", detail"
    sql += " FROM qa JOIN files ON (files.fileid=qa.fileid)"
    sql += f" WHERE problem={code} OR problem=-{code}"
    sql += " ORDER BY visit, detector ASC"

    with engine.connect() as connection:
        res = connection.execute(text(sql))

    # Convert to list of dictionaries
    results = []
    for row in res.fetchall():
        row_dict = row._asdict()

        # Convert specific fields
        row_dict['uid'] = int(row_dict['uid'])
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
            row_dict['username'] = uid2username(row_dict['uid'])
            
        results.append(row_dict)

    return results

def main(params: Dict):
    return api_handler(params['problem'], params.get('short', False))

