#!/usr/bin/env python
"""
Returns the path to the file or the file content as a StreamingResponse
"""
import os
from os.path import basename
from io import BytesIO, StringIO, FileIO
import json

from typing import Dict, List, Optional, Tuple
from fastapi import Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.exceptions import HTTPException

from botocore.exceptions import ClientError
from botocore.response import StreamingBody

from .config import config
from .common import getDBHandle
from .common import exp_checker_logger

logger = exp_checker_logger()

def create_headers(revalidate: bool = False):
    """Create headers for streaming file."""

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
    return headers

def stream_response(stream, chunk_size: int = 1024, revalidate: bool = False) -> StreamingResponse:
    """ Stream content. """

    def iostream_generator(stream, chunk_size: int = 1024):
        """Generator to stream data from an IOStream in chunks."""
        stream.seek(0)  # Ensure stream is at the beginning

        while True:
            # Read chunk_size bytes from the stream
            chunk = stream.read(chunk_size)
            
            # Break if no more data
            if not chunk:
                break
            
            yield chunk

    headers = create_headers(revalidate)
    return StreamingResponse(iostream_generator(stream, chunk_size), headers=headers)
    
def download_file(file_path: str, revalidate: bool = False) -> StreamingResponse:
    """Downloads a file from disk to the user's browser.

    Parameters
    ----------
    file_path (str): The file path to download.
    revalidate (bool, optional): Whether to set cache control headers for revalidation. Defaults to False.

    Returns
    -------
    resp : StreamingResponse
    """
    logger.debug(f"download_file: {file_path}")
    # file = include path
    headers = create_headers(revalidate)

    def iterfile():
        with open(file_path, mode="rb") as f:
            yield from f

    return StreamingResponse(iterfile(), headers=headers)

def get_content_from_file(file_path: str):
    """ Access a file using the butler and stream to user's browser.

    Parameters
    ----------
    file_path : path to the file

    Returns
    -------
    stream : FileIO stream
    """
    logger.debug("Getting image content from file...")
    stream = FileIO(file_path, mode="r")
    return stream
    
def get_content_from_butler(butler, dataId: Dict):
    """ Access a file using the butler and stream to user's browser.

    Parameters
    ----------
    butler (lsst.daf.butler.Butler) : to access data
    dataId (dict) : value pairs that label the DatasetRef within a Collection.

    Returns
    -------
    stream : BytesIO stream
    """
    logger.debug("Getting image content from butler...")
    # Create the memory object
    from lsst.afw.fits import MemFileManager
    manager = MemFileManager()

    # Get the file and write to memory
    datasetType = 'calexpBinned'
    exposure = butler.get(datasetType, dataId=dataId)

    # Compress the file
    opts = dict()
    if config.get('compress_images', True): 
        from lsst.afw.fits import ImageCompressionOptions, ImageWriteOptions, ImageScalingOptions
        logger.debug("Compressing image")
        quantize = 10.0
        compression = ImageCompressionOptions(ImageCompressionOptions.RICE, True, 0.0)
        scaling = ImageScalingOptions(ImageScalingOptions.STDEV_BOTH, 32, quantizeLevel=quantize)
        opts['imageOptions'] = ImageWriteOptions(compression, scaling)
        opts['maskOptions'] = ImageWriteOptions(compression)
        opts['varianceOptions'] = opts['imageOptions']

    exposure.writeFits(manager, **opts)

    # Convert to IO stream
    stream = BytesIO(manager.getData())
    return stream

def get_content_from_websocket(dataId: Dict):
    """ Access a file from a worker pod using a websocket.

    Parameters
    ----------
    dataId (dict) : value pairs that label the DatasetRef within a Collection.

    Returns
    -------
    stream : BytesIO stream
    """
    logger.debug("Getting image content from websocket...")
    import websocket
    import base64
    
    datasetType = 'calexpBinned'
    #dataId = {"instrument": "LSSTComCam", "detector": 3, "visit": 2024110900185}
    
    command = {
        "name": "get fits image",
        "parameters": {
            "repo": config['butler_repo'],
            "collection": config['butler_collection'],
            "image_name": datasetType,
            "data_id": dataId,
            "compress": config.get('compress_images', True),
        }
    }

    # Create the websocket
    ws = websocket.WebSocket()
    ws.connect(config['websocket_uri'])

    # Send and receive a message
    ws.send(json.dumps(command))
    response = ws.recv()

    # Close the socket
    ws.close()
    
    # Convert the response to IO stream
    response = json.loads(response)
    stream = BytesIO(base64.b64decode(response['content']['fits']))
    return stream

def get_fov_image(params: Dict, client):
    """ Get FoV mosaic from RubinTV S3 bucket.

    Parameters
    ----------
    params: parameter dict

    Returns
    -------
    response : streaming response for the file
    """
    # Build the S3 key
    # Example:
    #comcam/2024-11-19/calexp_mosaic/000040/comcam_calexp_mosaic_2024-11-19_000040.jpg
    camera_name = 'comcam'
    channel_name = 'calexp_mosaic'
    visit = str(params['expname'])
    day_obs = int(visit[0:8])
    seq_num = int(visit[8:])
    date_str = f"{visit[0:4]}-{visit[4:6]}-{visit[6:8]}"
    seq_str = f"{seq_num:06d}"
    filename = f"{camera_name}_{channel_name}_{date_str}_{seq_str}.jpg"
    key = f"{camera_name}/{date_str}/{channel_name}/{seq_str}/{filename}"

    # Get the file from S3
    try:
        obj = client.get_object(Bucket=client._bucket_name, Key=key)
        data_stream = obj["Body"]
        assert isinstance(data_stream, StreamingBody)
    except ClientError:
        raise HTTPException(status_code=404, detail=f"No such file for: {key}")

    return StreamingResponse(content=data_stream.iter_chunks())

def main(params: Dict, request: Request):
    logger.debug(f"image.main: {params}")
    
    if (params.get('type') == "fov_old"):
        # Download the FoV image
        #path = config['fovpath'][config['release']].replace("%e", params['expname'])
        path = config['fovpath'][config['release']].format(**params)
        file_path = os.path.join(config['base_dir'], path)
        logger.debug(f"file_path (type={params['type']}): {file_path}")
        if not os.path.exists(file_path):
            logger.warn("FoV file not found.")
            file_path = f"{config['base_dir']}/assets/fov_not_available.png"
        return download_file(file_path)

    if (params.get('type') == "fov"):
        # Download the FoV image
        logger.debug(f"fov (type={params['type']}): {params}")
        if params.get('expname') in (None, 'null'):
            logger.warn("FoV file not found.")
            file_path = f"{config['base_dir']}/assets/fov_not_available.png"
            return download_file(file_path)

        s3_client = request.app.state.s3_client
        return get_fov_image(params, s3_client)

    elif (params.get('type') == "dm"):
        # Provide path/code to access file
        dbh = getDBHandle()
        expname = params['expname']
        ccd = params['ccd']
        sql = f"SELECT name FROM files WHERE expname = '{expname}' and ccd = '{ccd}'"
        res = dbh.execute(sql)
        row = res.fetchone()
        dbh.close()
        
        # This builds the URL to automatically download the file
        #file_path = 'https://'+config['domain']+'/get_image?release='+config['release']+'name='+row['name'];
        # This provides the url to the file
        file_path = 'https://'+config['domain']+config['fitspath'][config['release']]+row['name']
        logger.debug(f"file_path (type={params['type']}): {file_path}")
        return file_path

    elif (params.get('type') == "old_file"):
        # Old interface to download the image file from disk
        path = config['fitspath'][config['release']]
        file_path = os.path.join(config['base_dir'], path, params['name'])
        logger.debug(f"file_path (type={params['type']}): {file_path}")
        return download_file(file_path, True)

    elif (params.get('type') == "file"):
        # Get image file from disk
        path = config['fitspath'][config['release']]
        file_path = os.path.join(config['base_dir'], path, params['name'])
        logger.debug(f"file_path (type={params['type']}): {file_path}")
        stream = get_content_from_file(file_path)
        return stream_response(stream, 1024, True)
    
    elif (params.get('type') == "ws"):
        # Get image file from worker through websocket
        filename = os.path.basename(params['name'])
        junk, visit, band, det = os.path.splitext(filename)[0].rsplit('_',3)
        dataId = dict(instrument='LSSTComCam', visit=int(visit), detector=int(det))
        logger.debug(f"dataId: {dataId}")
        stream = get_content_from_websocket(dataId)
        return stream_response(stream, 1024, True)
    
    else:
        # Get image file from the butler
        filename = os.path.basename(params['name'])
        junk, visit, band, det = os.path.splitext(filename)[0].rsplit('_',3)
        dataId = dict(instrument='LSSTComCam', visit=int(visit), detector=int(det))
        logger.debug(f"dataId: {dataId}")
        butler = request.app.state.butler
        if butler is None:
            logger.warn("Butler not found.")
            return None
        else:
            stream = get_content_from_butler(butler, dataId)
            return stream_response(stream, 1024, True)

if __name__ == '__main__':
    ## Testing...
    ## This downloads the file
    #params = {'release': 'r2.1i', 'name': 'calexp-v00006854/R21/S02_B.fits'}
    # 
    ## This gets the file path
    #params = {'release': 'r2.1i', 'type': 'dm', 'expname': 'calexp-v00006854', 'ccd':'21-02-B'}
    ## This is the path that should be returned:
    ## exclusive/output-2.1i-20190119/binned_sensor/calexp-v00006854/R21/S02_B.fits
    # 
    ## This gets a FoV image
    #params = {'release': 'r2.1i', 'type': 'fov', 'expname': 'calexp-v00006854'}

    ## This gets a Butler image
    #params = {'release': 'r2.1i', 'type': 'butler', 'expname': 'calexp-v00006854'}

    #print(main(params))

    #from lsst.daf.butler import Butler
    #repo = config['butler_repo']
    #collection = config['butler_collection']
    #butler = Butler(repo,collections=collection)
    #dataId = dict(instrument='LSSTComCam', detector=3, visit=2024110900185)
    #print(dataId)
    #resp = butler_file(butler,  dataId)

    pass
