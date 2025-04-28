#!/usr/bin/env python
"""
Populate the gallery information.
"""
__author__ = "Alex Drlica-Wagner"
import json
from sqlalchemy import text

from .common import getDBHandle

def main():
    sql = """SELECT files.expname, files.ccd, qa.qaid as qa_id, qa.detail, qa.timestamp, qa.userid 
    FROM qa JOIN files ON (files.fileid=qa.fileid) 
    WHERE qa.qaid IN (SELECT MIN(qa.qaid) FROM qa WHERE problem=1000 GROUP BY qa.fileid)"""

    engine = getDBHandle()
    with engine.connect() as connection:
        res = connection.execute(text(sql))

    return [row._asdict() for row in res.fetchall()]

if __name__ == "__main__":
    print(json.dumps(main()))
