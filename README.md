# cloud_instance_sentry

基于 AliCloud 提供的 OpenAPI 实现的一个云资源到期实例提醒 Bot。

## 1. 用途

说到云资源续费，公认不移，是一件几乎不可能出错的事情，根据 “墨菲定律” 如果事情有变坏的可能，不管概率多小，总会发生。

实际工作中还是遇到不少因为云资源到期未续费造成的服务中断情况，所以编写该程序，通过定期巡检避免此类问题发生。

* 支持对称加密用户填写到配置文件中的 AK 信息。
* 支持多个 AK 账号巡检。
* 支持云账号额度巡检。
* 支持全局配置。
* 支持将巡检报告发送到钉钉 & 飞书。

## 2. 项目状态

正常维护，应用于公司部分线上环境。

* 已测试环境
  * Python 3.7
  * CentOS Linux release 7.9.2009 (Core)

## 3. 环境准备

### 3.1 Python 安装

程序基于 Python3 研发，如果系统中没有 Python3 可使用下面方式安装：

```sh
# 下载 Python 源码
wget "https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tar.xz"
# 解压
tar -xvJf Python-3.7.3.tar.xz
# 编译
cd Python-3.7.3
./configure prefix=/usr/local/python3 
make && make install 
ln -fs /usr/local/python3/bin/python3 /usr/bin/python3 
ln -fs /usr/local/python3/bin/pip3 /usr/bin/pip3
```

测试：

```sh
python3 --version
pip3 --version
```

### 3.2 代码依赖安装

下载源代码：

```sh
# 下载源码
wget https://github.com/COOH-791/cloud_instance_sentry/archive/refs/heads/main.zip
# 解压
unzip cloud_instance_sentry-main.zip
# 进入代码
cd cloud_instance_sentry-main/
```

在项目路径中，创建虚拟环境：

```sh
# 创建虚拟环境文件夹
mkdir venv
cd venv
# 创建虚拟环境
python3 -m venv .
# bin  include  lib  lib64  pyvenv.cf
# 激活环境
source ./bin/activate
```

安装依赖模块：

```sh
# 更新 pip
pip3 install --upgrade pip
```

```sh
# 进入代码 requirements.txt 文件目录，执行依赖模块安装
pip3 install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt
# 该模块需要单独安装
pip3 install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com alibabacloud_cas20200407==1.0.13
```

退出当前虚拟环境：

```sh
deactivate
```

## 4. 使用案例

本小节，会介绍代码如何配置以及执行流程。

### 4.1 配置文件介绍

以下是脱敏的测试配置文件，通过它向大家介绍各项配置的含义。

```ini
[global-config]
# 实例过期天数阈值
global_overdue_day = 15
# 费用阈值
global_amount_threshold = 1000000
# webhook
global_webhook = https://oapi.dingtalk.com/robot/send?access_token=39c437db9d6f217b1cedad7012c8f
# 最大显示多少个实例
max_list_length = 10
# 心跳检测
ping = on
# 是否隐藏余额，on 隐藏 off 不隐藏
global_amount_invisible = off

[test01]
username = 测试用户1
access_key = B_c31f34addb5f08f365b322dd199f92092b34142e64e
access_key_secret = B_2344bfd8236ea936d38c7e3474841f033fa9
amount_threshold = 10000
overdue_day = 10

[test02]
username = 测试用户2
access_key = B_c31f34addb5f08f365b322dd199f92092b34142e64e
access_key_secret = B_2344bfd8236ea936d38c7e3474841f033fa9
```

该程序支持巡检多个 AK 账号，配置文件由两部分组成，分别是 **全局配置** 和 **用户配置**，其中全局配置是必需要配置的，用户配置是指每个 AK 的信息配置，有多个 AK 就有多少个用户配置。

**全局配置 [global-config]：**

* global_overdue_day：全局实例过期天数阈值，如果用户配置中，没有设置 `overdue_day` 过期天数阈值，那么会以全局配置中该值为准。
* global_amount_threshold：全局费用阈值，如果用户配置中，没有设置 `amount_threshold` 余额阈值，那么会以全局配置中该值为准。
* global_webhook：通知群的 webhook ，如果用户配置中，没有设置 `webhook` 群通知 token，那么会以全局配置中该值为准。
* max_list_length：如果过期实例非常多的话，发送出来的卡片会非常长，而且超出限制消息会发送失败，该参数用来配置，过期实例列表的最大长度。
* ping：设置为 off 的话，如果当天巡检没有发现即将过期的实例，那么不会发送任何消息，设置为 on 的话，既使没有巡检出过期实例，也会向用户发送一个通知，相当于一个心跳检测，告诉用户程序正常运行。
* global_amount_invisible：程序会采集余额，但是有些用户对余额比较敏感，不想让余额展示出来，可通过设置该参数。如果用户配置中，没有设置 amount_invisible 参数，那么会以全局配置中该值为准。

**用户配置 [用户名]：**

如上面的演示，[test01] 和 [test02] 这两部分为用户配置，其中 section name 由用户自由设置（支持英文和下划线）有多少个 AK 配置多少个 section 即可。

因为有全局配置的存在，用户配置中，只有 3 个配置项是必需要设置的：

* username：用户名。
* access_key：AK。
* access_key_secret：AK 密钥。

可选配置，如果配置了，将优先以用户配置为准：

* webhook：通知的群 webhook。
* amount_threshold：费用阈值。
* overdue_day：过期天数阈值。
* amount_invisible：是否隐藏余额，on 隐藏 off 不隐藏。

**关于飞书通知和钉钉通知：**

程序会通过关键字自动判断用户提供的 webhook 是钉钉还是飞书的，所以用户直需要创建好机器人，将 webhook URL 写到配置文件中即可。

机器人配置的关键字：巡检

### 4.2 启动巡检

编写完配置文件后，使用刚才创建的虚拟环境 Python3 启动程序：

```sh
/code/cloud_instance_sentry-main/venv/bin/python3 patrol_cloud_sentry.py
```

正常情况下，配置的群里，将会收到如下信息：

>**实例类型**：rds

>**实例 ID**：rm-bp129dqwdqwdl58p 

>**剩余天数**：<font color=#FF0000>**7**</font>

 >**到期时间**：2023-12-16

****
>**实例类型**：rds

>**实例 ID**：rm-bp1dwqdwq1e1j4 

>**剩余天数**：<font color=#FF0000>**7**</font>

 >**到期时间**：2023-12-16

****
>**实例类型**：rds

>**实例 ID**：rm-bp1wqdqwdm9p16 

>**剩余天数**：<font color=#FF0000>**7**</font>

 >**到期时间**：2023-12-16

****
**您有 <font color=#FF0000>161</font> 个资源将在 <font color=#FF0000>15</font> 天内到期，未设置自动续费：**

>**rds** (19)  ,**ons** (1)  ,**ecs** (127)  ,**sas** (1)  ,**pconn** (2)  ,**dds** (2)  ,**redisa** (6)  ,**mpsoftware-mt9-dt41** (1)  ,**hdm** (1)  ,**dts** (1)  

当前账户余额：**<font color=#228B22>2,672,769.60 ¥**</font>

程序默认会读取当前目录下的配置文件 `./config.ini` 如需更换配置文件，可使用 -f='配置文件路径'。

测试无异常后，可配置定时任务，例如每天 09:30 进行过期实例巡检：

```sh
30 09 * * * /code/cloud_instance_sentry-main/venv/bin/python3 /code/cloud_instance_sentry-main/cloud_instance_sentry/patrol_cloud_sentry.py -f=/opt/cloud_instance_sentry-main/cloud_instance_sentry/pord_config.ini
```

注意，定时任务中的配置文件需要写绝对路径。

### 4.3 程序流程

程序的执行流程如下：

1. 读取配置文件，会进行判断用户配置中的 AK 信息是否已经加密，如果没有加密将使用对称加密针对 AK 信息加密。
2. 使用 AK 调用阿里云 OpenAPI 拉取实例列表。
3. 根据列表和用户提供的阈值，组织消息列表。
4. 调用消息通知模块，发送巡检结果。

## 5. 后记

有任何问题，请与我联系。邮箱：[huabing8023@126.com](https://github.com/COOH-791/mysql_clone_backup/tree/main)

欢迎提问题提需求，欢迎 Pull Requests！

