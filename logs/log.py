#!/usr/bin/env python3
# -*-coding:utf-8 -*-
# __author__:Jonathan
# email:nining1314@gmail.com
from asset import models


def log_handler(asset_obj, event_name, user, detail, component=None):
    log_catelog = {
        1: ['FieldChanged', 'HardwareChanges'],
        2: ['NewComponentAdded'],
    }
    if not user.id:
        user = models.UserProfile.objects.last()
    event_type = None
    for k, v in log_catelog.items():
        if event_name in v:
            event_type = k
            break

    log_obj = models.EventLog(
        name=event_name,
        event_type=event_type,
        asset_id=asset_obj.id,
        component=component,
        detail=detail,
        user_id=user.id
    )
    log_obj.save()