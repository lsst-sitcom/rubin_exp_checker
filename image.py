#!/usr/bin/env python
"""
Returns the path to the file or the file content as a StreamingResponse
"""
import os
from os.path import basename
from typing import Dict, List, Optional, Tuple
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import text

from .config import config
from .common import setRelease, getDBHandle
from .common import exp_checker_logger

logger = exp_checker_logger()

setRelease()

def download_file(file_path: str, revalidate: bool = False) -> StreamingResponse:
    """Downloads a file to the user's browser.

    Args:
        file_path (str): The file path to download.
        revalidate (bool, optional): Whether to set cache control headers for revalidation. Defaults to False.
    """
    logger.debug(f"download_file: {file_path}")
    # file = include path
    headers = {'Content-Description': 'File Transfer',
               'Content-Type': 'application/octet-stream',
               'Content-Transfer-Encoding': 'binary'}
    if (revalidate):
        headers['Expires'] =  "0"
        headers['Cache-Control'] = 'must-revalidate, post-check=0, pre-check=0'
        headers['Pragma'] = 'public'
    else:
        headers['Date'] = 'Fri, 05 Nov 2024 00:00:00 GMT';
        headers['Cache-Control'] = 'max-age=31556926'

    def iterfile():
        with open(file_path, mode="rb") as f:
            yield from f

    return StreamingResponse(iterfile(), headers=headers)

def main(params: Dict):
    logger.debug(f"{basename(__file__)}.main: {params}")
    dbh = getDBHandle()

    if (params.get('type') == "fov"):
        # Download the FoV image
        path = config['fovpath'][config['release']].replace("%e", params['expname'])
        file_path = os.path.join(config['base_dir'], path)
        if not os.path.exists(file_path):
            file_path = "assets/fov_not_available.png"
        logger.debug(f"file_path (type={params['type']}): {file_path}")
        return download_file(file_path);

    elif (params.get('type') == "dm"):
        # Provide path/code to access file
        expname =params['expname']
        ccd = params['ccd']
        sql = f"SELECT name FROM files WHERE expname = '{expname}' and ccd = '{ccd}'"
        res = dbh.execute(sql)
        row = res.fetchone()

        # This builds the URL to automatically download the file
        #file_path = 'https://'+config['domain']+'/get_image?release='+config['release']+'name='+row['name'];
        # This provides the url to the file
        file_path = 'https://'+config['domain']+config['fitspath'][config['release']]+row['name']
        logger.debug(f"file_path (type={params['type']}): {file_path}")
        return file_path

    else:
        # Download the image file
        path = config['fitspath'][config['release']]
        file_path = os.path.join(config['base_dir'], path, params['name'])
        logger.debug(f"file_path (type={params['type']}): {file_path}")
        return download_file(file_path, True)

if __name__ == '__main__':
    # Testing...
    # This downloads the file
    params = {'release': 'r2.1i', 'name': 'calexp-v00006854/R21/S02_B.fits'}

    # This gets the file path
    params = {'release': 'r2.1i', 'type': 'dm', 'expname': 'calexp-v00006854', 'ccd':'21-02-B'}
    # This is the path that should be returned:
    # exclusive/output-2.1i-20190119/binned_sensor/calexp-v00006854/R21/S02_B.fits

    # This gets a FoV image
    params = {'release': 'r2.1i', 'type': 'fov', 'expname': 'calexp-v00006854'}

    print(main(params))
