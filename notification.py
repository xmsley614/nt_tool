#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Use wxpusher/smabao to send notifications to phone.
"""
import hashlib
import urllib
import urllib.request

import requests

import config

####### wxpusher #######

BASEURL = "http://wxpusher.zjiecode.com/api"


class WxPusherException(Exception):
    """WxPusher specific base exception."""


class WxPusherNoneTokenException(WxPusherException):
    """Raised when both token and default token are None."""


class WxPusher:
    """WxPusher Python SDK."""

    default_token = None

    @classmethod
    def send_message(cls, content, **kwargs):
        """Send Message."""
        payload = {
            "appToken": cls._get_token(kwargs.get("token")),
            "content": content,
            "summary": kwargs.get("summary"),
            "contentType": kwargs.get("content_type", 1),
            "topicIds": kwargs.get("topic_ids", []),
            "uids": kwargs.get("uids", []),
            "url": kwargs.get("url"),
            "verifyPay": kwargs.get("verifyPay", False),
        }
        url = f"{BASEURL}/send/message"
        return requests.post(url, json=payload).json()

    @classmethod
    def query_message(cls, message_id):
        """Query message status."""
        url = f"{BASEURL}/send/query/{message_id}"
        return requests.get(url).json()

    @classmethod
    def create_qrcode(cls, extra, valid_time=1800, token=None):
        """Create qrcode with extra callback information."""
        payload = {
            "appToken": cls._get_token(token),
            "extra": extra,
            "validTime": valid_time,
        }
        url = f"{BASEURL}/fun/create/qrcode"
        return requests.post(url, json=payload).json()

    @classmethod
    def query_user(cls, page, page_size, token=None):
        """Query users."""
        payload = {
            "appToken": cls._get_token(token),
            "page": page,
            "pageSize": page_size,
        }
        url = f"{BASEURL}/fun/wxuser"
        return requests.get(url, params=payload).json()

    @classmethod
    def _get_token(cls, token=None):
        """Get token with validation."""
        token = token or cls.default_token
        if not token:
            raise WxPusherNoneTokenException()
        return token


####### smsbao #######
SMSAPI = "http://api.smsbao.com/"

statusStr = {
    "0": "短信发送成功",
    "-1": "参数不全",
    "-2": "服务器空间不支持,请确认支持curl或者fsocket,联系您的空间商解决或者更换空间",
    "30": "密码错误",
    "40": "账号不存在",
    "41": "余额不足",
    "42": "账户已过期",
    "43": "IP地址限制",
    "50": "内容含有敏感词",
}


def md5(str):
    m = hashlib.md5()
    m.update(str.encode("utf8"))
    return m.hexdigest()


def send_sms(phone, content):
    """send short message to phone

    :phone: 13712345678
    :content: message content

    """
    data = urllib.parse.urlencode(
        {"u": config.USER, "p": config.PASSWORD, "m": phone, "c": content}
    )
    send_url = SMSAPI + "sms?" + data
    response = urllib.request.urlopen(send_url)
    the_page = response.read().decode("utf-8")
    print(statusStr[the_page])


if __name__ == "__main__":
    # Wechat
    wxp = WxPusher()
    wxp.send_message(
        "message content",
        token=config.TOKEN,
        summary="abstract",
        topic_ids=config.TOPIC_IDS,
        uids=config.UIDS,
        #  verifyPay=True,
    )
    # SMS
    for phone in config.PHONE_NUMS:
        send_sms(phone, "message content")
