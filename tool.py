# coding=utf-8

import codecs
import datetime
import time
import numbers


def markdown_to_html(data):
    return data


def html_to_markdown(data):
    return data


def get_article(path, from_format, to_format):
    f = codecs.open("data/articles/" + path, encoding="utf-8")
    text = f.read()
    if from_format == "html" and to_format == "markdown":
        return html_to_markdown(text), to_format
    elif from_format == "markdown" and to_format == "html":
        return markdown_to_html(text), to_format
    else:
        return text, from_format


def mm_strip(data):
    return " ".join(data.split())


def get_rating(rating):
    n = filter(str.isdigit, rating)
    return int(n)


def to_timestamp(val, style=None):
    if isinstance(val, numbers.Real):
        return int(val / 1000)
    elif isinstance(val, datetime.date):
        return int(time.mktime(val.timetuple()))
    elif isinstance(val, basestring):
        if style:
            tmp = datetime.datetime.strptime(val, style)
            return int(time.mktime(tmp.timetuple())) if tmp else None

        for style in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                tmp = datetime.datetime.strptime(val, style)
                return int(time.mktime(tmp.timetuple())) if tmp else None
            except ValueError:
                continue
        else:
            return None
    else:
        return None
