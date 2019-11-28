# coding=utf-8

import socket
import socks
import requests
from bs4 import BeautifulSoup
from blogdb import BlogDB
from datetime import datetime
import tool
import proxy
import random

book_site = "https://book.douban.com"
book_url = "/people/{account}/all"

movie_site = "https://movie.douban.com"
wish = "/people/{account}/wish"
do = "/people/{account}/do"
collect = "/people/{account}/collect"

user_agent_list = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
]


def get_by_proxy(url, http_proxies, headers=None, timeout=3, retry=3, no_proxy=True):
    if headers is None:
        headers = {"User-Agent": random.choice(user_agent_list)}
    elif "User-Agent" not in headers:
        headers["User-Agent"] = random.choice(user_agent_list)

    for i in range(retry):
        default_socket = None
        if http_proxies:
            selected = random.choice(http_proxies)
            if selected["scheme"] == "socks5":
                proxies = None
                default_socket = socket.socket
                socks.set_default_proxy(socks.SOCKS5, selected["ip"], selected["port"])
                socket.socket = socks.socksocket
            else:
                proxies = {
                    "http": proxy.proxy_to_url(selected),
                    "https": proxy.proxy_to_url(selected)
                }
        else:
            selected = None
            proxies = None

        try:
            rsp = requests.get(url, timeout=timeout, proxies=proxies, headers=headers)
            if rsp.status_code != 200:
                print("get {} by proxy {} error {}".format(url, selected, rsp.status_code))
                continue
            else:
                return rsp
        except Exception as e:
            print(e)
            continue
        finally:
            if default_socket:
                socket.socket = default_socket

    if no_proxy:
        try:
            rsp = requests.get(url, timeout=timeout, headers=headers)
            if rsp.status_code != 200:
                print("get {} error {}".format(url, rsp.status_code))
                return None
            else:
                return rsp
        except Exception as e:
            print(e)
            return None
    else:
        return None


def get_books(url, proxies):
    rsp = get_by_proxy(book_site + url, proxies)
    if not rsp:
        return None, None

    soup = BeautifulSoup(rsp.text, features="lxml")
    rsp.close()

    books = []

    items = soup.select(".article > .interest-list > .subject-item")
    for item in items:
        book = {
            "link": item.select_one(".pic .nbg")["href"],
            "img": item.select_one(".pic img")["src"],
            "title": tool.mm_strip(item.select_one(".info a").text),
            "pub": item.select_one(".info .pub").text.strip()
        }

        date, state = item.select_one(".info .date").text.split(None, 1)
        rating = item.select_one(".info [class^=rating]")
        comment = item.select_one(".info .comment").text.strip()

        books.append({
            "date": datetime.strptime(date, "%Y-%m-%d").date(),
            "state": state,
            "rating": tool.get_rating(rating["class"][0]) if rating else None,
            "comment": comment,
            "book": book
        })

    next = soup.select_one(".paginator .next a")
    return books, next["href"] if next else None


def get_movies(url, proxies):
    rsp = get_by_proxy(movie_site + url, proxies)
    if not rsp:
        return None, None

    soup = BeautifulSoup(rsp.text, features="lxml")
    rsp.close()

    movies = []

    items = soup.select(".article > .grid-view > .item")
    for item in items:
        titles = item.select_one(".info .title em").text.split("/", 1)
        movie = {
            "link": item.select_one(".pic .nbg")["href"],
            "img": item.select_one(".pic img")["src"],
            "title": tool.mm_strip(titles[0]) if len(titles) > 0 else None,
            "alias": tool.mm_strip(titles[1]) if len(titles) > 1 else None,
            "intro": item.select_one(".info .intro").text.strip()
        }

        date = item.select_one(".info .date").text.strip()
        rating = item.select_one(".info [class^=rating]")
        comment = item.select_one(".info .comment")

        movies.append({
            "date": datetime.strptime(date, "%Y-%m-%d").date(),
            "state": u"想看" if url.startswith(wish) else u"在看" if url.startswith(do) else u"看过",
            "rating": tool.get_rating(rating["class"][0]) if rating else None,
            "comment": comment.text.strip() if comment else None,
            "movie": movie
        })

    next = soup.select_one(".paginator .next a")
    return movies, next["href"] if next else None


if __name__ == "__main__":
    proxies = proxy.proxy_shadowsocks()

    db = BlogDB("data/blog.sqlite")

    next = book_url
    ok = True

    while True:
        print("Update books page {} ...".format(next))
        books, next = get_books(next, proxies)
        if not books:
            print("Get books page failed")
            ok = False
            break

        db.add_books_half(books)

        if next is None:
            break

    if ok:
        db.clear_books()
        db.add_books_confirm()
        print("Books updated")
    else:
        db.add_books_rollback()
        print("Books not updated")

    ok = True
    for state in [wish, do, collect]:
        next = state
        while True:
            print("Update movies page {} ...".format(next))
            movies, next = get_movies(next, proxies)
            if not movies:
                print("Get movies page failed")
                ok = False
                break

            db.add_movies_half(movies)

            if next is None:
                break

    if ok:
        db.clear_movies()
        db.add_movies_confirm()
        print("Movies updated")
    else:
        db.add_movies_rollback()
        print("Movies not updated")
