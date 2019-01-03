# coding=utf-8

from flask import Flask, Blueprint, request, current_app, g, session, jsonify, send_from_directory
from flask_session import Session
from xaccel import XAccel
from functools import wraps
from blogdb import BlogDB
import tool
import json
import requests


def login_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        print(session)
        if "session_key" not in session or "open_id" not in session or "app_id" not in session:
            return "not login", 401
        return func(*args, **kwargs)

    return inner


def register_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        print(session)
        if "user_id" not in session:
            return "not register", 401
        return func(*args, **kwargs)

    inner.func_name = func.func_name
    return inner


def get_db():
    if not hasattr(g, "db"):
        # thread local
        g.db = BlogDB("data/blog.sqlite")
    return g.db


def make_article(article, abstract, abstract_format, body, body_format):
    item = {
        "articleID": article["id"],
        "title": article["title"],
        "user": {
            "userID": article["user_id"],
            "nickName": article["nick_name"],
            "avatarUrl": article["avatar_url"],
            "gender": article["gender"]
        },
        "author": article["author"],
        "sourceLink": article["source_link"],
        "createTime": tool.to_timestamp(article["create_time"]),
        "updateTime": tool.to_timestamp(article["update_time"]),
        "classification": article["classification"],
        "tags": article["tags"].split(",") if article["tags"] is not None else None
    }
    if abstract:
        item["abstract"], item["abstractFormat"] = tool.get_article(article["abstract"], article["abstract_format"], abstract_format)
    if body:
        item["body"], item["bodyFormat"] = tool.get_article(article["body"], article["body_format"], body_format)
    return item


api = Blueprint("api", __name__, url_prefix="/api/v1")


@api.route("/GetArticle", methods=["GET", "POST"])
@register_required
def get_article():
    req = request.json if request.is_json else request.args

    article_id, abstract, abstract_format, body, body_format, sort = (req.get(key, default_value) for key, default_value in (
        ("articleID", None),
        ("abstract", True),
        ("abstractFormat", None),
        ("body", True),
        ("bodyFormat", None),
        ("sort", "create")))

    article = get_db().get_article(article_id)
    prev, next = get_db().get_article_siblings(article_id, sort)

    data = {
        "article": make_article(article, abstract, abstract_format, body, body_format),
        "prev": {"articleID": prev["id"], "title": prev["title"]} if prev["id"] else None,
        "next": {"articleID": next["id"], "title": next["title"]} if next["id"] else None
    }

    rsp = {"data": data}
    return jsonify(rsp)


@api.route("/GetLatestArticles", methods=["GET", "POST"])
@register_required
def get_latest_articles():
    req = request.json if request.is_json else request.args
    reverse, sort, abstract, abstract_format, body, body_format, page, page_size = (req.get(key, default_value) for key, default_value in (
        ("reverse", False),
        ("sort", "create"),
        ("abstract", True),
        ("abstractFormat", None),
        ("body", False),
        ("bodyFormat", None),
        ("page", 1), ("pageSize", 5)))

    articles = get_db().get_latest_articles(reverse, sort, page, page_size)
    total = get_db().get_articles_total()

    data = {
        "articles": [make_article(article, abstract, abstract_format, body, body_format) for article in articles],
        "total": total["total"]
    }
    rsp = {"data": data}
    return jsonify(rsp)


@api.route("/GetLatestComments", methods=["GET", "POST"])
@register_required
def get_latest_comments():
    req = request.json if request.is_json else request.args

    target, target_id, reverse, sort, page, page_size = (req.get(key, default_value) for key, default_value in (
        ("target", None),
        ("targetID", None),
        ("reverse", False),
        ("sort", "create"),
        ("page", 1),
        ("pageSize", 10)))

    comments = get_db().get_latest_comments(target, target_id, reverse, sort, page, page_size)

    items = []
    for comment in comments:
        item = {
            "commentID": comment["id"],
            "user": {
                "userID": comment["user_id"],
                "nickName": comment["nick_name"],
                "avatarUrl": comment["avatar_url"],
                "gender": comment["gender"]
            },
            "createTime": tool.to_timestamp(comment["create_time"]),
            "body": comment["body"],
        }
        items.append(item)

    total = get_db().get_comments_total(target, target_id)

    data = {"comments": items, "total": total["total"]}
    rsp = {"data": data}
    return jsonify(rsp)


@api.route("/GetLatestLikes", methods=["GET", "POST"])
@register_required
def get_latest_likes():
    req = request.json if request.is_json else request.args

    target, target_id, page, page_size, mine = (req.get(key, default_value) for key, default_value in (
        ("target", None),
        ("targetID", None),
        ("page", 1),
        ("pageSize", 20),
        ("mine", False)))

    likes = get_db().get_latest_likes(target, target_id, page, page_size)

    items = []
    for like in likes:
        item = {
            "likeID": like["id"],
            "user": {
                "userID": like["user_id"],
                "nickName": like["nick_name"],
                "avatarUrl": like["avatar_url"],
                "gender": like["gender"]
            },
            "createTime": tool.to_timestamp(like["create_time"]),
        }
        items.append(item)

    total = get_db().get_likes_total(target, target_id)

    my_like = None
    if mine:
        like = get_db().get_like(target, target_id, session["user_id"])
        if like:
            my_like = {
                "likeID": like["id"],
                "user": {
                    "userID": like["user_id"],
                    "nickName": like["nick_name"],
                    "avatarUrl": like["avatar_url"],
                    "gender": like["gender"]
                },
                "createTime": tool.to_timestamp(like["create_time"])
            }

    data = {"likes": items, "total": total["total"], "mine": my_like}
    rsp = {"data": data}
    return jsonify(rsp)


@api.route("/AddComment", methods=["GET", "POST"])
@register_required
def add_comment():
    req = request.json if request.is_json else request.args

    target, target_id, body = (req.get(key, default_value) for key, default_value in (
        ("target", None),
        ("targetID", None),
        ("body", None)))

    comment_id = get_db().add_comment(target, target_id, body, session["user_id"])
    data = {"commentID": comment_id}
    rsp = {"data": data}
    return jsonify(rsp)


@api.route("/DeleteComment", methods=["GET", "POST"])
@register_required
def delete_comment():
    req = request.json if request.is_json else request.args

    comment_id = req.get("commentID", None)
    count = get_db().delete_comment(comment_id)
    if count == 0:
        rsp = {"error": "comment {} does not exist.".format(comment_id)}
        return jsonify(rsp)
    else:
        return ""


@api.route("/AddLike", methods=["GET", "POST"])
@register_required
def add_like():
    req = request.json if request.is_json else request.args

    target, target_id = (req.get(key, default_value) for key, default_value in (
        ("target", None),
        ("targetID", None)))

    like_id = get_db().add_like(target, target_id, session["user_id"])
    data = {"likeID": like_id}
    rsp = {"data": data}
    return jsonify(rsp)


@api.route("/DeleteLike", methods=["GET", "POST"])
@register_required
def delete_like():
    req = request.json if request.is_json else request.args

    like_id = req.get("likeID", None)

    count = get_db().delete_like(like_id)
    if count == 0:
        rsp = {"error": "like {} does not exist.".format(like_id)}
        return jsonify(rsp)
    else:
        return ""


@api.route("/AboutMe", methods=["GET", "POST"])
@register_required
def about_me():
    req = request.json if request.is_json else request.args

    images, introduction = (req.get(key, default_value) for key, default_value in (
        ("images", True),
        ("introduction", True)))

    data = {}
    with open("data/about/me.json", "r") as f:
        me = json.load(f, encoding="UTF-8")
        if images:
            data["images"] = me["images"]
        if introduction:
            data["introduction"] = me["introduction"]

    rsp = {"data": data}
    return jsonify(rsp)


@api.route("/Login", methods=["GET", "POST"])
def login():
    req = request.json if request.is_json else request.args

    code = req.get("code", None)

    ret = requests.get(application.config["CODE_2_SESSION_URL"], params={
        "appid": application.config["WX_APP_ID"],
        "secret": application.config["WX_APP_SECRET"],
        "js_code": code,
        "grant_type": "authorization_code"
    }, timeout=2).json()

    print(ret)
    if ret.get("errcode", 0) != 0:
        rsp = {"error": ret["errmsg"]}
        return jsonify(rsp)

    # # test code
    # ret = {
    #     "session_key": "mysessionkey",
    #     "openid": "myopenid"
    # }

    session["session_key"] = ret["session_key"]
    session["app_id"] = application.config["WX_APP_ID"]
    session["open_id"] = ret["openid"]

    return ""


@api.route("/Logout", methods=["GET", "POST"])
@register_required
def logout():
    session.clear()
    return ""


@api.route("/Register", methods=["GET", "POST"])
@login_required
def register():
    req = request.json if request.is_json else request.args

    nick_name, avatar_url, gender = (req.get(key, default_value) for key, default_value in (
        ("nickName", None),
        ("avatarUrl", None),
        ("gender", None)))

    user = get_db().register_user(session["app_id"], session["open_id"], nick_name, avatar_url, gender)

    # # test code
    # user = {
    #     "id": 1000,
    #     "admin": 1
    # }

    session["user_id"] = user["id"]

    data = {
        "userID": user["id"],
        "admin": user["admin"] == 1
    }
    rsp = {"data": data}
    return jsonify(rsp)


@api.route("/GetBooks", methods=["GET", "POST"])
@register_required
def get_books():
    req = request.json if request.is_json else request.args

    page, page_size = (req.get(key, default_value) for key, default_value in (
        ("page", 1),
        ("pageSize", 10)))

    books = get_db().get_books(page, page_size)

    items = []
    for book in books:
        item = {
            "date": tool.to_timestamp(book["date"]),
            "state": book["state"],
            "rating": book["rating"],
            "comment": book["comment"],
            "book": {
                "link": book["link"],
                "img": book["img"],
                "title": book["title"],
                "pub": book["pub"]
            }
        }
        items.append(item)

    total = get_db().get_books_total()

    data = {"books": items, "total": total["total"]}
    rsp = {"data": data}
    return jsonify(rsp)


@api.route("/GetMovies", methods=["GET", "POST"])
@register_required
def get_movies():
    req = request.json if request.is_json else request.args

    page, page_size = (req.get(key, default_value) for key, default_value in (
        ("page", 1),
        ("pageSize", 10)))

    movies = get_db().get_movies(page, page_size)

    items = []
    for movie in movies:
        item = {
            "date": tool.to_timestamp(movie["date"]),
            "state": movie["state"],
            "rating": movie["rating"],
            "comment": movie["comment"],
            "movie": {
                "link": movie["link"],
                "img": movie["img"],
                "title": movie["title"],
                "alias": movie["alias"],
                "intro": movie["intro"]
            }
        }
        items.append(item)

    total = get_db().get_movies_total()

    data = {"movies": items, "total": total["total"]}
    rsp = {"data": data}
    return jsonify(rsp)


@api.route("/GetTimeline", methods=["GET", "POST"])
@register_required
def get_timeline():
    req = request.json if request.is_json else request.args

    page, page_size = (req.get(key, default_value) for key, default_value in (
        ("page", 1),
        ("pageSize", 15)))

    books, movies = get_db().get_timeline(page, page_size)

    items = []

    for book in books:
        item = {
            "type": "book",
            "item": {
                "date": tool.to_timestamp(book["date"]),
                "state": book["state"],
                "rating": book["rating"],
                "comment": book["comment"],
                "book": {
                    "link": book["link"],
                    "img": book["img"],
                    "title": book["title"],
                    "pub": book["pub"]
                }
            }
        }
        items.append(item)

    for movie in movies:
        item = {
            "type": "movie",
            "item": {
                "date": tool.to_timestamp(movie["date"]),
                "state": movie["state"],
                "rating": movie["rating"],
                "comment": movie["comment"],
                "movie": {
                    "link": movie["link"],
                    "img": movie["img"],
                    "title": movie["title"],
                    "alias": movie["alias"],
                    "intro": movie["intro"]
                }
            }
        }
        items.append(item)

    items.sort(key=lambda x: x["item"]["date"], reverse=True)

    books_total = get_db().get_books_total()
    movies_total = get_db().get_movies_total()

    data = {"timeline": items, "total": books_total["total"] + movies_total["total"]}
    rsp = {"data": data}
    return jsonify(rsp)


static = Blueprint("static", __name__, url_prefix="/static")


@static.route("/images/<path:path>", methods=["GET"])
@register_required
def get_images(path):
    if current_app.use_x_sendfile:
        return current_app.xaccel("images/" + path)
    else:
        return send_from_directory("data/static/images", path)


application = Flask(__name__)
application.config.from_pyfile("apiconf.py")
Session(application)
XAccel(application)
application.register_blueprint(api)
application.register_blueprint(static)

if __name__ == "__main__":
    application.run(debug=True)
