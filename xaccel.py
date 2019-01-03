# coding=utf-8

from flask.helpers import safe_join
import os


class XAccel:
    redirect_base = "/xaccel"
    charset = None  # FIXME
    buffering = "yes"
    expires = "off"
    limit_rate = "off"

    def __init__(self, app):
        if "XACCEL_REDIRECT_BASE" in app.config:
            self.redirect_base = app.config["XACCEL_REDIRECT_BASE"]
        if "XACCEL_CHARSET" in app.config:
            self.charset = app.config["XACCEL_CHARSET"]
        if "XACCEL_BUFFERING" in app.config:
            self.buffering = app.config["XACCEL_BUFFERING"]
        if "XACCEL_EXPIRES" in app.config:
            self.expires = app.config["XACCEL_EXPIRES"]
        if "XACCEL_LIMIT_RATE" in app.config:
            self.limit_rate = app.config["XACCEL_LIMIT_RATE"]

        app.xaccel = self

    def __call__(self, file):
        if os.path.isabs(file):
            raise RuntimeWarning("XAccel only accepts relative file path")

        headers = {}
        if self.redirect_base:
            headers["X-Accel-Redirect"] = safe_join(self.redirect_base, file).encode("utf-8")
        if self.charset:
            headers["X-Accel-Charset"] = self.charset
        if self.buffering:
            headers["X-Accel-Buffering"] = self.buffering
        if self.expires:
            headers["X-Accel-Expires"] = self.expires
        if self.limit_rate:
            headers["X-Accel-Limit-Rate"] = self.limit_rate

        # let front-end auto detect mime type
        headers["Content-Type"] = ""
        return "", 200, headers
