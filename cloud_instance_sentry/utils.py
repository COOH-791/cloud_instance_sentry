# -*- coding: utf-8 -*-
import json
from dingtalkchatbot.chatbot import DingtalkChatbot
from alibabacloud_bssopenapi20171214.client import Client as BssOpenApi20171214Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bssopenapi20171214 import models as bss_open_api_20171214_models
from alibabacloud_cas20200407.client import Client as cas20200407Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_cas20200407 import models as cas_20200407_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

# 配置类
import configparser
import binascii
import requests
from pyDes import des, CBC, PAD_PKCS5


class OpenAPIAdmin(object):
    """
    阿里云提供的 OpenAPI 接口调用
    """

    def __init__(self, access_key_id, access_key_secret):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    def create_client(self):
        """
        使用AK&SK初始化账号Client
        """
        config = open_api_models.Config(
            # 您的AccessKey ID,
            access_key_id=self.access_key_id,
            # 您的AccessKey Secret,
            access_key_secret=self.access_key_secret
        )
        # 访问的域名
        config.endpoint = 'business.aliyuncs.com'
        return BssOpenApi20171214Client(config)

    def get_instance_list(self):
        """
        获取所有正常状态的实例列表
        :return: 实例列表，类型是 LIST(Dict)
        字典内容样例：
        {
        'CreateTime': '2018-04-19T10:17:00Z', # 创建时间
        'EndTime': '2025-04-19T16:00:00Z', # 到期时间
        'InstanceID': 'rm-wqeqweqweqwe', # 实例 ID
        'OwnerId': 121212121212,
        'ProductCode': 'rds',
        'ProductType': 'rds', # 实例类型
        'Region': 'cn-hangzhou',  # 地域
        'RenewStatus': 'ManualRenewal',
        'RenewalDuration': 12,
        'RenewalDurationUnit': 'M',
        'Seller': '26842',
        'Status': 'Normal',
        'SubStatus': 'Normal',
        'SubscriptionType': 'Subscription' # 付费方式
        }
        """
        client = self.create_client()

        page_num = 1
        instance_info = list()

        while True:
            query_available_instances_request = bss_open_api_20171214_models.QueryAvailableInstancesRequest(
                page_size=20,
                page_num=page_num
            )

            # 数据清洗
            response_data = str(client.query_available_instances(query_available_instances_request)).replace('\'',
                                                                                                             '\"').replace(
                'True', '\"True\"')

            # 以列表内嵌字典格式返回数据
            dict_data = json.loads(response_data).get('body').get('Data').get('InstanceList')

            # 没拉到数据，说明到底了
            if len(dict_data) == 0:
                break

            # 列表合并
            # instance_info.extend(dict_data)
            for i in dict_data:
                # 过滤一下 oss 没有 end time
                if i['ProductCode'] == 'oss':
                    continue

                instance_info.append(i)

            page_num += 1

        return instance_info

    def get_available_amount(self):
        """
        接口返回值
        {
        'AvailableAmount': '148,537.51', # 可用额度
        'AvailableCashAmount': '0.00', # 现金余额
        'CreditAmount': '150,000.00', # 信控余额
         'Currency': 'CNY', # 币种
         'MybankCreditAmount': '0.00' # 网商银行信用额度。
         }
        """
        client = self.create_client()

        runtime = util_models.RuntimeOptions()
        try:
            response_data = str(client.query_account_balance_with_options(runtime)).replace('\'',
                                                                                            '\"').replace('True',
                                                                                                          '\"True\"')
            dict_data = json.loads(response_data).get('body').get('Data')
            return dict_data
        except Exception as error:
            return {'AvailableAmount': 'error'}


class ConfigEncryptAK(object):
    def __init__(self, secret_key, config_path):
        # 密钥
        self.secret_key = secret_key
        # 配置文件地址
        self.config_path = config_path

    def file_config_check(self):
        """
        检查配置文件，对没有加密对 AK 进行加密
        """
        config = configparser.ConfigParser()

        config.read(self.config_path, encoding='utf-8')

        # 遍历 section
        for section_name in config.sections():
            if section_name == 'global-config':
                continue

            # 判断配置中的 AK 是否被加密过
            tm_k = config[section_name]['access_key']
            tm_s = config[section_name]['access_key_secret']

            # B_ 开头表示加密过了
            if tm_k[0:2] == 'B_':
                continue
            else:
                config[section_name]['access_key'] = 'B_' + self.des_encrypt(tm_k)
                config[section_name]['access_key_secret'] = 'B_' + self.des_encrypt(tm_s)

                with open(self.config_path, 'w') as configfile:
                    config.write(configfile)

    def des_encrypt(self, passwd):
        secret_key = self.secret_key
        iv = secret_key
        des_obj = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        secret_bytes = des_obj.encrypt(passwd, padmode=PAD_PKCS5)
        return binascii.b2a_hex(secret_bytes).decode('utf-8')

    def des_decipher(self, passwd):
        secret_key = self.secret_key
        iv = secret_key
        des_obj = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        decrypt_str = des_obj.decrypt(binascii.a2b_hex(passwd[2:]), padmode=PAD_PKCS5)
        return decrypt_str.decode('utf-8')


def send_ding(content, user_webhook):
    header = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }

    message = {

        "msgtype": "markdown",
        "markdown": {
            "title": 'Cloud Sentry',
            "text": content
        },
        "at": {
            "isAtAll": False
        }
    }

    message_json = json.dumps(message)
    info = requests.post(url=user_webhook, data=message_json, headers=header)
    return str(info.text)


def send_feishu(content, user_webhook):
    """
    发送飞书通知方法
    :param content: 消息内容
    :param webhook: 群 token
    :return:
    """
    # webhook：飞书群地址url
    webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/63856c7d-45c0-43c8-96db-c1f3fb5aafa1"
    # headers: 请求头
    headers = {'Content-Type': 'application/json'}

    # alert_headers: 告警消息标题
    alert_headers = "飞书测试"
    # alert_content: 告警消息内容，用户可根据自身业务内容，定义告警内容
    alert_content = content
    # message_body: 请求信息主体
    message_body = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": alert_content,

                }
            ],
            "header": {
                "template": "red",
                "title": {
                    "content": alert_headers,
                    "tag": "plain_text"
                }
            }
        }}
    response = requests.request("POST", webhook, headers=headers, data=json.dumps(message_body))
    print(response.text)
    return str(response.text)


def send_message(content, user_webhook):
    if user_webhook.find('dingtalk') != -1:
        rs = send_ding(content, user_webhook)
        return rs
    elif user_webhook.find('feishu') != -1:
        rs = send_feishu(content, user_webhook)
        return rs


if __name__ == '__main__':
    openapi = OpenAPIAdmin('ak', 'ak')
    # print(openapi.get_available_amount())
    instance_data = openapi.get_instance_list()
