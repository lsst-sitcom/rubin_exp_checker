from pathlib import Path
from typing import Dict

config: Dict[str, any] = {
    "base_dir": Path(__file__).resolve().parent,
    "butler_repo": "embargo", #"s3://embargo@rubin-summit-users/butler.yaml"
    "butler_collection": "u/kadrlica/binCalexp4",
    "s3_profile_name": "rubin-rubintv-data-summit",
    "s3_endpoint_url": "https://s3dfrgw.slac.stanford.edu",
    "websocket_uri": "ws://localhost:9999/ws/client",
    "transfer_type": "butler",
    "compress_images": True,
    "repo": "https://github.com/lsst-sitcom/rubin_exp_checker",
    "slack_channel" : "#sciunit-image-inspection",
    "slack_link" : "https://rubin-obs.slack.com/archives/C07Q45NN0CX",
    "contact": "<URL>",
    "domain": "8000/rubintv/exp_checker/",
    "filedb": {
        #"r2.1i": ".db/files.2.1i-20241105.db",
        "r2.1i": ".db/files.comcam-20241109.db",
        "ComCam": ".db/files.comcam-20241117.db",
    },
    "fitspath": {
        #"r2.1i": "exclusive/output-2.1i-20190119/binned_sensor/",
        "r2.1i": "exclusive/comcam/calexp_binned/",
        "ComCam": "exclusive/comcam/calexp_binned/",
    },
    "fovpath": {
        #"r2.1i": "exclusive/output-2.1i-20190119/focal_plane/{expname}.png",
        "r2.1i": "exclusive/comcam/calexp_mosaic/{expname:.8s}/comcam_calexp_mosaic_{expname}.jpg",
        "ComCam": "exclusive/comcam/calexp_mosaic/{expname:.8s}/comcam_calexp_mosaic_{expname}.jpg",
    },
    "releases": ["r2.1i", "ComCam"],
    "release": None,
    "images_per_fp": 378,
    "problem_code": {
        "OK": 0,
        # Instrument
        "Guiding": 11,
        "Shutter": 12,
        "Readout": 13,
        "Haze": 14,
        # Flat fielding
        "Amp jump": 21,
        "Fringing": 22,
        "Tape bump": 23,
        "Tree rings": 24,
        "Vertical jump": 25,
        "Vertical stripes": 26,
        # Reflections
        "Ghost": 32,
        "Bright spray": 31,
        "Brush strokes": 33,
        "Bright arc": 34,
        # Tracks
        "Satellite": 41,
        "Airplane": 42,
        # Masking
        "Column mask": 51,
        "Excessive mask": 53,
        "Cosmic ray": 54,
        "Cross-talk": 55,
        "Edge-bleed": 56,
        # Sky estimation
        "Dark rim": 61,
        "Dark halo": 62,
        "Quilted sky": 63,
        "Wavy sky": 64,
        "Anti-bleed": 65,
        # Simulation
        "Speckling": 71,
        "Cosmic": 72,
        "Star": 73,
        "Galaxy": 74,
        "Sky background": 75,
        "Instrument": 76,
        "Knots": 77,
        # Other
        "Other...": 255,
        "Awesome!": 1000
    }
}
