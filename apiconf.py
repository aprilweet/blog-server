# coding=utf-8

WX_APP_ID = "{wx_miniapp_id}"
WX_APP_SECRET = "{wx_miniapp_secret}"
CODE_2_SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"

JSON_AS_ASCII = False
SECRET_KEY = "{random for cookie}"

SESSION_TYPE = "sqlalchemy"
SESSION_SQLALCHEMY_TABLE = "session"
SQLALCHEMY_DATABASE_URI = "sqlite:///data/blog.sqlite"
SQLALCHEMY_TRACK_MODIFICATIONS = False

USE_X_SENDFILE = True
XACCEL_REDIRECT_BASE = "/xaccel"
