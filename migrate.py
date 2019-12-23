# coding=utf-8

import sqlite3
import jsonlines
from tool import get_article, to_timestamp
from datetime import datetime
from uuid import uuid4
import json


class Reader:
    __conn = None

    def __init__(self):
        self.__conn = sqlite3.connect("data/blog.sqlite")
        self.__conn.row_factory = sqlite3.Row

    def __del__(self):
        if self.__conn:
            self.__conn.close()

    def table(self, table):
        sql = u"SELECT * FROM {}".format(table)
        cursor = self.__conn.execute(sql)
        return cursor.fetchall()

    def article(self, path):
        return get_article(path, "markdown", "markdown")[0]


class Writer:
    def collection(self, collection, data):
        with jsonlines.open("data/migrate/{}.json".format(collection), mode="w") as f:
            for obj in data:
                f.write(obj)


class Adapter:
    __reader = None
    __writer = None

    __user = {}
    __article = {}

    def __init__(self, reader, writer):
        self.__reader = reader
        self.__writer = writer

    def __doc_id(self):
        return str(uuid4())

    def __db_time(self, val):
        s = to_timestamp(val)
        if s:
            return {"$date": {"$numberLong": str(s * 1000)}}
        else:
            return None

    def user(self):
        data = []
        for user in self.__reader.table("user"):
            doc = {"_id": self.__doc_id()}
            doc["appID"] = user["app_id"]
            doc["openID"] = user["open_id"]
            doc["nickName"] = user["nick_name"]
            doc["avatar"] = {
                "url": user["avatar_url"]
            }
            doc["gender"] = "female" if user["gender"] == 2 else "male" if user["gender"] == 1 else None
            doc["admin"] = (user["admin"] == 1)
            doc["createTime"] = self.__db_time(user["create_time"])
            doc["updateTime"] = self.__db_time(user["update_time"])
            self.__user[user["id"]] = doc["_id"]
            data.append(doc)

        self.__writer.collection("mmUser", data)

    def article(self):
        tags = {}
        for tag in self.__reader.table("tag"):
            tags.setdefault(tag["article_id"], [])
            tags[tag["article_id"]].append(tag["tag_name"])

        data = []
        for article in self.__reader.table("article"):
            doc = {"_id": self.__doc_id()}
            doc["deleted"] = (article["flag"] == 1)
            doc["visible"] = (article["flag"] == 0)
            doc["title"] = article["title"]
            doc["author"] = article["author"]
            doc["userID"] = self.__user[article["user_id"]]
            doc["createTime"] = self.__db_time(article["create_time"])
            doc["updateTime"] = self.__db_time(article["update_time"])
            doc["sourceLink"] = article["source_link"]
            doc["abstract"] = self.__reader.article(article["abstract"])
            doc["body"] = self.__reader.article(article["body"])
            doc["classification"] = article["classification"]
            doc["tags"] = tags.get(article["id"], [])
            self.__article[article["id"]] = doc["_id"]
            data.append(doc)

        self.__writer.collection("mmArticle", data)

    def comment(self):
        data = []
        for comment in self.__reader.table("comment"):
            doc = {}
            doc["deleted"] = (comment["flag"] == 1)
            doc["target"] = comment["target"]
            doc["targetID"] = self.__article[comment["target_id"]] if comment["target"] == "article" else None
            doc["userID"] = self.__user[comment["user_id"]]
            doc["createTime"] = self.__db_time(comment["create_time"])
            doc["updateTime"] = self.__db_time(comment["update_time"])
            doc["body"] = comment["body"]
            data.append(doc)

        self.__writer.collection("mmComment", data)

    def like(self):
        data = []
        for like in self.__reader.table("like"):
            doc = {}
            doc["deleted"] = (like["flag"] == 1)
            doc["target"] = like["target"]
            doc["targetID"] = self.__article[like["target_id"]] if like["target"] == "article" else None
            doc["userID"] = self.__user[like["user_id"]]
            doc["createTime"] = self.__db_time(like["create_time"])
            doc["updateTime"] = self.__db_time(like["update_time"])
            data.append(doc)

        self.__writer.collection("mmLike", data)

    def analytics(self):
        data = []
        for item in self.__reader.table("analytics"):
            doc = {}
            doc["createTime"] = self.__db_time(item["create_time"])
            doc["event"] = item["event"]

            item_data = json.loads(item["data"])
            if item["event"] == "open_article":
                doc["data"] = {
                    "user_id_tcb": self.__user[item_data["user_id"]],
                    "article_id_tcb": self.__article[item_data["article_id"]],
                    "article_title": item_data["article_title"]
                }
            elif item["event"] == "reject_auth":
                if item_data["target"] == "article":
                    doc["data"] = {
                        "user_id_tcb": self.__user[item_data["user_id"]],
                        "target": "article",
                        "target_id_tcb": self.__article[int(item_data["target_id"])]
                    }
                elif item_data["target"] == "system":
                    doc["data"] = {
                        "user_id_tcb": self.__user[item_data["user_id"]],
                        "target": "system",
                    }
                else:
                    print("Invalid data.target {}".format(item_data["target"]))
            else:
                print("Invalid event {}".format(item["event"]))
            data.append(doc)

        self.__writer.collection("mmAnalytics", data)


if __name__ == "__main__":
    adapter = Adapter(Reader(), Writer())
    adapter.user()
    adapter.article()
    adapter.comment()
    adapter.like()
    adapter.analytics()
