# coding=utf-8

# 参考 https://www.python.org/dev/peps/pep-0249/#paramstyle
# named paramstyle 貌似只能作为 column value 占位符，可能不满足复杂条件的组合
# 在此，select读类型使用python format格式化，需要注意入参的特殊字符
# update/insert/delete写类型使用paramstyle格式化。

import sqlite3


class BlogDB:
    __db = None
    __conn = None

    def __init__(self, db):
        self.__db = db
        self.__conn = sqlite3.connect(self.__db)
        self.__conn.row_factory = sqlite3.Row

    def __del__(self):
        self.__conn.close()

    def get_article(self, article_id, admin):
        sql = u"SELECT *,GROUP_CONCAT(tag.tag_name) AS tags FROM article LEFT JOIN tag ON article.id=tag.article_id LEFT JOIN user ON article.user_id=user.id WHERE article.flag IN ({flags}) AND article.id={article_id} GROUP BY article.id".format(
            flags="0,2" if admin else "0",
            article_id=article_id)

        cursor = self.__conn.execute(sql)
        return cursor.fetchone()

    def get_latest_articles(self, reverse, sort, page, page_size, admin):
        sql = u"SELECT *,GROUP_CONCAT(tag.tag_name) AS tags FROM article LEFT JOIN tag ON article.id=tag.article_id LEFT JOIN user ON article.user_id=user.id WHERE article.flag IN ({flags}) GROUP BY article.id ORDER BY {field} {is_desc} LIMIT {limit} OFFSET {offset}".format(
            flags="0,2" if admin else "0",
            field="create_time" if sort == "create" else "update_time",
            is_desc="" if reverse else "DESC",
            limit=page_size,
            offset=(page - 1) * page_size)

        cursor = self.__conn.execute(sql)

        return cursor.fetchall()

    def get_articles_total(self, admin):
        sql = u"SELECT COUNT(*) AS total FROM article WHERE flag IN ({flags})".format(
            flags="0,2" if admin else "0")

        cursor = self.__conn.execute(sql)
        return cursor.fetchone()

    def get_latest_comments(self, target, target_id, reverse, sort, page=None, page_size=None):
        sql = u"SELECT * FROM comment LEFT JOIN user ON comment.user_id=user.id WHERE comment.flag=0 AND comment.target='{target}' {target_id} ORDER BY comment.{field} {is_desc} {limit}".format(
            target=target,
            target_id="" if target == "system" else "AND comment.target_id={}".format(target_id),
            field="create_time" if sort == "create" else "update_time",
            is_desc="" if reverse else "DESC",
            limit="" if (page is None) or (page_size is None) else "LIMIT {limit} OFFSET {offset}".format(
                limit=page_size,
                offset=(page - 1) * page_size))

        cursor = self.__conn.execute(sql)
        return cursor.fetchall()

    def get_article_siblings(self, article_id, sort, admin):
        sql = u"SELECT MIN({field}),* FROM article WHERE {field} >= (SELECT {field} FROM article WHERE id={article_id} AND flag IN ({flags})) AND flag IN ({flags}) AND id!={article_id}".format(
            flags="0,2" if admin else "0",
            article_id=article_id,
            field="create_time" if sort == "create" else "update_time"
        )

        cursor = self.__conn.execute(sql)
        next = cursor.fetchone()

        sql = u"SELECT MAX({field}),* FROM article WHERE {field} <= (SELECT {field} FROM article WHERE id={article_id} AND flag IN ({flags})) AND flag IN ({flags}) AND id!={article_id}".format(
            flags="0,2" if admin else "0",
            article_id=article_id,
            field="create_time" if sort == "create" else "update_time"
        )

        cursor = self.__conn.execute(sql)
        prev = cursor.fetchone()

        return prev, next

    def get_comments_total(self, target, target_id):
        sql = u"SELECT COUNT(*) AS total FROM comment WHERE flag=0 AND target='{target}' {target_id}".format(
            target=target,
            target_id="" if target == "system" else "AND target_id={}".format(target_id))

        cursor = self.__conn.execute(sql)
        return cursor.fetchone()

    def get_latest_likes(self, target, target_id, page, page_size):
        sql = u"SELECT * FROM like LEFT JOIN user ON like.user_id=user.id WHERE like.flag=0 AND like.target='{target}' {target_id} ORDER BY like.create_time DESC LIMIT {limit} OFFSET {offset}".format(
            target=target,
            target_id="" if target == "system" else "AND like.target_id={}".format(target_id),
            limit=page_size,
            offset=(page - 1) * page_size)

        cursor = self.__conn.execute(sql)
        return cursor.fetchall()

    def get_likes_total(self, target, target_id):
        sql = u"SELECT COUNT(*) AS total FROM like WHERE flag=0 AND target='{target}' {target_id}".format(
            target=target,
            target_id="" if target == "system" else "AND target_id={}".format(target_id))

        cursor = self.__conn.execute(sql)
        return cursor.fetchone()

    def get_like(self, target, target_id, user_id):
        sql = u"SELECT * FROM like LEFT JOIN user ON like.user_id=user.id WHERE like.flag=0 AND like.target='{target}' {target_id} AND like.user_id={user_id}".format(
            target=target,
            target_id="" if target == "system" else "AND like.target_id={}".format(target_id),
            user_id=user_id)

        cursor = self.__conn.execute(sql)
        return cursor.fetchone()

    def manage_article(self, article_id, visible):
        cursor = self.__conn.execute("UPDATE article SET flag=:flag WHERE id=:article_id AND flag!=1", {
            "flag": 0 if visible else 2,
            "article_id": article_id})

        self.__conn.commit()
        return cursor.lastrowid

    def add_comment(self, target, target_id, body, user_id):
        cursor = self.__conn.execute("INSERT INTO comment (flag, target, target_id, user_id, body, create_time) VALUES (0,:target,:target_id,:user_id,:body,DATETIME('NOW','LOCALTIME'))", {
            "target": target,
            "target_id": None if target == "system" else target_id,
            "user_id": user_id,
            "body": body})

        self.__conn.commit()
        return cursor.lastrowid

    def delete_comment(self, comment_id):
        cursor = self.__conn.execute(u"UPDATE comment SET flag=1,update_time=DATETIME('NOW','LOCALTIME') WHERE flag=0 AND id=:comment_id", {
            "comment_id": comment_id})
        self.__conn.commit()
        return cursor.rowcount

    def add_like(self, target, target_id, user_id):
        cursor = self.__conn.execute(u"INSERT INTO like (flag, target, target_id, user_id, create_time) VALUES (0,:target,:target_id,:user_id,DATETIME('NOW','LOCALTIME'))", {
            "target": target,
            "target_id": None if target == "system" else target_id,
            "user_id": user_id})

        self.__conn.commit()
        return cursor.lastrowid

    def delete_like(self, like_id):
        cursor = self.__conn.execute(u"UPDATE like SET flag=1,update_time=DATETIME('NOW','LOCALTIME') WHERE flag=0 AND id=:like_id", {
            "like_id": like_id})

        self.__conn.commit()
        return cursor.rowcount

    def register_user(self, app_id, open_id):
        cursor = self.__conn.execute(u"SELECT * FROM user WHERE app_id=:app_id AND open_id=:open_id", {
            "app_id": app_id,
            "open_id": open_id})
        ret = cursor.fetchone()

        if ret:
            return ret["id"], ret["admin"] == 1
        else:
            cursor = self.__conn.execute(u"INSERT INTO user (app_id, open_id, create_time) VALUES (:app_id,:open_id,DATETIME('NOW','LOCALTIME'))", {
                "app_id": app_id,
                "open_id": open_id})
            self.__conn.commit()
            return cursor.lastrowid, False

    def update_user(self, user_id, nick_name, avatar_url, gender):
        cursor = self.__conn.execute(u"UPDATE user SET nick_name=:nick_name, avatar_url=:avatar_url, gender=:gender, update_time=DATETIME('NOW','LOCALTIME') WHERE id=:user_id", {
            "nick_name": nick_name,
            "avatar_url": avatar_url,
            "gender": gender,
            "user_id": user_id})
        self.__conn.commit()
        return cursor.lastrowid

    def get_books(self, page, page_size):
        sql = u"SELECT * FROM books WHERE flag=0 ORDER BY date DESC LIMIT {limit} OFFSET {offset}".format(
            limit=page_size,
            offset=(page - 1) * page_size)

        cursor = self.__conn.execute(sql)
        return cursor.fetchall()

    def get_books_total(self):
        sql = u"SELECT COUNT(*) AS total FROM books WHERE flag=0"
        cursor = self.__conn.execute(sql)
        return cursor.fetchone()

    def get_movies(self, page, page_size):
        sql = u"SELECT * FROM movies WHERE flag=0 ORDER BY date DESC LIMIT {limit} OFFSET {offset}".format(
            limit=page_size,
            offset=(page - 1) * page_size)

        cursor = self.__conn.execute(sql)
        return cursor.fetchall()

    def get_movies_total(self):
        sql = u"SELECT COUNT(*) AS total FROM movies WHERE flag=0"
        cursor = self.__conn.execute(sql)
        return cursor.fetchone()

    def clear_books(self):
        cursor = self.__conn.execute(u"DELETE FROM books WHERE flag=0")
        self.__conn.commit()
        return cursor.rowcount

    def add_books_half(self, books):
        cursor = self.__conn.executemany(
            u"INSERT INTO books (link, title, pub, img, state, rating, comment, date, create_time, flag) VALUES (:link,:title,:pub,:img,:state,:rating,:comment,:date,DATETIME('NOW','LOCALTIME'),1)",
            [{
                "link": item["book"]["link"],
                "title": item["book"]["title"],
                "pub": item["book"]["pub"],
                "img": item["book"]["img"],
                "state": item["state"],
                "rating": item["rating"],
                "comment": item["comment"],
                "date": item["date"]
            } for item in books])

        self.__conn.commit()
        return cursor.rowcount

    def add_books_rollback(self):
        cursor = self.__conn.execute(u"DELETE FROM books WHERE flag=1")
        self.__conn.commit()
        return cursor.rowcount

    def add_books_confirm(self):
        cursor = self.__conn.execute(u"UPDATE books SET flag=0 WHERE flag=1")
        self.__conn.commit()
        return cursor.rowcount

    def clear_movies(self):
        cursor = self.__conn.execute(u"DELETE FROM movies WHERE flag=0")
        self.__conn.commit()
        return cursor.rowcount

    def add_movies_half(self, movies):
        cursor = self.__conn.executemany(
            u"INSERT INTO movies (link, title, alias, intro, img, state, rating, comment, date, create_time, flag) VALUES (:link,:title,:alias,:intro,:img,:state,:rating,:comment,:date,DATETIME('NOW','LOCALTIME'),1)",
            [{
                "link": item["movie"]["link"],
                "title": item["movie"]["title"],
                "alias": item["movie"]["alias"],
                "intro": item["movie"]["intro"],
                "img": item["movie"]["img"],
                "state": item["state"],
                "rating": item["rating"],
                "comment": item["comment"],
                "date": item["date"]
            } for item in movies])

        self.__conn.commit()
        return cursor.rowcount

    def add_movies_rollback(self):
        cursor = self.__conn.execute(u"DELETE FROM movies WHERE flag=1")
        self.__conn.commit()
        return cursor.rowcount

    def add_movies_confirm(self):
        cursor = self.__conn.execute(u"UPDATE movies SET flag=0 WHERE flag=1")
        self.__conn.commit()
        return cursor.rowcount

    def get_timeline(self, page, page_size):
        sql = u"SELECT link, date, 'book' AS type FROM books WHERE flag=0 UNION SELECT link, date, 'movie' AS type FROM movies WHERE flag=0 ORDER BY date DESC LIMIT {limit} OFFSET {offset}".format(
            limit=page_size,
            offset=(page - 1) * page_size)
        cursor = self.__conn.execute(sql)

        books = []
        movies = []
        for item in cursor.fetchall():
            if item["type"] == "book":
                books.append(item["link"])
            elif item["type"] == "movie":
                movies.append(item["link"])

        if len(books) > 0:
            sql = u"SELECT * FROM books WHERE link IN ('{}')".format(
                "','".join(books))
            cursor = self.__conn.execute(sql)
            books = cursor.fetchall()

        if len(movies) > 0:
            sql = u"SELECT * FROM movies WHERE link IN ('{}')".format(
                "','".join(movies))
            cursor = self.__conn.execute(sql)
            movies = cursor.fetchall()

        return books, movies

    def add_analytics(self, event, data):
        cursor = self.__conn.execute(u"INSERT INTO analytics (event, data, create_time) VALUES (:event,:data,DATETIME('NOW','LOCALTIME'))", {
            "event": event,
            "data": data})

        self.__conn.commit()
        return cursor.lastrowid
