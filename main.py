# this directory will be overwritten by the actual exp-checker app:
# https://github.com/lsst-sitcom/rubin_exp_checker
import os, json, enum
from typing import Annotated, Dict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi import Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
from pydantic import BaseModel

#from sqlmodel import Field, Session, SQLModel, create_engine

from .common import exp_checker_logger
from .config import config
from . import api, gallery, image, mydata, problems, ranking, stats, submit

BASE_DIR = config['base_dir']
TEMPLATES_DIR = BASE_DIR / "templates"
#STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"

logger = exp_checker_logger()

# Create the app
app = FastAPI()

# Redirect to index
@app.get("/")
def redirect_to_index():
    return RedirectResponse(url="./index.html")

@app.get("/api")
def get_problems(release: str,
                 problem: str,
                 short: bool | str = None,
) -> Response:
    # bool | str allows query parameter to be used with no value
    params = {"release": release,
              "problem": problem,
              "short": short != False}
    response = api.main(params)
    return Response(json.dumps(response))

# Return the authorization
@app.get("/auth")
def get_auth() -> str:
    # This should be replaced by project authorization routine
    response = {"auth": True, "username": "kadrlica"}
    #response = {"auth": False}
    return json.dumps(response)

@app.get("/contact")
def get_contact() -> str:
    # Provide contact information
    #response = 'mailto:' + config['adminemail']
    response = config['contact']
    return response

@app.get("/download_file")
def download_file(filename: str) -> StreamingResponse:
    path = config['fitspath'][config['release']]
    filepath = os.path.join(path,filename)
    return getImage.download_file(filepath, True)

@app.get("/gallery")
def get_gallery() -> Response:
    """Query database for gallery of problems."""
    response = gallery.main()
    return Response(json.dumps(response))

@app.get("/headers")
def read_headers(req: Request) -> Dict:
    """Return the json-formatted dict of headers"""
    return req.headers

@app.get("/get_image")
async def get_image(release: str,
                    name: str | None = None,
                    expname: str | None = None,
                    ccd: str | None = None,
                    type: str | None = None
) -> Response:
    params = {'release': release, 'name': name,
              'expname': expname, 'ccd': ccd,
              'type': type}
    response = image.main(params)
    return response

@app.get("/mydata")
def get_mydata(release: str) -> Response:
    """Query database for user data."""
    data = mydata.main()
    return Response(json.dumps(data))


@app.get("/problems")
def get_problems(release: str,
                 fileid: int | None = None,
                 output: str | None = None,
                 problem: str | None = None,
                 my_problems: bool | str = False
) -> Response:
    """Query database for problems associated with an image."""
    # bool | str allows query parameter to be used with no value
    params = {"release": release,
              "fileid" : fileid,
              "output": output,
              "problem": problem,
              "my_problems": my_problems != False}

    response = problems.main(params)
    return Response(json.dumps(response))

@app.get("/ranking")
def get_ranking(limit: int = 15) -> Response:
    """Query database for ranking information."""
    rank = ranking.main(limit)
    return Response(json.dumps(rank))

@app.get("/stats")
def get_stats(release: str,
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

class Item(BaseModel):
    fileid: int | None = None
    expname: str | None = None
    ccd: str | None = None
    problem: str | None = None
    problems: list | None = None
    detail: str | None = None
    show_marks: bool | str = False
    qa_id: int | None = None
    release: str | None = None

@app.post("/submit")
async def post_submit(item: Item) -> Response:
    if item.show_marks == '': item.show_marks = True
    params = item.model_dump(exclude_none=True)
    logger.debug(f'submit: {params}')
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
        return templates.TemplateResponse(f"{page_name}.html",
                                          context = {
                                              "request": request,
                                              "repo": config['repo'],
                                          })
    else:
        # If not allowed, raise a 404 Not Found error
        raise HTTPException(status_code=404, detail="Page not found")

# Mount static files and assets
# https://stackoverflow.com/questions/65916537/a-minimal-fastapi-example-loading-index-html
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/material", StaticFiles(directory=BASE_DIR / 'material'), name="material")

# For testing, mount everything in main directory
#app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")
