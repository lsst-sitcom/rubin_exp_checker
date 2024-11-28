#!/usr/bin/env python
"""
Generic python script.
"""
__author__ = "Alex Drlica-Wagner"
import json

from .common import getDBHandle

def main():
    dbh = getDBHandle()
    sql = 'SELECT files.expname, files.ccd, qa.qaid as qa_id, qa.detail, qa.timestamp, qa.userid FROM qa JOIN files ON (files.fileid=qa.fileid) WHERE qa.qaid IN (SELECT MIN(qa.qaid) FROM qa WHERE problem=1000 GROUP BY qa.fileid)'
    res = dbh.execute(sql)
    return [dict(row) for row in res.fetchall()]

if __name__ == "__main__":
    print(json.dumps(main()))
