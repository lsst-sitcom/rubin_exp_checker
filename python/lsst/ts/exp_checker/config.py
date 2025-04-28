from pathlib import Path
from typing import Dict, Any

from pydantic import Field
from pydantic_settings import BaseSettings

config_dictionary: Dict[str, Any] = {
    "base_dir": Path(__file__).resolve().parent,
    #"websocket_uri": "ws://localhost:9999/ws/client",
    "websocket_uri": "ws://rubintv:8080/rubintv/ws/ddv/client",
    "transfer_type": "butler",
    "compress_images": True,
    "repo": "https://github.com/lsst-sitcom/rubin_exp_checker",
    "slack_channel" : "#sciunit-image-inspection",
    "slack_link" : "https://rubin-obs.slack.com/archives/C07Q45NN0CX",
    "contact": "<URL>",
    "domain": "8000/rubintv/exp_checker/",
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
    "releases": ["LSSTCam"],
    "release": "LSSTCam",
    "images_per_fp": 189
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
        "Hardware imprint": 23,
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
        "Vampire": 59,
        # Sky estimation
        "Dark edge": 61,
        "Dark halo": 62,
        # Other
        "Other...": 255,
        "Awesome!": 1000
    }
}

class Configuration(BaseSettings):

    butler_repo: str = Field(
            default="embargo",
            description="Butler repository path or alias"
            )

    butler_collection: str = Field(
            default="u/kadrlica/LSSTCam/binCalexp4",
            description="Butler collection to display"
            )

    butler_instrument: str = Field(
            default="LSSTCam", 
            description="Name of the instrument to use in butler queries."
            )

    s3_profile_name: str = Field(
            default="rubin-rubintv-data-usdf-embargo",
            description="S3 Profile Name"
            )

    s3_endpoint_url: str = Field(
            default="https://sdfembs3.sdf.slac.stanford.edu",
            description="S3 Endpoint URL"
            )

    s3_bucket_name: str = Field(
            default="rubin-rubintv-data-usdf",
            description="S3 Bucket Name"
            )


    db_engine: str = Field(
            default="postgresql+psycopg2",
            description="Sqlalchemy database engine"
            )

    db_host: str = Field(
            default="",
            description="Database hostname"
            )

    db_port: str = Field(
            default="5432",
            description="Database port"
            )

    db_username: str = Field(
            default="exp-checker",
            description="Username to connect to database"
            )

    db_password: str = Field(
            default="",
            description="Password for connecting to the database"
            )

    db_dbname: str = Field(
            default="exp-checker",
            description="Name of the database to connect to"
            )


    # This is a temporary way to add some configuration as pydantic fields without
    # having to migrate all config usage away from the brackets syntax. All the
    # config_dict entries SHOULD get migrated and then this should be dropped.
    def __getitem__(cls, key: str) -> Dict[str, Any]:
        return config_dictionary.get(key)

config = Configuration()
