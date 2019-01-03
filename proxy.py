# coding=utf-8

import requests
from bs4 import BeautifulSoup


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
                "port": item.select_one("td[data-title=PORT]").text.strip()
            })

        return proxies
    except Exception, e:
        print(e)
        return False


def proxy_to_url(proxy):
    scheme = "http://"
    return "{}{}:{}".format(scheme, proxy["ip"], proxy["port"])


if __name__ == "__main__":
    proxies = proxy_kuaidaili()
    print("kuaidaili: {}".format(proxies))
