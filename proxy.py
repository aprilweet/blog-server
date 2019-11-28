# coding=utf-8

import requests
from bs4 import BeautifulSoup


def proxy_shadowsocks():
    return [{
        "ip": "127.0.0.1",
        "port": 1080,
        "scheme": "socks5"
    }]


def proxy_kuaidaili():
    url = "https://www.kuaidaili.com/free/"
    try:
        rsp = requests.get(url, timeout=3)
        if rsp.status_code != 200:
            print("get {} error {}".format(url, rsp.status_code))
            return False

        soup = BeautifulSoup(rsp.text, features="lxml")
        rsp.close()

        proxies = []

        items = soup.select("[id=list] tbody > tr")
        for item in items:
            proxies.append({
                "ip": item.select_one("td[data-title=IP]").text.strip(),
                "port": item.select_one("td[data-title=PORT]").text.strip(),
                "scheme": "http"
            })

        return proxies
    except Exception as e:
        print(e)
        return False


def proxy_xiladaili():
    url = "http://www.xiladaili.com/gaoni/"
    try:
        rsp = requests.get(url, timeout=10)
        if rsp.status_code != 200:
            print("get {} error {}".format(url, rsp.status_code))
            return False

        soup = BeautifulSoup(rsp.text, features="lxml")
        rsp.close()

        proxies = []

        items = soup.select("table.fl-table tbody > tr")
        for item in items:
            ip, port = item.select_one("td:nth-of-type(1)").text.strip().split(":", 1)
            scheme = item.select_one("td:nth-of-type(2)").text.strip().lower()
            if scheme.startswith("https"):
                scheme = "https"
            elif scheme.startswith("http"):
                scheme = "http"
            else:
                continue

            proxies.append({
                "ip": ip,
                "port": port,
                "scheme": scheme
            })

        return proxies
    except Exception as e:
        print(e)
        return False


def proxy_89ip():
    url = "http://www.89ip.cn/"
    try:
        rsp = requests.get(url, timeout=3)
        if rsp.status_code != 200:
            print("get {} error {}".format(url, rsp.status_code))
            return False

        soup = BeautifulSoup(rsp.text, features="lxml")
        rsp.close()

        proxies = []

        items = soup.select("table.layui-table tbody > tr")
        for item in items:
            ip = item.select_one("td:nth-of-type(1)").text.strip()
            port = item.select_one("td:nth-of-type(2)").text.strip()

            proxies.append({
                "ip": ip,
                "port": port,
                "scheme": "http"
            })

        return proxies
    except Exception as e:
        print(e)
        return False


def proxy_to_url(proxy):
    return "{}://{}:{}".format(proxy["scheme"], proxy["ip"], proxy["port"])


if __name__ == "__main__":
    proxies = proxy_kuaidaili()
    print("kuaidaili: {}".format(proxies))

    proxies = proxy_xiladaili()
    print("xiladaili: {}".format(proxies))

    proxies = proxy_89ip()
    print("89ip: {}".format(proxies))
