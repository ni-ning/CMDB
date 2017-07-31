#!/usr/bin/env python3
# -*-coding:utf-8 -*-
# __author__:Jonathan
# email:nining1314@gmail.com

from django.conf.urls import url
from asset import views

urlpatterns = [
    url(r'report/asset_with_no_asset_id/$', views.asset_with_no_asset_id),
    url(r'dashboard/$', views.dashboard),
    url(r'events_list/$', views.events_list),
    url(r'events/detail-(\d+)/$', views.events_detail),
    url(r'main/$', views.main),
    url(r'table/$', views.table),
    url(r'report/$', views.asset_report),
    url(r'video/$', views.video),
    url(r'login/$', views.login),
    url(r'test/$', views.test),
]