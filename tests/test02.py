import requests
import json


def post_to_robot():
    # https://open.feishu.cn/document/common-capabilities/message-card/message-cards-content/using-markdown-tags
    # webhook：飞书群地址url
    webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/63856c7d-45c0-43c8-96db-c1f3fb5aafa1"
    # headers: 请求头
    headers = {'Content-Type': 'application/json'}

    # alert_headers: 告警消息标题
    alert_headers = "飞书测试"
    # alert_content: 告警消息内容，用户可根据自身业务内容，定义告警内容
    alert_content = "普通文本\n标准emoji😁😢🌞💼🏆❌✅\n*斜体*\n**粗体**\n~~删除线~~\n[文字链接](www.example.com)\n[差异化跳转]($urlVal)\n<at id=all></at>"
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


post_to_robot()
