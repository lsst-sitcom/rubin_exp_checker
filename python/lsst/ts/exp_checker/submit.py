from typing import Any, Dict, Optional, Tuple
import json

from .common import getDBHandle, getActivity, userClass
from .common import username2uid, exp_checker_logger
from .common import getNextImage, getProblems, numberSuffix
from .config import config

from sqlalchemy import text

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
    engine = getDBHandle()
    nflag = 0

    with engine.connect() as conn:
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

                conn.execute(text("INSERT INTO qa (fileid, userid, problem, x, y, detail) "
                                    "VALUES (:fileid, :userid, :problem, :x, :y, :detail)"),
                               {"fileid": params['fileid'],
                                "userid": uid, "problem": code, "x": problem['x'], "y": problem['y'],
                                "detail": problem['detail']})

        if nflag > 0:
            # Increment the summary table
            cursor = conn.execute(text(
                'UPDATE submissions SET total_files = total_files + 1, flagged_files = flagged_files + 1 WHERE userid = :userid'),
                                 {"userid": uid} )
            if cursor.rowcount == 0:
                conn.execute(text('INSERT INTO submissions VALUES (:userid, 1, 1)'), {"userid": uid})
        else:
            # Insert qa for exposures with no flagged problems (i.e., "OK")
            conn.execute(text( 'INSERT INTO qa (fileid, userid) VALUES (:fileid, :userid)'),
                           {"fileid": params['fileid'], "userid": uid})
            # Increment the summary table
            cursor = conn.execute(text(
                'UPDATE submissions SET total_files = total_files + 1 WHERE userid = :userid'),
                                    {"userid": uid})
            if cursor.rowcount == 0:
                conn.execute(text('INSERT INTO submissions VALUES (:userid, 1, 0)'), {"userid": uid})


def get_congrats(uid: int) -> Dict:
    """Get congratulations message for completion.

    Parameters
    ----------
    uid [int] : user id

    Returns
    -------
    congrats [dict] : dictionary
    """
    engine = getDBHandle()
    activity = getActivity(engine, uid)
    old_user_class = userClass(activity['alltime'] - 1)
    user_class = userClass(activity['alltime'])
    congrats: Dict[str, Any] = {}
    if user_class > old_user_class:
        congrats = {
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
    engine = getDBHandle()
    row = getNextImage(engine, params, uid)
    if row:
        row['uid'] = uid
        row['name'] = f"get_image?release={config['release']}&name={row['name']}"
        if params.get('show_marks') or params.get('qa_id'):
            row['marks'] = getProblems(engine, row['fileid'], params.get('qa_id'))
    else:
        row = {
            'error': "File missing",
            'message': "The requested image cannot be retrieved.",
            'description': "Either we don't have the band or the file is not part of the requested release."
        }
    return row

def main(params: Dict) -> str:
    logger.debug(f"submit.main: {params}")
    engine = getDBHandle()
    uid = params['uid']

    congrats = None
    if uid and (params.get('fileid') is not None):
        submit_image(params, uid)
        congrats = get_congrats(uid)

    row = get_next_image(params, uid)

    if congrats:
        row['congrats'] = congrats

    return json.dumps(row)
