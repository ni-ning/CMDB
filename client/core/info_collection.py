#!/usr/bin/env python3
# -*-coding:utf-8 -*-
# __author__:Jonathan
# email:nining1314@gmail.com
import platform,sys
from plugins import plugin_api


class InfoCollection(object):
    def __init__(self):
        pass

    def get_platform(self):
        os_platform = platform.system()
        return os_platform

    def collect(self):
        os_platform = self.get_platform()
        try:
            func = getattr(self, os_platform)
            info_data = func()
            formatted_data = self.build_report_data(info_data)
            return formatted_data

        except AttributeError as e:
            sys.exit("Error:Asset doens't support os [%s]! " % os_platform)

    def Linux(self):
        sys_info = plugin_api.LinuxSysInfo()

        return sys_info

    def Windows(self):
        sys_info = plugin_api.WindowsSysInfo()
        return sys_info


    def build_report_data(self,data):
        return data