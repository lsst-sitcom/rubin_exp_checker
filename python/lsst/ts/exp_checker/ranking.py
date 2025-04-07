#!/usr/bin/env python
"""
Generic python script.
"""
__author__ = "Alex Drlica-Wagner"

from typing import List, Dict
import json
from .common import getDBHandle

import sqlalchemy

def main(limit: int | None = None) -> List[Dict[str, int]]:
    engine = getDBHandle()

    query = 'SELECT userid, total_files, flagged_files FROM submissions WHERE total_files > 0 ORDER BY total_files DESC'
    if limit is not None:
        query += f' LIMIT {limit}'

    with engine.connect() as connection:
        res = connection.execute(sqlalchemy.text(query))
    return [dict(row) for row in res.fetchall()]

