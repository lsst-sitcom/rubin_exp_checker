

FROM lsstsqre/centos:w_latest

USER root


WORKDIR /workdir

COPY . .

RUN <<ENDRUN
source /opt/lsst/software/stack/loadLSST.bash
pip install .

ENDRUN

# Switch to NONROOT user
USER lsst

CMD "./entrypoint.sh"

