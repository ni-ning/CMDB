from django.shortcuts import render, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from asset import core


@csrf_exempt
def asset_with_no_asset_id(request):

    if request.method == 'GET':
        return HttpResponse("get")

    elif request.method == "POST":

        asset_obj = core.Asset(request)
        res = asset_obj.get_asset_id_by_sn()

        return HttpResponse(json.dumps(res))
