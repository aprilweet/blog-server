# coding=utf-8

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


def get_by_proxy(url, http_proxies, timeout=3, retry=3, no_proxy=True):
    for i in range(retry):
        if http_proxies:
            proxies = {
                "http": proxy.proxy_to_url(random.choice(http_proxies))
            }
        else:
            proxies = None

        try:
            rsp = requests.get(url, timeout=timeout, proxies=proxies)
            if rsp.status_code != 200:
                print("get {} by proxy {} error {}".format(url, proxies, rsp.status_code))
                continue
            else:
                return rsp
        except Exception as e:
            print(e)
            continue

    if no_proxy:
        try:
            rsp = requests.get(url, timeout=timeout)
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
    proxies = proxy.proxy_kuaidaili()

    db = BlogDB("data/blog.sqlite")

    next = book_url
    while True:
        print("Update books page {} ...".format(next))
        books, next = get_books(next, proxies)
        if not books:
            print("Get books page failed")
            break

        db.add_books_half(books)

        if next is None:
            break

    db.clear_books()
    db.add_books_confirm()
    print("Books updated")

    for state in [wish, do, collect]:
        next = state
        while True:
            print("Update movies page {} ...".format(next))
            movies, next = get_movies(next, proxies)
            if not movies:
                print("Get movies page failed")
                break

            db.add_movies_half(movies)

            if next is None:
                break

    db.clear_movies()
    db.add_movies_confirm()
    print("Movies updated")
