#!/usr/bin/env python3
# -*-coding:utf-8 -*-
# __author__:Jonathan
# email:nining1314@gmail.com

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Params = {
    'server': '127.0.0.1',
    'port': 8080,
    'request_timeout': 30,
    "urls": {
        "asset_report_with_no_id": "/asset/report/asset_with_no_asset_id/",
        "asset_report": "/asset/report/",
    },
    'asset_id': os.path.join(BASE_DIR, 'var', '.asset_id'),
    'log_file': os.path.join(BASE_DIR, 'logs', 'run_log'),

    'auth': {
        'user': 'root',
        'token': 'abc',
    },

}

if __name__ == '__main__':
    print(Params.get('asset_id'))
    print(Params.get('log_file'))
