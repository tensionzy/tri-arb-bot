import os
from dotenv import load_dotenv
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models


class SmsSender:
    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str = 'cn-hangzhou'):
        """
        初始化 SmsSender 类，设置阿里云的 AccessKey 和区域。

        :param access_key_id: 阿里云 AccessKey ID
        :param access_key_secret: 阿里云 AccessKey Secret
        :param region_id: 地区 ID，默认值为 'cn-hangzhou'
        """
        self.client = self.create_client(access_key_id, access_key_secret, region_id)

    @staticmethod
    def create_client(access_key_id: str, access_key_secret: str, region_id: str) -> Dysmsapi20170525Client:
        """
        创建并返回阿里云短信服务的客户端。

        :param access_key_id: 阿里云 AccessKey ID
        :param access_key_secret: 阿里云 AccessKey Secret
        :param region_id: 地区 ID
        :return: 阿里云短信服务客户端
        """
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        config.endpoint = f'dysmsapi.aliyuncs.com'
        return Dysmsapi20170525Client(config)

    def send_sms(self, phone_number: str, sign_name: str, template_code: str, template_param: str) -> bool:
        """
        发送短信到指定的电话号码。

        :param phone_number: 接收短信的电话号码
        :param sign_name: 短信签名
        :param template_code: 短信模板代码
        :param template_param: 短信模板参数，JSON 字符串
        :return: 成功返回 True，否则返回 False
        """
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name=sign_name,
            template_code=template_code,
            phone_numbers=phone_number,
            template_param=template_param
        )
        runtime = util_models.RuntimeOptions()
        try:
            response = self.client.send_sms_with_options(send_sms_request, runtime)
            print("短信发送成功:", response.body)
            return True
        except Exception as error:
            print("短信发送失败:", error.message)
            if hasattr(error, 'data'):
                print("诊断地址:", error.data.get("Recommend"))
            return False


if __name__ == '__main__':
    load_dotenv()
    smsSender = SmsSender(access_key_id=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
                          access_key_secret=os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET'))
    smsSender.send_sms(phone_number='15998488863', sign_name='joey的短信提醒', template_code='SMS_472065257',
                       template_param='{"code":"1234"}')
