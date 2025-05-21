# app/utils.py

import pandas as pd
import re
from state import add_message
from config import (
    LOGFILE_PATH,
    N_LOG_LINES,
)

def extract_features_with_line_numbers(logfile_path, last_n=N_LOG_LINES):
    pattern = re.compile(
        r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) \S+" (?P<status>\d+) (?P<size>\d+)'
    )
    data = []
    url_map = {
        '/': 0,
        '/index.html': 1,
        '/about': 2,
        '/contact': 3,
        '/help': 4,
        '/favicon.ico': 5,
        '/static/logo.png': 6,
        '/static/style.css': 7
    }
    try:
        with open(logfile_path) as f:
            all_lines = f.readlines()
            total_lines = len(all_lines)
            lines = all_lines[-last_n:]
            start_line_number = total_lines - len(lines) + 1
            for i, line in enumerate(lines):
                m = pattern.match(line)
                if m:
                    entry = m.groupdict()
                    entry['Line'] = start_line_number + i
                    entry['method_num'] = 0 if entry['method'] == 'GET' else 1
                    entry['url_num'] = url_map.get(entry['url'], 99)
                    entry['status'] = int(entry['status'])
                    entry['size'] = int(entry['size'])
                    data.append(entry)
    except Exception as e:
        add_message(f"Error reading logfile: {e}", "warning")
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if not df.empty:
       cols = ['Line'] + [c for c in df.columns if c != 'Line']
       df = df[cols]
    return df
 
