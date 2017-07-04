from django.contrib import admin
from asset import models
from asset import core


class AssetApprovalAdmin(admin.ModelAdmin):
    list_display = ('sn', 'asset_type', 'manufactory', 'model', 'cpu_model', 'os_type', 'os_release', 'approved',)
    list_filter = ('asset_type', 'os_type', )
    search_fields = ('sn', 'os_type', )
    list_editable = ('asset_type', 'approved',)
    actions = ['asset_approval', ]

    def asset_approval(self, request, querysets):
        # request   action操作的请求request
        # querysets 自定义操作时，选择操作待审批对象集
        for obj in querysets:
            asset_obj = core.Asset(request)
            if asset_obj.data_is_valid_without_id(obj):
                asset_obj.data_inject()  # 资产总表，关联表各种新增记录
                obj.approved = True     # 待审批对象，变为已审批
                obj.save()              # 保存(内部处理：先删除，在新增)

    asset_approval.short_description = '新资产审批'


admin.site.register(models.UserProfile)
admin.site.register(models.Asset)
admin.site.register(models.Server)
admin.site.register(models.NetworkDevice)
admin.site.register(models.IDC)
admin.site.register(models.BusinessUnit)
admin.site.register(models.Contract)
admin.site.register(models.CPU)
admin.site.register(models.Disk)
admin.site.register(models.NIC)
admin.site.register(models.RAM)
admin.site.register(models.Manufactory)
admin.site.register(models.Tag)
admin.site.register(models.Software)
admin.site.register(models.EventLog)
admin.site.register(models.NewAssetApprovalZone, AssetApprovalAdmin)
