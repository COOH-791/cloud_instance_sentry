# -*- coding: utf-8 -*-
import json
import requests


def send_feishu(user_webhook):
    """
    发送飞书通知方法
    :param content: 消息内容
    :param webhook: 群 token
    :return:
    """
    payload_message = {
        "elements": [
            {
                "tag": "markdown",
                "content": "## 测试告警\n**这是一条简单的测试**\n>测试"
            }
        ]
    }

    header = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }

    message_json = json.dumps(payload_message)
    info = requests.post(url=user_webhook, data=message_json, headers=header)

    response_code = json.loads(info.content)
    return str(response_code)


print(send_feishu('https://open.feishu.cn/open-apis/bot/v2/hook/63856c7d-45c0-43c8-96db-c1f3fb5aafa1'))
