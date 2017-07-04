#!/usr/bin/env python3
# -*-coding:utf-8 -*-
# __author__:Jonathan
# email:nining1314@gmail.com

from django.conf.urls import url
from asset import views

urlpatterns = [
    url(r'report/asset_with_no_asset_id/', views.asset_with_no_asset_id),
]