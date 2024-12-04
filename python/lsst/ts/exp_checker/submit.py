from typing import Any, Dict, Optional, Tuple
import json
import sqlite3

from .common import getDBHandle, getActivity, userClass
from .common import username2uid, exp_checker_logger
from .common import getNextImage, getProblems, numberSuffix
from .config import config

logger = exp_checker_logger()

def submit_image(params: Dict, uid: int) -> None:
    """Submit image inspection to the database.

    Parameters
    ----------
    params [Dict]: image problem information
    uid [int]: user ID

    Returns
    -------
    None
    """
    dbh = getDBHandle()
    nflag = 0

    # Insert the problem details (note that "OK" and "Awesome!" included as problems)
    problems = params.get('problems')
    if problems:
        problem_codes = config['problem_code']
        for problem in problems:
            # Parse false positive problems from strings
            if problem['problem'][0] == "-":
                problem['problem'] = problem['problem'][1:]
                code = -problem_codes[problem['problem']]
            else:
                code = problem_codes[problem['problem']]

            # "Awesome!" marks shouldn't be flagged as problems
            if code not in [problem_codes['Awesome!']]:
                nflag += 1

            problem['x'] = int(problem['x'])
            problem['y'] = int(problem['y'])
            if problem['detail'] == '':
                problem['detail'] = None

            dbh.execute('INSERT INTO qa (fileid, userid, problem, x, y, detail) VALUES (?, ?, ?, ?, ?, ?)',
                (params['fileid'], uid, code, problem['x'], problem['y'], problem['detail']))

    if nflag > 0:
        # Increment the summary table
        cursor = dbh.execute(
            'UPDATE submissions SET total_files = total_files + 1, flagged_files = flagged_files + 1 WHERE userid = ?',
            (uid,))
        if cursor.rowcount == 0:
            dbh.execute('INSERT INTO submissions VALUES (?, 1, 1)', (uid,))
    else:
        # Insert qa for exposures with no flagged problems (i.e., "OK")
        dbh.execute(
            'INSERT INTO qa (fileid, userid, problem, x, y, detail) VALUES (?, ?, ?, ?, ?, ?)',
            (params['fileid'], uid, 0, None, None, None))
        # Increment the summary table
        cursor = dbh.execute(
            'UPDATE submissions SET total_files = total_files + 1 WHERE userid = ?',
            (uid,))
        if cursor.rowcount == 0:
            dbh.execute('INSERT INTO submissions VALUES (?, 1, 0)', (uid,))

    try:
        dbh.commit()
    except sqlite3.Error as e:
        dbh.rollback()
    dbh.close()

def get_congrats(uid: int) -> Dict:
    """Get congratulations message for completion.

    Parameters
    ----------
    uid [int] : user id

    Returns
    -------
    congrats [dict] : dictionary
    """
    dbh = getDBHandle()
    activity = getActivity(dbh, uid)
    old_user_class = userClass(activity['alltime'] - 1)
    user_class = userClass(activity['alltime'])
    congrats = None
    if user_class > old_user_class:
        congrats: Dict[str, Any] = {
            'text': "You have just finished your ",
            'detail': "To reflect your achievements, we've upgraded you to <span id='status_class' class='badge'></span> status.",
            'userclass': user_class
        }
        if user_class == 1:
            congrats['text'] += "<strong>first 10 images</strong>!"
        elif user_class == 2:
            congrats['text'] += "<strong>first 100 images</strong>!"
        else:
            fps = activity['alltime'] // config['images_per_fp']
            congrats['text'] += f"<strong>{numberSuffix(fps)} focal plane</strong>!"
    elif activity['alltime'] % config['images_per_fp'] == 0:
        fps = activity['alltime'] // config['images_per_fp']
        congrats = {
            'text': f"You have just finished your <strong>{numberSuffix(fps)} focal plane</strong>!"
        }

    return congrats

def get_next_image(params: Dict, uid: int) -> Dict:
    """Get the row containing information about the next image.

    Parameters
    ----------
    params [Dict]: image problem information
    uid [int]: user ID

    Returns
    -------
    row [dict]: information about the next image
    """
    dbh = getDBHandle()
    row = getNextImage(dbh, params, uid)
    if row:
        row['uid'] = uid
        row['name'] = f"get_image?release={config['release']}&name={row['name']}"
        if params.get('show_marks') or params.get('qa_id'):
            row['marks'] = getProblems(dbh, row['fileid'], params.get('qa_id'))
    else:
        row = {
            'error': "File missing",
            'message': "The requested image cannot be retrieved.",
            'description': "Either we don't have the band or the file is not part of the requested release."
        }
    return row

def main(params: Dict) -> None:
    logger.debug(f"submit.main: {params}")
    dbh = getDBHandle()
    uid = params['uid']

    congrats = None
    if uid and (params.get('fileid') is not None):
        submit_image(params, uid)
        congrats = get_congrats(uid)

    row = get_next_image(params, uid)

    if congrats:
        row['congrats'] = congrats

    return json.dumps(row)

if __name__ == "__main__":
    params = {}
    res = main(params)
    print(res)
