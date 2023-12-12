import configparser
import binascii
from pyDes import des, CBC, PAD_PKCS5


class ConfigEncryptAK(object):
    def __init__(self, secret_key, config_path):
        # 密钥
        self.secret_key = secret_key
        # 配置文件地址
        self.config_path = config_path

    def main(self):
        self.file_config_check()

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


if __name__ == '__main__':
    cf = ConfigEncryptAK('yunshenq', 'config.ini')
    cf.main()
