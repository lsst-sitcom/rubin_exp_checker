from typing import Dict, List, Union, Any, Optional
import json
import sqlite3
from sqlite3 import Connection
from datetime import datetime, timedelta, UTC

from sqlalchemy import text

from .config import config
from .common import getDBHandle

def main(params: dict) -> None:
    engine = getDBHandle()
    stats = {}

    with engine.connect() as connection:
        # Basic stats: how many files done
        if params.get('total'):
            cursor = connection.execute(text('SELECT COUNT(DISTINCT(timestamp)) FROM qa'))
            result = cursor.fetchone()
            stats['total'] = int(result[0]) if result else 0

        if params.get('today'):
            # Set timezone to GMT if not set
            date = (datetime.now(UTC) - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            cursor = connection.execute(text(
                "SELECT COUNT(DISTINCT(timestamp)) FROM qa WHERE timestamp > :date"),
                                        {"date": date}
            )
            result = cursor.fetchone()
            stats['today'] = int(result[0]) if result else 0

        if params.get('breakup'):
            # How many have problems
            problems: List[Dict[str, Any]] = []
            stats['checked'] = 0

            for name, code in config['problem_code'].items():
                if 0 <= code < 1000:
                    cursor = connection.execute(text('SELECT COUNT(DISTINCT(fileid)) from qa WHERE problem = :code'),
                                                {"code": code})
                    row = cursor.fetchone()
                    
                    if code == 0:
                        if row:
                            stats['fine'] = int(row[0])
                            stats['checked'] = stats.get('checked', 0) + int(row[0])
                    else:
                        this_problem = {
                            "name": name,
                            "all": 0,
                            "false_positive": 0
                        }
                        
                        if row:
                            stats['checked'] = stats.get('checked', 0) + int(row[0])
                            this_problem['all'] += int(row[0])
                        
                        # Check negative code
                        cursor = connection.execute(text('SELECT COUNT(DISTINCT(fileid)) from qa WHERE problem = :code'),
                                                {"code": -code})
                        row = cursor.fetchone()
                        
                        if row:
                            stats['checked'] = stats.get('checked', 0) + int(row[0])
                            this_problem['all'] += int(row[0])
                            this_problem['false_positive'] += int(row[0])
                        
                        problems.append(this_problem)
            
            stats['breakup'] = problems

        if params.get('throughput'):
            cursor = connection.execute(text('''
                SELECT substr(timestamp,1,10) as date,
                       COUNT(1) as marks,
                       COUNT(DISTINCT(fileid)) as files
                FROM qa
                GROUP BY substr(timestamp,1,10)
            '''))
            
            throughput = []
            for row in cursor.fetchall():
                throughput.append({
                    'date': row[0],
                    'marks': row[1],
                    'files': row[2]
                })
            
            stats['throughput'] = throughput

    return stats

if __name__ == "__main__":
    params = {"release": "r2.1i", "total": True, "today": True}
    print(json.dumps(main(params)))
