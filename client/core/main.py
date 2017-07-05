#!/usr/bin/env python3
# -*-coding:utf-8 -*-
# __author__:Jonathan
# email:nining1314@gmail.com
import os
import sys
import json
import requests
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from conf import settings
from core import api_token
from core import info_collection


class ArgvHandler(object):
    def __init__(self, argv_list):
        self.argvs = argv_list
        self.parse_argv()

    def parse_argv(self):
        if len(self.argvs) > 1:
            if hasattr(self, self.argvs[1]):
                func = getattr(self, self.argvs[1])
                func()
            else:
                self.help_msg()
        else:
            self.help_msg()

    def help_msg(self):
        msg = '''
        collect_data       收集硬件信息
        run_forever
        get_asset_id
        report_asset       收集硬件信息并汇报
        '''
        print(msg)

    def collect_data(self):
        obj = info_collection.InfoCollection()
        asset_data = obj.collect()
        print(asset_data)

    def run_forever(self):
        print('run_forever')

    def get_asset_id(self):
        print('get_asset_id')

    def report_asset(self):
        obj = info_collection.InfoCollection()
        asset_data = obj.collect()
        asset_id = self.load_asset_id()

        if asset_id:
            # 有设备编号
            asset_data["asset_id"] = asset_id
            post_url = "asset_report"
        else:
            # 无设备编号
            asset_data["asset_id"] = None
            post_url = "asset_report_with_no_id"

        data = {
            'asset_data': json.dumps(asset_data)
        }

        response = self.__submit_data(post_url, data, method='post')


        if "asset_id" in response:
            self.__update_asset_id(response["asset_id"])

        # logs

    def load_asset_id(self):
        asset_id_file = settings.Params['asset_id']
        has_asset_id = False
        if os.path.isfile(asset_id_file):
            f = open(asset_id_file)
            asset_id = f.read().strip()
            f.close()
            if asset_id.isdecimal():
                return asset_id
        return has_asset_id

    def __submit_data(self, url, data, method):
        if url in settings.Params['urls']:
            if type(settings.Params['port']) is int:
                full_url = "http://%s:%s%s" % (
                                            settings.Params['server'],
                                            settings.Params['port'],
                                            settings.Params['urls'][url])
            else:
                full_url = "http://%s%s" % (
                    settings.Params['server'],
                    settings.Params['urls'][url])

            print('Connecting [%s], it may take a minute.' % full_url)

            if method == 'get':
                pass
            elif method == 'post':
                try:
                    res = requests.post(url=full_url, data=data)
                    callback = json.loads(res.text)
                    print("\033[31;1m[%s]:[%s]\033[0m response:\n%s" % (method, full_url, callback))
                    return callback
                except Exception as e:
                    sys.exit("\033[31;1m%s\033[0m" % e)





        else:
            raise KeyError

    def __update_asset_id(self, new_asset_id):
        asset_id_file = settings.Params['asset_id']
        f = open(asset_id_file, "w")
        f.write(str(new_asset_id))
        f.close()
