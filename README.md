# Exposure Checker

This project provides a web-app for crowdsourced image quality control for LSST DESC. The app loads and displays FITS images directly in the browser and works on desktop and mobile devices. Users are asked to identify features in survey images, which are recorded and tracked. The LSST implementation is based off of the [DES exposure checker](https://github.com/pmelchior/des-exp-checker). More details can be found in [Melchior et al., Astron.Comput., 16, 99 (2016)](http://adsabs.harvard.edu/abs/2016A%26C....16...99M).

The license is MIT. Feel free to use and modify, but please cite our paper if you do.

## Setup

The app runs on the fastapi webserver using javascript and jinja2.

1. Install a conda or virtual environment:

```bash
mamba create -n exp_checker nodejs python setuptools uvicorn sqlmodel
conda activate exp_checker
```

2. Install `npm` javascript package manager

```bash
npm install
npm audit fix # (if necessary)
npm run build
```

3. Copy your aws credentials into:

```bash
cp credentials ~/.aws/credentials
chmod og-rx ~/.aws/credentials
```

## Installation

1. Clone the repository and install with `pip`:

```
git clone git@github.com:lsst-ts/exp_checker.git
cd exp_checker
pip install -e .
pip install -r requirements.txt
```

2. Create an empty database file `files.db`:

```bash
sqlite3 files.db < sql/files.sql
```

   Move the db file into a directory that the webserver can access but that is hidden from direct access. Because of `.htaccess`, files and directories that start with a `.` are inaccessible when requested through the webserver, so you do:

````bash
mkdir .db
mv files.db .db/
````
   
3. Load information about the test images into the file database. As you can see from the schema in `sql/files.sql`,  each image requires 4 pieces of information:

```sql
expname TEXT,
ccd TEXT,
band TEXT,
name TEXT
```

   `ccd` and `band` should be obvious, `expname` is the short but unique name of the exposure, and `name` (as a bit of a misnomer) is actually the filename of the FITS file in question. No full paths are needed, you'll set them in  `$config['fitspath']` next.

4. Rename `config.py.template` to `config.py` and edit as necessary. 
5. Add the new release to `templates/release_selector.shtml`.
6. On a production environment: Remove `.git` and `README.md`.
7. Run `fix_permissions.sh` to update file permission:

   ```bash
   ./fix_permissions.sh
   ```
   
## Configuration

The `config.py` file contains almost all of the particular configuration for the server and the location of files. Its content is:

```python
config = {
    "base_dir": Path(__file__).resolve().parent, # parent directory
    "domain": "<DOMAIN>",                # webserver url
    "repo": "<URL>",                     # github repository
    "slack_channel" : "<CHANNEL>",       # slack channel name for communication
    "slack_link" : "<URL>",              # slack channel link for communication
    "contact": "<INFO>",                 # contact information
    "releases": ["r2.1i"],               # list of releases
    "release": None,                     # active release (empty, set by app)
    "filedb": {"r2.1i": "<FILE PATH>"},  # release: path to database file
    "fitspath": {"r2.1i": "<DIR PATH>"}, # release: directory with FITS images
    "fovpath": {"r2.1i": "<DIR PATH>"},  # release: directory with FoV images
    "images_per_fp": 378,                # number of images in FoV (used for congrats)
    "problem_code": Dict[str, int]       # problem label: integer code
}
```

### Releases

The code has a mechanism to switch between data releases. For that define a list of releases, e.g.,

```python
"releases": ["SVA1", "Y1A1"]
```

 Set the values for `filedb`, `fovpath`, `fitspath` with one key-value pair for each release, e.g.,

```python
"filedb": {"SVA1": ".db/files.sva1.db",
           "Y1A1": ".db/files.y1a1.db"}
```

Currently the releases also need to be set by hand in the `templates/release_selector.shtml` file (this behavior be updated in the future). The name of each release must be the content of HTML node of `class="release-button"` like

```html
<a class="release-button" href="#">SVA1</a>
```

### Problem classes

Problem classes are defined in two different locations: As textual labels for frontend users and as numbers for the server (the reduce overhead and storage requirements in the file databases).

1. Open `templates/problem_selector.shtml` and modify as needed. For a label to be working as intended, it needs to be the content of an HTML node of `class="problem"`, e.g.

 ```html
<a class="problem" href="#">Column mask</a>
```

2. Open `config.py` and make sure each problem label has a numeric code in `config['problem_code']`, e.g.

```python
config['problem_code'] = {
    "OK": 0,          # DO NOT CHANGE!
    "Other...": 999,  # DO NOT CHANGE!
    "Awesome!": 1000, # DO NOT CHANGE!
    "Column mask": 1, # Example problem type
    ...
```

## API

In addition to the frontend statistics pages, user generated reports can be queried with an API. The path is

```
api?release=SVA1&problem=Column%20mask
```

The parameter `release` needs to be from `config['releases']` and problem needs to be a key in `config['problem_codes']`. If necessary, both need to be url encoded.

The API returns JSON of the following form:

```json
[
  {"qa_id": number,
  "expname": string,
  "ccd": number,
  "band": string,
  "problem": string,
  "x": number,
  "y": number,
  "detail": null or string,
  "false_positive": true or false,
  "release": string
  }
]
```

The list has one of dictionary per reported problem that matches the request. `qa_id` is a unique identifier of the report in the given `release`, `x/y` are the CCD coordinates of the center of the problem marker, `detail` (only set for labels "Other…" and "Awesome!") is a user-generated text to describe the report.
