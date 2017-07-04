#!/usr/bin/env python3
# -*-coding:utf-8 -*-
# __author__:Jonathan
# email:nining1314@gmail.com
import json
from django.core.exceptions import ObjectDoesNotExist
from asset import models


class Asset(object):
    def __init__(self, request):
        self.request = request
        self.mandatory_fields = ['sn', 'asset_id', 'asset_type', ]  # 必须包含的字段验证
        self.field_sets = {
            # ToDo
        }

        self.response = {  # 数据返回要标准
            'error': [],
            'info': [],
            'warning': [],
        }
    """
    self.resonse作为返回结果的存储
    self.response_msg作为返回结果的操作
    """
    def response_msg(self, msg_type, key, msg):
        if msg_type in self.response:
            self.response[msg_type].append({key: msg})
        else:
            raise ValueError

    def mandatory_check(self, data, only_check_sn=False):
        """合法性检查，要求客户端发过来的数据必须包括指定的字段"""
        for field in self.mandatory_fields:
            if field not in data:
                self.response_msg('error', 'MandatoryCheckFailed',
                                  "The field [%s] is mandatory and not provided in your reporting data" % field)
        else:
            if self.response['error']:
                return False

        # 字段合法性通过
        """
        1. 根据sn号在资产总表Asset里，找不到对应记录，就把上报的数据存到临时待审批表NewAssetApprovalZone
            -- 第一次上报，根据sn号在表NewAssetApprovalZone新增记录
            -- 多次上报时，根据sn号在表NewAssetApprovalZone更新记录
        2. 根据sn号在资产总表Asset里，找到对应记录，就把对应的资产asset_id返回给客户端
        3. 验证开关

            -- 只验证sn号,即only_check_sn=True
            -- 验证sn和asset_id,即only_check_sn=False
        4. models.Asset.objects.get(sn=data['sn'])特性：不存在会抛出异常，ObjectDoesNotExist
        """
        try:
            if not only_check_sn:
                self.asset_obj = models.Asset.objects.get(id=int(data['asset_id']), sn=data['sn'])
            else:
                self.asset_obj = models.Asset.objects.get(sn=data['sn'])
            return True
        except ObjectDoesNotExist as e:
            self.response_msg('error', 'AssetDataInvalid',
                              "Cannot find asset object in DB by using asset id [%s] and SN [%s] " % (
                                  data['asset_id'], data['sn']))
            self.waiting_approval = True
            return False

    def get_asset_id_by_sn(self):

        data = self.request.POST.get('asset_data')  # 获取客户端采集的数据
        response = {}   # 定义返回数据格式字典
        if data:
            try:
                data = json.loads(data)  # 客户端数据解析为字典

                """
                1. 资产，审核区无记录
                2. 资产，审核区有记录：未验证
                3. 资产，审核区有记录：已验证，资产总表有记录，服务器表无记录
                4. 资产，审核区有记录：已验证，资产总表有记录，服务器表有记录
                """
                if self.mandatory_check(data, only_check_sn=True):
                    pass
                else:
                    # 只验证sn号时未通过分支，代表时新资产，即资产总表Asset不存在记录
                    if hasattr(self, 'waiting_approval'):
                        response = {
                            'needs_aproval': "this is a new asset,needs IT admin's approval to create the new asset id."
                        }
                        self.clean_data = data
                        self.save_new_asset_to_approval_zone() # 表NewAssetApprovalZone新增记录
                    else:
                        response = self.response
            except ValueError as e:
                self.response_msg('error', 'AssetDataInvalid', str(e))
                response = self.response
        else:
            self.response_msg('error', 'AssetDataInvalid', "The reported asset data is not valid or provided")
            response = self.response

        return response

    def save_new_asset_to_approval_zone(self):
        asset_sn = self.clean_data.get('sn')
        asset_already_in_approval_zone, status = models.NewAssetApprovalZone.objects.get_or_create(
            sn=asset_sn,
            data=json.dumps(self.clean_data),
            manufactory=self.clean_data.get('manufactory'),
            model=self.clean_data.get('model'),
            asset_type=self.clean_data.get('asset_type'),
            ram_size=self.clean_data.get('ram_size'),
            cpu_model=self.clean_data.get('cpu_model'),
            cpu_count=self.clean_data.get('cpu_count'),
            cpu_core_count=self.clean_data.get('cpu_core_count'),
            os_distribution=self.clean_data.get('os_distribution'),
            os_release=self.clean_data.get('os_release'),
            os_type=self.clean_data.get('os_type'),
        )
        print(asset_already_in_approval_zone, status)
        return True

    def data_is_valid_without_id(self, db_obj=None):
        # 待审批区未审核的记录，在资产总表Asset新增记录，得到包含资产id的数据self.clean_data

        if db_obj:
            data = db_obj.data  # 从admin页面actions列表调用
        else:
            data = self.request.POST.get("asset_data")  # 从页面request传入数据

        if data:
            try:
                data = json.loads(data)
                asset_obj, status = models.Asset.objects.get_or_create(sn=data.get('sn'),name=data.get('sn'))
                data['asset_id'] = asset_obj.id
                self.mandatory_check(data)
                self.clean_data = data
                if not self.response['error']:
                    return True
            except ValueError as e:
                self.response_msg('error', 'AssetDataInvalid', str(e))
        else:
            self.response_msg('error', 'AssetDataInvalid', "The reported asset data is not valid or provided")

    def data_inject(self):
        # 完整资产创建和更新
        if self.__is_new_asset():
            # 完整新资产，如服务器表中有对应记录
            self.create_asset()
        else:
            # 不是完整新增产，如服务器表中无对应记录
            pass

    def __is_new_asset(self):
        if not hasattr(self.asset_obj, self.clean_data['asset_type']):
            return True
        else:
            return False

    def create_asset(self):

        func = getattr(self, '_create_%s' % self.clean_data['asset_type'])
        create_obj = func()

    def _create_server(self):
        self.__create_server_info()
        self.__create_or_update_manufactory()

        self.__create_cpu_component()
        self.__create_disk_component()
        self.__create_nic_component()
        self.__create_ram_component()

    def __create_server_info(self, ignore_errs=False):
        # 1. 验证字段合法性 __verify_field，有问题保存在 self.response['error']中
        # 2. ignore_errs=True，开关选项，可忽略错误
        # 3. 汇总新增记录所需数据 data_set
        # 4. 新增记录 obj = models.Server(**data_set);obj.save()

        try:
            self.__verify_field(self.clean_data, 'model', str)
            if not len(self.response['error']) or ignore_errs == True:
                data_set = {
                    'asset_id': self.asset_obj.id,
                    'raid_type': self.clean_data.get('raid_type'),
                    'model': self.clean_data.get('model'),
                    'os_type': self.clean_data.get('os_type'),
                    'os_distribution': self.clean_data.get('os_distribution'),
                    'os_release': self.clean_data.get('os_release'),
                }
                obj = models.Server(**data_set)
                obj.save()
                return obj
        except Exception as e:
            self.response_msg('error','ObjectCreationException', 'Object [server] %s'% str(e))

    def __create_or_update_manufactory(self):
        print('__create_or_update_manufactory')

    def __create_cpu_component(self, ignore_errs=False):
        try:
            self.__verify_field(self.clean_data, 'model', str)
            self.__verify_field(self.clean_data, 'cpu_count', int)
            self.__verify_field(self.clean_data, 'cpu_core_count', int)
            if not len(self.response['error']) or ignore_errs == True:
                data_set = {
                    'asset_id': self.asset_obj.id,
                    'cpu_model': self.clean_data.get('cpu_model'),
                    'cpu_count': self.clean_data.get('cpu_count'),
                    'cpu_core_count': self.clean_data.get('cpu_core_count'),
                }
                obj = models.CPU(**data_set)
                obj.save()
                log_msg = "Asset[%s] --> has added new [cpu] component with data [%s]" % (self.asset_obj, data_set)
                self.response_msg('info', 'NewComponentAdded', log_msg)
                return obj
        except Exception as e:
            self.response_msg('error', 'ObjectCreationException', 'Object [cpu] %s' % str(e))

    def __create_disk_component(self):
        disk_info = self.clean_data.get('physical_disk_driver')
        if disk_info:
            for disk_item in disk_info:
                try:
                    self.__verify_field(disk_item, 'capacity', float)
                    self.__verify_field(disk_item, 'iface_type', str)
                    self.__verify_field(disk_item, 'model', str)
                    if not len(self.response['error']):
                        data_set = {
                            'asset_id': self.asset_obj.id,
                            'sn': disk_item.get('sn'),
                            'slot': disk_item.get('slot'),
                            'capacity': disk_item.get('capacity'),
                            'model': disk_item.get('model'),
                            'iface_type': disk_item.get('iface_type'),
                        }
                        obj = models.Disk(**data_set)
                        obj.save()
                except Exception as e:
                    self.response_msg('error', 'ObjectCreationException', 'Object [disk] %s' % str(e))
        else:
            self.response_msg('error', 'LackOfData', 'Disk info is not provied in your reporting data')

    def __create_nic_component(self):
        nic_info = self.clean_data.get('nic')
        if nic_info:
            for nic_item in nic_info:
                try:
                    self.__verify_field(nic_item, 'macaddress', str)
                    if not len(self.response['error']):
                        data_set = {
                            'asset_id': self.asset_obj.id,
                            'name': nic_item.get('name'),
                            'sn': nic_item.get('sn'),
                            'macaddress': nic_item.get('macaddress'),
                            'ipaddress': nic_item.get('ipaddress'),
                            'bonding': nic_item.get('bonding'),
                            'model': nic_item.get('model'),
                            'netmask': nic_item.get('netmask'),
                        }
                        obj = models.NIC(**data_set)
                        obj.save()
                except Exception as e:
                    self.response_msg('error', 'ObjectCreationException', 'Object [nic] %s' % str(e))
        else:
            self.response_msg('error', 'LackOfData', 'NIC info is not provied in your reporting data')

    def __create_ram_component(self):
        ram_info = self.clean_data.get('ram')
        if ram_info:
            for ram_item in ram_info:
                try:
                    self.__verify_field(ram_item, 'capacity', int)
                    self.__verify_field(ram_item, 'slot', str)
                    if not len(self.response['error']):
                        data_set = {
                            'asset_id': self.asset_obj.id,
                            'slot': ram_item.get("slot"),
                            'sn': ram_item.get('sn'),
                            'capacity': ram_item.get('capacity'),
                            'model': ram_item.get('model'),
                        }

                        obj = models.RAM(**data_set)
                        obj.save()

                except Exception as e:
                    self.response_msg('error', 'ObjectCreationException', 'Object [ram] %s' % str(e))
        else:
            self.response_msg('error', 'LackOfData', 'RAM info is not provied in your reporting data')

    def __verify_field(self, data_set, field_key, data_type, required=True):
        # data_set  ---> self.clean_data，采集的数据字典
        # field_key ---> 'model',采集数据字典的key
        # data_type --->  str，所需的数据类型
        # required  --->  采集的字典中需要此字段
        # 最终结果是判断self.repsonse中'error'是否有值

        field_val = data_set.get(field_key)
        if field_val:
            try:
                data_set[field_key] = data_type(field_val) # int("strs")
            except ValueError as e:
                self.response_msg('error', 'InvalidField', "The field [%s]'s data type is invalid, the correct data type should be [%s] " % (
                                      field_key, data_type))
        elif required == True:
            self.response_msg('error', 'LackOfField', "The field [%s] has no value provided in your reporting data [%s]" % (
                                  field_key, data_set))