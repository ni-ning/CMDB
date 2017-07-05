#!/usr/bin/env python3
# -*-coding:utf-8 -*-
# __author__:Jonathan
# email:nining1314@gmail.com
import json
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from asset import models
from logs.log import log_handler


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
                    response = {'asset_id': self.asset_obj.id,}
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

    # 初次向审核信息表写记录函数块
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

    # 初次向资产总表写记录函数块
    def data_inject(self):
        # 完整资产创建和更新
        if self.__is_new_asset():
            # 完整新资产，如服务器表中有对应记录
            print("新资产，即将创建...")
            self.create_asset()
        else:
            # 不是完整新增产，如服务器表中无对应记录
            print("旧资产，即将更新...")
            self.update_asset()

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
            if not len(self.response['error']) or ignore_errs  == True:
                data_set = {
                    'asset_id': self.asset_obj.id,
                    'raid_type': self.clean_data.get('raid_type'),
                    'model': self.clean_data.get('model'),
                    'os_type': self.clean_data.get('os_type'),
                    'os_distribution': self.clean_data.get('os_distribution'),
                    'os_release': self.clean_data.get('os_release'),}
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

    #  更新资产记录相关函数块
    #  self.data_inject()包含更新功能
    def data_is_valid(self):
        data = self.request.POST.get("asset_data")
        if data:
            try:
                data = json.loads(data)
                self.mandatory_check(data)
                self.clean_data = data
                # print(self.clean_data)
                if not self.response['error']:
                    return True
            except ValueError as e:
                self.response_msg('error', 'AssetDataInvalid', str(e))
        else:
            self.response_msg('error', 'AssetDataInvalid', "The reported asset data is not valid or provided")

    def update_asset(self):
        func = getattr(self, '_update_%s' % self.clean_data['asset_type'])
        update_obj = func()

    def _update_server(self):

        self.__update_cpu_component()
        self.__update_server_component()

        self.__update_asset_component(data_source=self.clean_data['nic'],
                                      fk='nic_set',
                                      update_fields=['name', 'sn', 'model', 'macaddress', 'ipaddress', 'netmask',
                                                           'bonding'],
                                      identify_field='macaddress')

        self.__update_asset_component(data_source=self.clean_data['physical_disk_driver'],
                                             fk='disk_set',
                                             update_fields=['slot', 'sn', 'model', 'manufactory', 'capacity',
                                                            'iface_type'],
                                             identify_field='slot'
                                             )
        self.__update_asset_component(data_source=self.clean_data['ram'],
                                            fk='ram_set',
                                            update_fields=['slot', 'sn', 'model', 'capacity'],
                                            identify_field='slot'
                                            )

    def __update_cpu_component(self):
        """
        1. 定义更新时需比对的字段
        2. 判断资产字表是否存在
            - 不存在，新增资产字表记录
            - 存在，进行比对更新
        """
        update_fields = ['cpu_model', 'cpu_count', 'cpu_core_count']
        if hasattr(self.asset_obj, 'cpu'):
            self.__compare_componet(model_obj=self.asset_obj.cpu, fields_from_db=update_fields, data_source=self.clean_data)
        else:
            self.__create_cpu_component(ignore_errs=True)

    def __update_server_component(self):
        update_fields = ['model', 'raid_type', 'os_type', 'os_distribution', 'os_release']
        if hasattr(self.asset_obj, 'server'):
            self.__compare_componet(model_obj=self.asset_obj.server,
                                    fields_from_db=update_fields,
                                    data_source=self.clean_data)
        else:
            self.__create_server_info(ignore_errs=True)

    def __compare_componet(self, model_obj, fields_from_db, data_source):
        """
        model_obj == 数据库中资产记录对象，如CPU中的cpu对象
        fields_from_db == 要比较的字段 ，如CPU中的['cpu_model', 'cpu_count', 'cpu_core_count']
        data_source == 客户端搜索的数据，如self.clean_data
        """
        print('---即将比较：[%s]' % model_obj, fields_from_db)
        print('---数据来源：%s' % data_source)

        for field in fields_from_db:
            """
            1. 取出双方的字段值
            2. 统一数据类型
            3. 比较
            4. 根据比较的结果，确定是否更新数据库
            """

            # 1. 取出双方的字段值
            val_from_db = getattr(model_obj, field)
            val_from_data_source = data_source.get(field)
            # 2. 统一数据类型
            if val_from_data_source:
                if type(val_from_db) is int:
                    val_from_data_source = int(val_from_data_source)
                elif type(val_from_db) is float:
                    val_from_data_source = float(val_from_data_source)
                elif type(val_from_db) is str:
                    val_from_data_source = str(val_from_data_source).strip()

                # 3. 比较
                if val_from_db == val_from_data_source:
                    pass
                else:
                    # 4. 根据比较的结果，确定是否更新数据库
                    print('val_from_db[%s]  != val_from_data_source[%s]' % (val_from_db, val_from_data_source),
                          type(val_from_db),
                          type(val_from_data_source),
                          field)

                    db_field = model_obj._meta.get_field(field)
                    db_field.save_form_data(model_obj, val_from_data_source)
                    model_obj.update_date = timezone.now()
                    model_obj.save()

                    log_msg = "Asset[%s] -> component[%s] -> field[%s]值 从[%s] 更新为 [%s]" % (
                        self.asset_obj, model_obj, field, val_from_db, val_from_data_source
                    )
                    self.response_msg('info', 'FieldChanged', log_msg)
                    log_handler(self.asset_obj, 'FieldChanged', self.request.user, log_msg, model_obj)

            else:
                self.response_msg('warning', 'AssetUpdateWarning',
                                  "Asset component [%s]'s field [%s] is not provided in reporting data " % (
                                      model_obj, field))
        model_obj.save()

    def __update_asset_component(self, data_source, fk, update_fields, identify_field=None):
        print(data_source, update_fields, identify_field)
        """
        1. data_source 客户端数据，如self.clean_data['nic']
        2. fk 外键，找到项目子资产与总资产之间的关系，如'nic_set',
            component_obj = getattr(self.asset_obj, 'nic_set')
            component_obj.all() # 所有网卡信息QuerySet
        3. update_fields,数据库中用来比对和更新的字段，如['name', 'sn', 'model', 'macaddress', 'ipaddress', 'netmask',
                                                           'bonding']
        4. identify_field，用来标识子资产的关键字段
        """
        try:
            component_obj = getattr(self.asset_obj, fk)
            if hasattr(self.asset_obj, fk):
                objects_from_db = component_obj.all()  # [nic_obj1, nic_obj2, nic_obj3...]
                for obj in objects_from_db:
                    """
                    1. 循环得到网卡一条记录对象 obj
                    2. 根据关键字段 macaddress获取这个obj相应关键字段值 key_field_data
                    3. 根据 key_field_data 再去客户端采集的数据中，找到对应mac值的字典数据
                    4. 库表记录和客户端数据字典进行比较self.__compare_componet
                    """
                    key_field_data = getattr(obj, identify_field)  # 库表已存在的 00-50-56-C0-00-08

                    for source_data_item in data_source:
                        key_field_data_from_source_data = source_data_item.get(identify_field)
                        if key_field_data_from_source_data is not None:

                            if type(key_field_data) is int:
                                key_field_data_from_source_data = int(key_field_data_from_source_data)
                            elif type(key_field_data) is float:
                                key_field_data_from_source_data = float(key_field_data_from_source_data)
                            elif type(key_field_data) is str:
                                key_field_data_from_source_data = str(key_field_data_from_source_data)

                            if key_field_data == key_field_data_from_source_data:  # 规则3
                                self.__compare_componet(model_obj=obj, fields_from_db=update_fields,
                                                        data_source=source_data_item)
                                break
                        else: # 代表数据源里连mac的值都没有
                            self.response_msg('warning', 'AssetUpdateWarning',
                                              "Asset component [%s]'s key field [%s] is not provided in reporting data " % (
                                                  fk, identify_field))
                    else:
                        # for...else  for循环正常执行结束后会执行else语句，但是break后就不执行了
                        # 在数据源，根据 key_field_data，找到不到对应值
                        print('Error:cannot find any matches in source data by using key field val [%s],component data is missing in reporting data!' %
                              (key_field_data))
                        self.response_msg("error", "AssetUpdateWarning",
                                          "Cannot find any matches in source data by using key field val [%s],component data is missing in reporting data!" % (
                                              key_field_data))

                # 只在库表里存在的记录，或只在数据源里存在的记录处理流程
                # 只在库表里存在的记录 - 删除
                # 只在数据源里存在的记录 - 添加
                self.__filter_add_or_deleted_components(model_obj_name=component_obj.model._meta.object_name,
                                                        data_from_db=objects_from_db,
                                                        data_source=data_source,
                                                        identify_field=identify_field)
            else:
                pass
        except Exception as e:
            print(str(e))

    def __filter_add_or_deleted_components(self, model_obj_name, data_from_db, data_source, identify_field):
        """
        1. model_obj_name: NIC, 用于.....
        2. data_from_db: 库表所有记录，QuerySet格式
        3. data_source：数据源所有记录，[{key1:value1},{key2:value2},{key3:value3},]
        4. identify_field：标识key，macaddress
        """
        print(model_obj_name)
        print(data_from_db)
        print(data_source)
        print(identify_field)

        data_source_key_list = [] # 用来存储客户端标识key的值，[macaddress1, macaddress2,macaddress3]
        for data in data_source:
            data_source_key_list.append(data.get(identify_field))

        temp_list = [getattr(obj, identify_field) for obj in data_from_db]  # 列表生产式***
        if temp_list:
            # 类型转换
            if type(temp_list[0]) == int:
                data_source_key_list = [int(i) for i in data_source_key_list]
            elif type(temp_list[0]) == str:
                data_source_key_list = [str(i) for i in data_source_key_list]
            elif type(temp_list[0]) == float:
                data_source_key_list = [float(i) for i in data_source_key_list]

            print('-->客户端标识数据列表：', data_source_key_list)
            print('-->库表标识数据列表：', [getattr(obj, identify_field) for obj in data_from_db])

        # 集合形式 -> 集合运算
        data_source_key_list = set(data_source_key_list)
        data_identify_val_from_db = set([getattr(obj, identify_field) for obj in data_from_db])

        data_only_in_db = data_identify_val_from_db - data_source_key_list  # 需删除
        data_only_in_data_source = data_source_key_list - data_identify_val_from_db  # 需添加

        print('只在库表里存在的记录标识: ', data_only_in_db)
        print('只在数据源里存在的记录标识: ', data_only_in_data_source)

        if data_only_in_db:
            self.__delete_components(all_components=data_from_db,
                                     delete_list=data_only_in_db,
                                     identify_field=identify_field)

        if data_only_in_data_source:
            print('开始新增数据................')
            self.__add_components(model_obj_name=model_obj_name,
                                  all_components=data_source,
                                  add_list=data_only_in_data_source,
                                  identify_field=identify_field)

    def __add_components(self, model_obj_name, all_components, add_list, identify_field):
        """
        1. model_obj_name: NIC
        2. all_components: 用户端采集所有数据集
        3. add_list：需要添加数据集合 {'B6:6D:83:99:9D:5A'}
        4. identify_field： 标识key  macaddress
        """
        print(model_obj_name)
        print(all_components)
        print(add_list)
        print(identify_field)

        model_class = getattr(models, model_obj_name)

        will_be_creating_list = []  # 需要创建的记录列表，元素为字典
        for data in all_components:
            if data[identify_field] in add_list:
                will_be_creating_list.append(data)

        try:
            for component in will_be_creating_list:
                data_dict = {}
                for field in model_class.auto_create_fields:
                    data_dict[field] = component.get(field)
                data_dict['asset_id'] = self.asset_obj.id
                obj = model_class(**data_dict)
                obj.save()
                print('创建新资产，数据来源:', data_dict)
                log_msg = "Asset[%s] --> component[%s] has just added a new item [%s]" % (
                    self.asset_obj, model_obj_name, data_dict)
                self.response_msg('info', 'NewComponentAdded', log_msg)
                log_handler(self.asset_obj, 'NewComponentAdded', self.request.user, log_msg, model_obj_name)

        except Exception as e:
            log_msg = "Asset[%s] --> component[%s] has error: %s" % (self.asset_obj, model_obj_name, str(e))
            self.response_msg('error', "AddingComponentException", log_msg)

    def __delete_components(self, all_components, delete_list, identify_field):
        '''
        1. all_components:  库表所有记录，QuerySet格式
        2. delete_list:     需要删除数据集合 {'B6:6D:83:99:9D:5B'}
        3. identify_field： 标识key  macaddress
        '''
        print(all_components)
        print(delete_list)
        print(identify_field)

        deleting_obj_list = []
        for obj in all_components:
            val = getattr(obj, identify_field)
            if val in delete_list:
                deleting_obj_list.append(obj)

        for i in deleting_obj_list:
            log_msg = "Asset[%s] --> component[%s] --> is lacking from reporting source data, assume it has been removed or replaced,will also delete it from DB" % (
                self.asset_obj, i)
            self.response_msg('info', 'HardwareChanges', log_msg)
            log_handler(self.asset_obj, 'HardwareChanges', self.request.user, log_msg, i)
            i.delete()