# this directory will be overwritten by the actual exp-checker app:
# https://github.com/lsst-sitcom/rubin_exp_checker
import asyncio
import os, json, enum, copy
from contextlib import asynccontextmanager
from typing import Annotated, Dict, Optional, Any
from typing import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, APIRouter, HTTPException, status
from fastapi import Request, Response, Header, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
from pydantic import BaseModel, Field, model_validator
import uvicorn

#from sqlmodel import Field, Session, SQLModel, create_engine
from . import __version__
from . import api, gallery, image, mydata, problems, ranking, stats, submit
from .common import exp_checker_logger, username2uid
from .config import config

BASE_DIR = config['base_dir']
TEMPLATES_DIR = BASE_DIR / "templates"
#STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"

logger = exp_checker_logger()

async def get_user(
        x_auth_request_user: Annotated[str | None, Header()] = None
) -> Dict:
    """ Get the authenticated username from header. 

    Parameters
    ----------
    x_auth_request_user : the authenticated username

    Returns
    -------
    response : Dict containing username and uid
    """

    # For testing
    if not x_auth_request_user:
        x_auth_request_user = "testuser"
        
    if not x_auth_request_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication header 'X-Auth-Request-User'"
        )

    if not x_auth_request_user.isalnum():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication username is not alphanumeric"
        )
    
    username = x_auth_request_user
    uid = username2uid(username)
    response = {'username': username, 'uid': uid}
    return response

def set_release(release: str | None = None):
    """ Set the release. This updates the value of the global config['release'].

    Parameters
    ----------
    release : the release to be set

    Returns
    -------
    release : the release that was set
    """

    # TODO: Why would one want to change the config object? Disabled for now,
    # remove if unnecessary
    return config['release']


class ImageParams(BaseModel):
    """Parameters for specifying an image."""
    fileid: int | None = None
    expname: str | None = Field(alias='visit', default=None)
    ccd: str | None = Field(alias='detector', default=None)
    name: str | None = Field(alias='filename', default=None)

    class Config:
        # This allows both field and alias to be valid
        populate_by_name = True
        # This setting prevents extra fields
        extra = 'forbid'

        
class SubmitBody(BaseModel):
    """Allowed exposure checker submission parameters."""
    fileid: int | None = None
    expname: str | None = Field(alias='visit', default=None)
    ccd: str | None = Field(alias='detector', default=None)
    problem: str | None = None
    problems: list | None = None
    detail: str | None = None
    show_marks: bool | str = False
    qa_id: int | None = None
    release: str | None = Depends(set_release)

    class Config:
        # This setting prevents extra fields
        extra = 'forbid'
        # This allows both field and alias to be valid
        populate_by_name = True

def create_butler(repo, collection):
    """ Create the LSST Butler. 

    Parameters
    ----------
    repo : butler repository
    collection : butler collection

    Returns
    -------
    butler : the instantiated butler
    """
    logger.info(f"Creating LSST Butler...")
    logger.debug(f"  repo: {repo}")
    logger.debug(f"  collection: {collection}")
    try:
        from lsst.daf.butler import Butler
        return Butler(repo, collections=collection)
    except ImportError as e:
        logger.warn(str(e))
        return None

def create_client(profile_name, endpoint_url):
    """ Create the S3 client. """
    logger.debug(f"Creating S3 client...")
    import boto3
    session = boto3.Session(region_name="us-east-1", profile_name=profile_name)
    try:
        client = session.client("s3", endpoint_url=endpoint_url)
        client._bucket_name = profile_name
    except KeyError:
        raise HTTPException(404, "Location not found")

    return client

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:

    if config["transfer_type"] == 'butler':
        butler = create_butler(config['butler_repo'],config['butler_collection'])
        app.state.butler = butler
    else:
        app.state.butler = None

    if config["s3_profile_name"]:
        client = create_client(config['s3_profile_name'], config['s3_endpoint_url'])
        app.state.s3_client = client
    else:
        app.state.s3_client = None

    yield

# Create the app
logger.debug(f"exp_checker: v{__version__}")
app = FastAPI(
    version=__version__,
    debug=True,
    lifespan=lifespan,
)

# Redirect to index 
@app.get("/")
async def redirect_to_index():
    return RedirectResponse(url="./index.html")

@app.get("/api")
async def get_api_problems(
        problem: str,
        release: str = Depends(set_release),
        short: bool | str = False,
) -> Response:
    # bool | str allows query parameter to be used with no value
    params = {"release": release,
              "problem": problem,
              "short": short != False}
    response = api.main(params)
    return JSONResponse(response)

@app.get("/auth")
async def get_auth(user: str = Depends(get_user)):
    """ Get the authentication and username. """
    # This should be replaced by project authorization routine
    response: Dict[str, Any] = {"auth": True, "user": user}
    return JSONResponse(content=response)

@app.get("/contact")
async def get_contact() -> str:
    # Provide contact information
    #response = 'mailto:' + config['adminemail']
    response = config['contact']
    return response

@app.get("/gallery")
async def get_gallery(
        release: str = Depends(set_release),
) -> Response:
    """Query database for gallery of problems."""
    response = gallery.main()
    return Response(json.dumps(response))

@app.get("/get_image")
async def get_image(
        request: Request,
        release: str = Depends(set_release),
        visit: str | None = None,
        detector: str | None = None,
        name: str | None = None, 
        type: str | None = None,
) -> Response:
    params = {'release': release, 'name': name,
              'expname': visit, 'ccd': detector,
              'visit': visit, 'detector': detector,
              'type': type}
    logger.debug(f"get_image.params: {params}")

    if params['type'] is None:
        params['type'] = config.get('transfer_type')
        logger.debug(f"Set image access type: {params['type']}")

    response = await image.main(params, request)
    return response

@app.get("/headers")
async def read_headers(request: Request) -> Dict:
    """Return the json-formatted dict of headers"""
    return dict(request.headers)

@app.get("/mydata")
async def get_mydata(
        release: str = Depends(set_release),
        user: Dict = Depends(get_user),
) -> Response:
    """Query database for user data."""
    data = mydata.main(user["username"])
    return Response(json.dumps(data))

@app.get("/problems")
async def get_problems(
        release: str = Depends(set_release),
        fileid: int | None = None,
        output: str | None = None,
        problem: str | None = None,
        my_problems: bool | str = False,
        user: Dict = Depends(get_user),
) -> Response:
    """Query database for problems associated with an image."""
    # bool | str allows query parameter to be used with no value
    params = {"release": release,
              "fileid" : fileid,
              "output": output,
              "problem": problem,
              "my_problems": my_problems != False,
    }
    params.update(user)

    response = problems.main(params)
    return Response(json.dumps(response))

@app.get("/ranking")
async def get_ranking(
        release: str = Depends(set_release),
        limit: int = 15
) -> Response:
    """Query database for ranking information."""
    rank = ranking.main(limit)
    return Response(json.dumps(rank))

@app.get("/stats")
async def get_stats(
        release: str = Depends(set_release),
        total: bool | str = False,
        today: bool | str = False,
        breakup: bool | str = False,
        throughput: bool | str = False
) -> Response:
    """Query database for user stats."""
    # bool | str allows query parameter to be used with no value
    params = {"release": release,
              "total": total != False,
              "today": today != False,
              "breakup": breakup != False,
              "throughput": throughput != False}

    response = stats.main(params)
    return Response(json.dumps(response))

@app.post("/submit")
async def post_submit(
        body: SubmitBody,
        user: Dict = Depends(get_user),
) -> Response:
    #if item.show_marks == '': item.show_marks = True
    body.show_marks = body.show_marks != False
    params = body.model_dump(exclude_none=True)
    params.update(user)
    logger.debug(f'submit: {params}')
    set_release(params['release'])
    response = submit.main(params)
    return Response(response)

# Set template directory
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
# Define the set of allowed page names to prevent unauthorized access
ALLOWED_PAGES = {"index", "viewer", "tutorial", "faq", "statistics", "api",
                 "gallery", "hodgepodge", "heat_map"}

# Define a dynamic route that captures the page name from the URL
@app.get("/{page_name}.html", response_class=HTMLResponse)
async def render_page(request: Request, page_name: str):
    # Check if the requested page is in the list of allowed pages
    if page_name in ALLOWED_PAGES:
        # Render the template with the request context
        env = Environment(autoescape=True, auto_reload=True)
        context = {"request": request, "version": __version__}
        context.update(copy.deepcopy(config))
        return templates.TemplateResponse(f"{page_name}.html", context=context)
    else:
        # If not allowed, raise a 404 Not Found error
        raise HTTPException(status_code=404, detail="Page not found")

@app.get("/collections")
async def get_collections(request: Request) -> Response:
    """Return the json-formatted dict of headers"""
    butler = request.app.state.butler
    collections = [_ for _ in butler.registry.queryCollections('LSSTComCam/*')]
    return Response(json.dumps(collections))

    
# Mount static files and assets
# https://stackoverflow.com/questions/65916537/a-minimal-fastapi-example-loading-index-html
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/material", StaticFiles(directory=BASE_DIR / 'material'), name="material")

# For testing, mount everything in main directory
#app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    uvicorn.run("lsst.ts.exp_checker.main:app", host="0.0.0.0")
