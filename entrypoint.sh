#!/bin/bash

source /opt/lsst/software/stack/loadLSST.bash
setup daf_butler
setup afw
setup obs_lsst

python -m lsst.ts.exp_checker.main

