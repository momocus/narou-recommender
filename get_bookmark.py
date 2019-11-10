# なろうにログインしてブックマークを取得する

import requests
from bs4 import BeautifulSoup
from urllib import parse
import pandas


class NarouBookmark:
    # ユーザーエージェントをFirefoxに偽装するためのヘッダー定義
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) \
    Gecko/20100101 Firefox/69.0"
    headers = {"user-agent": user_agent}

    def __init__(self):
        self.session = requests.Session()

    def login_narou(self):
        """
        なろうにログインする
        """
        # メールアドレスとパスワードの指定
        narouid = ""
        password = ""
        login_info = {
            "narouid": narouid,
            "pass": password
        }
        # なろうURL
        login_url = "https://ssl.syosetu.com/login/login/"
        self.session.post(login_url, headers=self.headers, data=login_info)

    def get_each_category(self, id):
        """
        指定されたカテゴリidでブックマークされた小説のncodeを取得する
        ブックマークは下記の通りカテゴリ分けされているため、カテゴリに応じてpointをつける
        category1: とても好きな作品 -> 2point
        category2: まあまあ好きな作品-> 1point
        category3: 好きではない作品-> 0point

        Parameters
        ----------
        id: int

        Returns
        -------
        bookmark: [[ncode,point]]
        """
        url = "https://syosetu.com/favnovelmain/list/?nowcategory=" + str(id)
        res = self.session.get(url, headers=self.headers)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        anchors = soup.select("a.title")
        point = NarouBookmark.id2point(id)
        bookmark = [[NarouBookmark.url2ncode(
            x.attrs["href"]), point] for x in anchors]
        return bookmark

    def get(self):
        """
        なろうにログインしてブックマークのcategory1,2,3を取得してDataFrameにする

        Returns
        -------
        df: 2 colums DataFrame
        e.g.
               ncode  point
        0    n3803fw      2
        1    n2509eu      1
        """
        self.login_narou()
        # love
        bookmarks = self.get_each_category(1)
        # like
        bookmarks.extend(self.get_each_category(2))
        # dislike
        bookmarks.extend(self.get_each_category(3))

        df = pandas.DataFrame(bookmarks, columns=['ncode', 'point'])
        return df

    @staticmethod
    def id2point(id):
        if id == 1:
            point = 2
        elif id == 2:
            point = 1
        elif id == 3:
            point = 0
        else:
            print('error')
        return point

    @staticmethod
    def url2ncode(nobel_url):
        """
        なろう小説のURLからncodeを抜き出す

        Parameters
        ----------
        nobel_url: str

        Returns
        ----------
        ncode: str
        """
        ncode = parse.urlparse(nobel_url).path.replace("/", "")
        return ncode


def main():
    naroubookmark = NarouBookmark()
    bookmarks = naroubookmark.get()
    print(bookmarks)


if __name__ == "__main__":
    main()
