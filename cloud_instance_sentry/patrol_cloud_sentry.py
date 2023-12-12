# -*- coding: utf-8 -*-
import os
import sys
import json
import datetime
import time
import configparser
import argparse
import logging

# 引用工具类
from utils import OpenAPIAdmin, ConfigEncryptAK, send_message

logging.basicConfig(filename='./error.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class CloudPatrolReport(object):
    def __init__(self, config_path):
        # 配置文件目录
        self.config_path = config_path
        # 密钥
        self.secret_key = 'yunshenq'
        # 加载全局配置文件：全局过期阈值、全局费用阈值、全局 webhook、最大列表长度、是否启用 ping
        self.g_overdue_day, self.g_available_amount, self.g_webhook, self.max_list_length, \
        self.ping, self.amount_invisible = self.load_global_config()

        # 加载用户配置文件
        self.user_config_list = self.load_user_config_data()

    def main(self):
        # 消息列表长度，最大不能超过 20
        if int(self.max_list_length) > 20:
            self.max_list_length = 20

        # 调用搜索即将过期实例
        self.find_overdue_instance()

    def find_overdue_instance(self):
        """
        找出即将到期的实例，如果开启自动付费，那么拉出来的到期时间是 2999-09-09
        程序在时间判断方面，使用了冗余计算，如果小于 3 天，建议尽快续费
        """
        # 外部循环的是 AK 列表用户
        for user_ini in self.user_config_list:
            # 调用 OpenAPI 对象
            api_obj = OpenAPIAdmin(user_ini['access_key'], user_ini['access_key_secret'])
            # 获得实例列表
            instance_data = api_obj.get_instance_list()

            # 当前用户的账户余额
            user_ini['available_amount'] = api_obj.get_available_amount()['AvailableAmount']

            # 初始化一个列表存储结果
            overdue_day_instance = list()

            # 该层循环的是实例列表
            for instance_df in instance_data:
                # 有部分实例类型，没有过期天数，例如 OSS
                if instance_df.get('EndTime') is not None:
                    # 调用时间差值计算
                    remainder_second, end_time = self.calculate_time_lag(instance_df.get('EndTime'))
                    # 过滤出即将到期的实例
                    if remainder_second > 0 and (remainder_second // 86400) < int(user_ini['overdue_day']) + 2:
                        # 组织消息
                        overdue_day_instance.append(
                            {
                                '用户名': user_ini['username'],
                                '实例ID': instance_df.get('InstanceID'),
                                '实例类型': instance_df.get('ProductCode'),
                                '到期时间': end_time,
                                '剩余天数': int((remainder_second // 86400) - 1)
                            })

            # 组织消息，调用推送
            res = self.make_send_message(overdue_day_instance, user_ini)
            logging.info('send_message_response {0}'.format(res))

    def make_send_message(self, overdue_day_instance: list, user_init: dict):
        """
        组织通知文本
        :param overdue_day_instance: 过期实例列表
        :param user_init: 当前循环实例的元数据
        """
        # 列表长度为 0 表示没有即将到期的实例，函数结束
        if len(overdue_day_instance) == 0:
            # 如果开启 ping 发送一天通知
            if user_init['ping'] == 'on':
                content = "尊敬的{0}，本次巡检未发现小于 {1} 天到期的资源。".format(user_init['username'], user_init['overdue_day'])
                # 调用发送
                res = send_message(content, user_init['webhook'])
                logging.info('send_message_response {0}'.format(res))

            return True

        # 按照剩余天数进行排序，升序
        overdue_day_list = sorted(overdue_day_instance, key=lambda i: i['剩余天数'], reverse=False)

        # 以上是钉钉通知的模版
        content = '## 【{0} - 到期实例巡检告警】\n\n'.format(overdue_day_list[0]['用户名'])

        # 组织列表，这里可以使用分片确认消息列表的长度，由用户指定
        for i in overdue_day_list[0: int(user_init['max_list_length'])]:
            content += '>**实例类型**：{0}\n\n>**实例 ID**：{1} \n\n>{2}\n\n >**到期时间**：{3}\n\n****\n'.format(i['实例类型'],
                                                                                                     i['实例ID'],
                                                                                                     self.colour_settings(
                                                                                                         i['剩余天数']),
                                                                                                     i['到期时间'])

        # 总结性统计分析
        summary_text = self.analysis_table(overdue_day_list, user_init)

        # 调用发送
        send_message(content + summary_text, user_init['webhook'])

    def analysis_table(self, overdue_day_list: list, user_init: dict):
        """
        负责写后面一段总结的文本
        """
        # 实例类型字典
        instance_type_num = dict()

        # 实例信息
        for i in overdue_day_list:
            if i['实例类型'] in instance_type_num.keys():
                instance_type_num[i['实例类型']] += 1
            else:
                instance_type_num[i['实例类型']] = 1

        content = '**您有 <font color=#FF0000>{0}</font> 个资源将在 <font color=#FF0000>{1}</font> 天内到期，未设置自动续费：**\n\n>' \
            .format(len(overdue_day_list), user_init['overdue_day'])

        for k, v in instance_type_num.items():
            content += '**{0}** ({1})  ,'.format(k, v)

        # 删除最后一个括号
        content = content[0:-1]
        # 涉及金额计算
        content += self.user_amount_analysis(user_init)

        return content

    @staticmethod
    def user_amount_analysis(user_init):
        """
        计算余额
        """
        # 用户不想显示余额，不用计算
        if user_init['amount_invisible'] == 'on':
            return ''

        amount_content = ''

        # 先判断是否采集到余额
        if user_init['available_amount'] != 'error':
            # 判断是否大于指定阈值
            if float(user_init['available_amount'].replace(',', '')) > float(
                    user_init['amount_threshold'].replace(',', '')):
                amount_content += '\n\n当前账户余额：**<font color=#228B22>{0} ¥**</font>'.format(
                    user_init['available_amount'])
            else:
                amount_content += '\n\n当前账户余额：**<font color=#FF0000>{0} ¥**</font>'.format(
                    user_init['available_amount'])
        else:
            amount_content += '\n\n余额未采集到'

        return amount_content

    @staticmethod
    def colour_settings(overdue_day_num):
        """
        给到期天数，然后根据天数返回颜色
        :param overdue_day_num:
        :return: 颜色十六进制文本
        """

        if overdue_day_num <= 7:
            markdown_text = "**剩余天数**：<font color=#FF0000>**{0}**</font>".format(overdue_day_num)
        else:
            # 大于 7 天，黄色
            markdown_text = "**剩余天数**：<font color=#CC6633>**{0}**</font>".format(overdue_day_num)

        return markdown_text

    @staticmethod
    def calculate_time_lag(end_time):
        """
        过期时间计算
        """
        now_time = datetime.datetime.now().strftime("%Y-%m-%d")
        itime = (datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ') + datetime.timedelta(hours=8)).strftime(
            "%Y-%m-%d")

        remainder = int(time.mktime(time.strptime(itime, "%Y-%m-%d"))) - int(
            time.mktime(time.strptime(now_time, "%Y-%m-%d")))

        return remainder, itime

    def load_user_config_data(self):
        """
        获取配置信息，会排除 global 配置
        """

        # 调用加密类
        cf = ConfigEncryptAK(self.secret_key, self.config_path)
        # 对配置文件进行检查
        cf.file_config_check()

        try:
            config = configparser.ConfigParser()
            config.read(self.config_path, encoding='utf-8')

            # 初始化存储列表
            user_config = list()

            for section_name in config.sections():
                # 跳过解析全局配置
                if section_name == 'global-config':
                    continue

                # 这里解析一些配置
                ini_data = dict(config.items(section_name))

                tem_user_cof = {
                    'section_name': section_name,
                    'username': ini_data.get('username'),
                    'access_key': cf.des_decipher(ini_data.get('access_key')),
                    'access_key_secret': cf.des_decipher(ini_data.get('access_key_secret')),
                    'webhook': ini_data.get('webhook', self.g_webhook),
                    'overdue_day': ini_data.get('overdue_day', self.g_overdue_day),
                    'amount_threshold': ini_data.get('amount_threshold', self.g_available_amount),
                    'max_list_length': ini_data.get('max_list_length', self.max_list_length),
                    'ping': ini_data.get('ping', self.ping),
                    'amount_invisible': ini_data.get('amount_invisible', self.amount_invisible)
                }

                user_config.append(tem_user_cof)

            return user_config
        except Exception as e:
            logging.error('Configuration file parsing error: {}'.format(e))
            sys.exit(0)

    def load_global_config(self):
        """
        加载全局配置文件
        """
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path, encoding='utf-8')
            g_ini = dict(config.items('global-config'))
            return g_ini.get('global_overdue_day'), \
                   g_ini.get('global_amount_threshold'), \
                   g_ini.get('global_webhook'), g_ini.get('max_list_length'), g_ini.get('ping'), \
                   g_ini.get('global_amount_invisible')
        except Exception as e:
            logging.error('Configuration file parsing error: {}'.format(e))
            sys.exit(0)


if __name__ == '__main__':
    # 参数配置
    parser = argparse.ArgumentParser(description='cloud_instance_sentry __author__ = Bing')
    parser.add_argument('--config', '-f', type=str, help='configuration file directory. default ./config.ini',
                        default='./config.ini')

    args = parser.parse_args()

    if os.path.exists(args.config):
        cpr = CloudPatrolReport(args.config)
        cpr.main()
    else:
        print("ERROR：{0} The configuration file does not exist.".format(args.config))
        parser.print_help()
