from django.shortcuts import render, HttpResponse, redirect
from django.views.decorators.csrf import csrf_exempt
import json
from asset import core
from asset import utils
from utils import page
from asset import models

@csrf_exempt
def asset_with_no_asset_id(request):

    if request.method == 'GET':
        return HttpResponse("get is OK.")
    elif request.method == "POST":
        asset_obj = core.Asset(request)
        res = asset_obj.get_asset_id_by_sn()
        return HttpResponse(json.dumps(res))


@csrf_exempt
def asset_report(request):
    if request.method == "POST":
        asset_obj = core.Asset(request)
        if asset_obj.data_is_valid():
            asset_obj.data_inject()

        return HttpResponse(json.dumps(asset_obj.response))


@csrf_exempt
def dashboard(request):
    return render(request, 'dashboard.html')

@csrf_exempt
def events_list(request):
    current_page = request.GET.get('p')
    all_count = models.EventLog.objects.all().order_by("-id").count()
    base_url = request.path_info

    page_info = page.PageInfo(current_page, 9, all_count, base_url, 11)
    obj_list = models.EventLog.objects.all().order_by("-id")[page_info.start():page_info.end()]

    return render(request, 'events_list.html', locals())


def events_detail(request, nid):
    nid = int(nid)
    event_obj = models.EventLog.objects.filter(id=nid).first()
    print(event_obj.name)
    return render(request, 'events_detail.html', locals())


@csrf_exempt
def servers_list(request):
    current_page = request.GET.get('p')
    all_count = models.EventLog.objects.all().order_by("-id").count()
    base_url = request.path_info

    page_info = page.PageInfo(current_page, 9, all_count, base_url, 11)
    obj_list = models.EventLog.objects.all().order_by("-id")[page_info.start():page_info.end()]

    return render(request, 'bak/servers_list.html')

def index(request):
    return render(request, 'index.html')

def main(request):
    return render(request, 'bak/main.html')

def table(request):
    return render(request, 'bak/table.html')


def video(request):
    return render(request, 'video.html')


def login(request):
    return render(request, 'login.html')

def test(request):
    return render(request, 'events_list.html')