
import unittest
import pytest
import json

from lsst.ts.exp_checker import submit
from lsst.ts.exp_checker.common import getDBHandle
from sqlalchemy import text


@pytest.fixture()
def load_database():
    engine = getDBHandle()
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO releases (release_id, name, butler, dataset_type, collection) "
                          "VALUES (1001, 'LSSTCam-v1', 'embargo', 'binnedCalexp', 'LSSTCam/runs/binnedv1') "))

        # One into the default release
        conn.execute(text("INSERT INTO files (release, expname, ccd, band, name) "
                          "VALUES (1, '2025051000567', '94', 'i', 'asdf') "))

        # One into the new release
        conn.execute(text("INSERT INTO files (release, expname, ccd, band, name) "
                          "VALUES (1001, '2025051000200', '1', 'g', 'asdf') "))
        conn.commit()

    yield
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM releases WHERE release_id  = 1001"))
        conn.execute(text("DELETE FROM files WHERE expname = '2025051000567'"))
        conn.commit()


def test_select_image(load_database):

    # Put an entry into the database
    # mock the butler get
    # POST to the "submit" page with the release name

    json_string = submit.main({"uid": 1234, "release": "LSSTCam-v1"})
    result = json.loads(json_string)
    print(result)

    # get back a data Id.
    assert 'expname' in result
    assert 'ccd' in result
    assert result['expname'] == '2025051000200'
