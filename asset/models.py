from django.db import models
from django.contrib.auth.models import User


class Asset(models.Model):
    """资产总表"""
    asset_type_choices = (
        ('server', u'服务器'),
        ('networkdevice', u'网络设备'),
        ('storagedevice', u'存储设备'),
        ('securitydevice', u'安全设备'),
        ('accessories', u'备件'),
        ('software', u'软件资产'),
    )
    asset_type = models.CharField(choices=asset_type_choices, max_length=64, default='server')
    name = models.CharField(max_length=64, unique=True)
    sn = models.CharField(u'资产SN号', max_length=128, unique=True)
    manufactory = models.ForeignKey('Manufactory', verbose_name=u'制造商', null=True, blank=True)
    management_ip = models.GenericIPAddressField(u'管理IP', blank=True, null=True)
    contract = models.ForeignKey('Contract', verbose_name=u'合同', blank=True, null=True)
    trade_date = models.DateField(u'购买日期', null=True, blank=True)
    expire_date = models.DateField(u'过保日期', null=True, blank=True)
    price = models.FloatField(u'价格', null=True, blank=True)
    business_unit = models.ForeignKey('BusinessUnit', verbose_name=u'所属业务线', null=True, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    admin = models.ForeignKey('UserProfile', verbose_name=u'资产管理员', null=True, blank=True)
    cabinet = models.ForeignKey('Cabinet', verbose_name=u'IDC机柜', null=True, blank=True)
    status_choices = (
        (0, u'在线'),
        (1, u'已下线'),
        (2, u'未知'),
        (3, u'故障'),
        (4, u'备用'),
    )
    status = models.SmallIntegerField(choices=status_choices, default=0)
    memo = models.TextField(u'备注', null=True, blank=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, auto_now=True)

    class Meta:
        verbose_name = '资产总表'
        verbose_name_plural = '资产总表'

    def __str__(self):
        return '<id: %s name: %s>' % (self.id, self.name)


class Server(models.Model):
    """服务器设备"""
    asset = models.OneToOneField('Asset')
    sub_asset_type_choices = (
        (0, u'PC服务器'),
        (1, u'刀片机'),
        (2, u'小型机'),
    )
    # auto 数据一般可信; manual 数据一般不可信
    created_by_choices = (
        ('auto', 'Auto'),
        ('manual', 'Manual'),
    )
    sub_asset_type = models.SmallIntegerField(choices=sub_asset_type_choices, verbose_name=u'服务器类型', default=0)
    created_by = models.CharField(choices=created_by_choices, max_length=32, default='auto')

    # 兼容虚拟主机
    hosted_on = models.ForeignKey('self', related_name='hosted_on_server', blank=True, null=True)

    model = models.CharField(verbose_name=u'型号', max_length=128, null=True, blank=True)
    raid_type = models.CharField(u'raid类型', max_length=512, blank=True, null=True)
    os_type = models.CharField(u'操作系统类型', max_length=64, blank=True, null=True)
    os_distribution = models.CharField(u'发行版本', max_length=64, blank=True, null=True)
    os_release = models.CharField(u'操作系统版本', max_length=64, blank=True, null=True)

    class Meta:
        verbose_name = '服务器'
        verbose_name_plural = "服务器"

    def __str__(self):
        return '%s sn:%s' % (self.asset.name, self.asset.sn)


class SecurityDevice(models.Model):
    """安全设备"""
    asset = models.OneToOneField('Asset')
    sub_asset_type_choices = (
        (0, u'防火墙'),
        (1, u'入侵检测设备'),
        (2, u'互联网网关'),
        (4, u'运维审计系统'),
    )
    sub_asset_type = models.SmallIntegerField(choices=sub_asset_type_choices, verbose_name="服务器类型", default=0)

    def __str__(self):
        return self.asset.id


class NetworkDevice(models.Model):
    asset = models.OneToOneField('Asset')
    sub_asset_type_choices = (
        (0, u'路由器'),
        (1, u'交换机'),
        (2, u'负载均衡'),
        (4, u'VPN设备'),
    )
    sub_asset_type = models.SmallIntegerField(choices=sub_asset_type_choices, verbose_name="服务器类型", default=0)
    vlan_ip = models.GenericIPAddressField(u'VlanIP', blank=True, null=True)
    intranet_ip = models.GenericIPAddressField(u'内网IP', blank=True, null=True)
    model = models.CharField(u'型号', max_length=128, null=True, blank=True)
    firmware = models.ForeignKey('Software', blank=True, null=True)
    port_num = models.SmallIntegerField(u'端口个数', null=True, blank=True)
    device_detail = models.TextField(u'设备详细配置', null=True, blank=True)

    class Meta:
        verbose_name = '网络设备'
        verbose_name_plural = "网络设备"


class Software(models.Model):
    """软件/系统"""
    asset = models.OneToOneField('Asset')
    sub_asset_type_choices = (
        (0, 'OS'),
        (1, u'办公\开发软件'),
        (2, u'业务软件'),
    )
    sub_asset_type = models.SmallIntegerField(choices=sub_asset_type_choices, verbose_name=u"软件类型", default=0)
    license_num = models.IntegerField(verbose_name=u"授权数", default=1)
    version = models.CharField(u'软件/系统版本', max_length=64, help_text=u'eg. CentOS release 6.5 (Final)', unique=True)

    def __str__(self):
        return self.version

    class Meta:
        verbose_name = '软件/系统'
        verbose_name_plural = "软件/系统"


class CPU(models.Model):
    """CPU组件"""
    asset = models.OneToOneField('Asset')
    cpu_model = models.CharField(u'CPU型号', max_length=128, blank=True)
    cpu_count = models.SmallIntegerField(u'物理cpu个数', default=1)
    cpu_core_count = models.SmallIntegerField(u'cpu核数', default=1)
    memo = models.TextField(u'备注', null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta:
        verbose_name = 'CPU部件'
        verbose_name_plural = "CPU部件"

    def __str__(self):
        return self.cpu_model


class RAM(models.Model):
    """内存组件"""
    asset = models.ForeignKey('Asset')
    sn = models.CharField(u'SN号', max_length=128, blank=True, null=True)
    model = models.CharField(u'内存型号', max_length=128)
    slot = models.CharField(u'插槽', max_length=64)
    capacity = models.IntegerField(u'内存大小(MB)')
    memo = models.CharField(u'备注', max_length=128, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return '%s:%s:%s' % (self.asset_id, self.slot, self.capacity)

    class Meta:
        verbose_name = 'RAM'
        verbose_name_plural = "RAM"
        unique_together = ("asset", "slot")

    auto_create_fields = ['sn', 'slot', 'model', 'capacity']


class Disk(models.Model):
    """硬盘组件"""
    asset = models.ForeignKey('Asset')
    sn = models.CharField(u'SN号', max_length=128, blank=True, null=True)
    slot = models.CharField(u'插槽位', max_length=64)
    # slot = models.IntegerField(u'插槽位')
    model = models.CharField(u'磁盘型号', max_length=128, blank=True, null=True)
    capacity = models.FloatField(u'磁盘容量GB')
    disk_iface_choices = (
        ('SATA', 'SATA'),
        ('SAS', 'SAS'),
        ('SCSI', 'SCSI'),
        ('SSD', 'SSD'),
    )
    iface_type = models.CharField(u'接口类型', max_length=64, choices=disk_iface_choices, default='SAS')
    memo = models.TextField(u'备注', blank=True, null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)

    auto_create_fields = ['sn', 'slot', 'model', 'capacity', 'iface_type']

    class Meta:
        unique_together = ("asset", "slot")
        verbose_name = '硬盘'
        verbose_name_plural = "硬盘"

    def __str__(self):
        return '%s:slot:%s capacity:%s' % (self.asset_id, self.slot, self.capacity)


class NIC(models.Model):
    """网卡组件"""
    asset = models.ForeignKey('Asset')
    name = models.CharField(u'网卡名', max_length=64, blank=True, null=True)
    sn = models.CharField(u'SN号', max_length=128, blank=True, null=True)
    model = models.CharField(u'网卡型号', max_length=128, blank=True, null=True)
    macaddress = models.CharField('MAC', max_length=64, unique=True)
    ipaddress = models.GenericIPAddressField('IP', blank=True, null=True)
    netmask = models.CharField(max_length=64, blank=True, null=True)
    bonding = models.CharField(max_length=64, blank=True, null=True)
    memo = models.CharField(u'备注', max_length=128, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True,auto_now=True, null=True)

    def __str__(self):
        return '%s:%s' % (self.asset_id, self.macaddress)

    class Meta:
        verbose_name = u'网卡'
        verbose_name_plural = u"网卡"

    auto_create_fields = ['name', 'sn', 'model', 'macaddress', 'ipaddress', 'netmask', 'bonding']


class RaidAdaptor(models.Model):
    """Raid卡"""
    asset = models.ForeignKey('Asset')
    sn = models.CharField(u'SN号', max_length=128, blank=True, null=True)
    slot = models.CharField(u'插口', max_length=64)
    model = models.CharField(u'型号', max_length=64, blank=True, null=True)
    memo = models.TextField(u'备注', blank=True, null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ("asset", "slot")


class Manufactory(models.Model):
    """制造商表"""
    manufactory = models.CharField(u'制造商名称', max_length=64, unique=True)
    suppport_num = models.CharField(u'支持电话', max_length=32, null=True, blank=True)
    memo = models.CharField(u'备注', max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = '制造商表'
        verbose_name_plural = '制造商表'

    def __str__(self):
        return self.manufactory


class BusinessUnit(models.Model):
    """业务线表"""
    parent_unit = models.ForeignKey('self', related_name='parent_level', blank=True, null=True)
    name = models.CharField(u'业务线', max_length=64, unique=True)
    memo = models.CharField(u'备注', max_length=64, blank=True, null=True)

    class Meta:
        verbose_name = '业务线表'
        verbose_name_plural = '业务线表'

    def __str__(self):
        return self.name


class Contract(models.Model):
    """合同表"""
    sn = models.CharField(u'合同号', max_length=128, unique=True)
    name = models.CharField(u'合同名称', max_length=128)
    price = models.FloatField(u'合同金额')
    detail = models.TextField(u'合同详情', blank=True, null=True)
    memo = models.TextField(u'备注', blank=True, null=True)
    start_date = models.DateField(blank=True)
    end_date = models.DateField(blank=True)
    license_num = models.IntegerField(u'license数量', blank=True, null=True)
    create_date = models.DateField(auto_now_add=True)
    update_date = models.DateField(auto_now=True)

    class Meta:
        verbose_name = '合同表'
        verbose_name_plural = '合同表'

    def __str__(self):
        return self.name


class Cabinet(models.Model):
    """机柜表"""
    idc = models.ForeignKey('IDC', verbose_name=u'IDC机房')
    number = models.CharField(max_length=32)

    class Meta:
        verbose_name = '机柜表'
        verbose_name_plural = '机柜表'
        unique_together = ('idc', 'number')

    def __str__(self):
        return self.number


class IDC(models.Model):
    """机房表"""
    name = models.CharField(u'机房名称', max_length=64, unique=True)
    memo = models.CharField(u'备注', max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = '机房表'
        verbose_name_plural = "机房表"

    def __str__(self):
        return self.name


class Tag(models.Model):
    """资产标签表"""
    name = models.CharField('Tag name', max_length=32, unique=True)
    creator = models.ForeignKey('UserProfile')
    create_date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = '资产标签表'
        verbose_name_plural = "资产标签表"

    def __str__(self):
        return self.name


class EventLog(models.Model):
    """事件日志表"""
    name = models.CharField(u'事件名称', max_length=128)
    event_type_choices = (
        (1, u'硬件变更'),
        (2, u'新增配件'),
        (3, u'设备下线'),
        (4, u'设备上线'),
        (5, u'定期维护'),
        (6, u'业务上线\更新\变更'),
        (7, u'其它'),
    )
    event_type = models.SmallIntegerField(u'事件类型', choices=event_type_choices)
    asset = models.ForeignKey('Asset')
    component = models.CharField(u'事件子项', max_length=256, blank=True, null=True)
    detail = models.TextField(u'事件详情', blank=True, null=True)
    date = models.DateTimeField(u'事件时间', auto_now_add=True)
    user = models.ForeignKey('UserProfile', verbose_name=u'事件源')
    memo = models.TextField(u'备注', blank=True, null=True)

    class Meta:
        verbose_name = '事件日志表'
        verbose_name_plural = "事件日志表"

    def __str__(self):
        return self.name

    def colored_event_type(self):
        if self.event_type == 1:
            cell_html = '<span style="background: orange;">%s</span>'
        elif self.event_type == 2:
            cell_html = '<span style="background: yellowgreen;">%s</span>'
        else:
            cell_html = '<span >%s</span>'
        return cell_html % self.get_event_type_display()

    colored_event_type.allow_tags = True
    colored_event_type.short_description = u'事件类型'


class UserProfile(models.Model):
    """用户表"""
    user = models.OneToOneField(User)
    name = models.CharField(max_length=32, null=True, blank=True)
    phone = models.CharField(max_length=32, null=True, blank=True)
    token = models.CharField(max_length=64, null=True, blank=True)


class NewAssetApprovalZone(models.Model):
    """新资产待审批区"""
    sn = models.CharField(u'资产SN号', max_length=128, unique=True)
    asset_type_choices = (
        ('server', u'服务器'),
        ('switch', u'交换机'),
        ('router', u'路由器'),
        ('firewall', u'防火墙'),
        ('storage', u'存储设备'),
        ('NLB', u'NetScaler'),
        ('wireless', u'无线AP'),
        ('software', u'软件资产'),
        ('others', u'其它类'),
    )
    asset_type = models.CharField(choices=asset_type_choices, max_length=64, blank=True, null=True)
    manufactory = models.CharField(max_length=64, blank=True, null=True)
    model = models.CharField(max_length=128, blank=True, null=True)
    ram_size = models.IntegerField(blank=True, null=True)
    cpu_model = models.CharField(max_length=128, blank=True, null=True)
    cpu_count = models.IntegerField(blank=True, null=True)
    cpu_core_count = models.IntegerField(blank=True, null=True)
    os_distribution = models.CharField(max_length=64, blank=True, null=True)
    os_type = models.CharField(max_length=64, blank=True, null=True)
    os_release = models.CharField(max_length=64, blank=True, null=True)
    data = models.TextField(u'资产数据')
    date = models.DateTimeField(u'汇报日期', auto_now_add=True)
    approved = models.BooleanField(u'已批准', default=False)
    approved_by = models.ForeignKey('UserProfile', verbose_name=u'批准人', blank=True, null=True)
    approved_date = models.DateTimeField(u'批准日期', blank=True, null=True)

    def __str__(self):
        return self.sn

    class Meta:
        verbose_name = '新上线待批准资产'
        verbose_name_plural = "新上线待批准资产"

