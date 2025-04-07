from pathlib import Path
from typing import Dict

config: Dict[str, any] = {
    "base_dir": Path(__file__).resolve().parent,
    "butler_repo": "embargo", #"s3://embargo@rubin-summit-users/butler.yaml", 
    "butler_collection": "u/kadrlica/binCalexp4",
    "s3_profile_name": "",
    "s3_endpoint_url": "https://s3dfrgw.slac.stanford.edu",
    #"websocket_uri": "ws://localhost:9999/ws/client",
    "websocket_uri": "ws://rubintv:8080/rubintv/ws/ddv/client",
    "transfer_type": "ws",
    "compress_images": True,
    "repo": "https://github.com/lsst-sitcom/rubin_exp_checker",
    "slack_channel" : "#sciunit-image-inspection",
    "slack_link" : "https://rubin-obs.slack.com/archives/C07Q45NN0CX",
    "contact": "<URL>",
    "domain": "8000/rubintv/exp_checker/",
    "db_engine": "postgresql+psycopg2",
    "db_host": "db",
    "db_port": "5432",
    "db_username": "exp-checker",
    "db_password": "debug",
    "db_dbname": "exp-checker",
    "filedb": {
        #"ComCam": ".db/files.comcam-20241117.db",
        #"dev": ".db/LSSTComCam-dev.db",
        #"ComCam": ".db/LSSTComCam-20241128.db",
        "dev": ".db/files.comcam-20241109.db",
        "ComCam": ".db/files.comcam-20241117.db",
    },
    "fitspath": {
        "dev": "exclusive/comcam/calexp_binned/",
        "ComCam": "exclusive/comcam/calexp_binned/",
    },
    "fovpath": {
        "dev": "exclusive/comcam/calexp_mosaic/{expname:.8s}/comcam_calexp_mosaic_{expname}.jpg",
        "ComCam": "exclusive/comcam/calexp_mosaic/{expname:.8s}/comcam_calexp_mosaic_{expname}.jpg",
    },
    "releases": ["dev", "ComCam"],
    "release": None,
    "images_per_fp": 378,
    "problem_code": {
        "OK": 0,
        # Instrument & Telescope
        "Guiding": 11,
        "Shutter": 12,
        "Readout noise": 13,
        "Focus": 14,
        # Flat fielding
        "Amplifier jump": 21,
        "Fringing": 22,
        "Hardware Imprint": 23,
        "Tree rings": 24,
        "Coffee stains": 25,
        # Reflections
        "Stray light": 31,
        "Ghost": 32,
        "Ghoul": 33,
        "Glint": 34,
        # Tracks
        "Satellite": 41,
        "Airplane": 42,
        "Tumbler": 43,
        "Meteor": 44,
        # Masking
        "Bad column": 51,
        "Bad pixels": 52,
        "Excessive mask": 53,
        "Cosmic ray": 54,
        "Crosstalk": 55,
        "Edge bleed": 56,
        "Bleed trail": 57,
        "Dark trail": 58,
        # Sky estimation
        "Dark edge": 61,
        "Dark halo": 62,
        # Other
        "Other...": 255,
        "Awesome!": 1000
    }
}
