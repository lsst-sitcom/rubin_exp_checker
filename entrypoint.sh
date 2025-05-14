#!/bin/bash

source /opt/lsst/software/stack/loadLSST.bash
setup daf_butler
setup afw
setup obs_lsst

if [[ -n "${DO_DB_MIGRATION}" ]]; then
    alembic upgrade head
fi

if [[ -n "${RUN_TESTS}" ]]; then
    pytest -p no:cacheprovider
else
    python -m lsst.ts.exp_checker.main
fi

