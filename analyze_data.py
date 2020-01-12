import bookmark
import narou
import pandas
import requests
import xml.etree.ElementTree as ET
import collections
import math
import numpy
import configparser

train_file = "./data/training.csv"
target_file = "./data/target.csv"


class TextAnalyzer(object):
    # 日本語形態素解析
    keitaiso = "https://jlp.yahooapis.jp/MAService/V1/parse"

    # 校正支援
    kousei = "https://jlp.yahooapis.jp/KouseiService/V1/kousei"

    def __init__(self):
        inifile = configparser.ConfigParser()
        inifile.read('./setting.ini', 'UTF-8')
        self.appid = inifile.get('yahoo', 'appid')

    def keitaiso_kaiseki(self, s):
        request_URL = self.keitaiso
        params = {"appid": self.appid,
                  "results": "ma",
                  "response": "pos",
                  "sentence": s}
        res = requests.post(request_URL, data=params)
        root = ET.fromstring(res.text)
        hinshi = [e.text for e in root.iter("{urn:yahoo:jp:jlp}pos")]
        hinshi_count = collections.Counter(hinshi)
        return hinshi_count

    def bunsho_kousei(self, s):
        request_URL = self.kousei
        params = {"appid": self.appid,
                  "sentence": s}
        res = requests.post(request_URL, data=params)
        root = ET.fromstring(res.text)
        shiteki = [e.text for e in root.iter(
            "{urn:yahoo:jp:jlp:KouseiService}ShitekiInfo")]
        return shiteki


def update_kyoshi():
    naroubookmark = bookmark.NarouBookmark()
    naroubookmark.login_narou()
    bookmarks = naroubookmark.get()
    all_ncodes = bookmarks["ncode"]

    # all_ncodesを20件ずつに分割する
    # なろうAPI制約：ncode指定で小説情報を取得するときは、20件以下しか取得できないため
    division = math.ceil(len(all_ncodes) / 20)
    splited_ncodes = numpy.array_split(all_ncodes, division)

    naroudat = pandas.DataFrame()
    # ncodeを指定してなろうAPIで小説情報取得
    for ncodes in splited_ncodes:
        params = {"ncode":  "-".join(ncodes)}
        jsondata = narou.get_jsondata(params)
        jsondata = jsondata[1:]  # 先頭の{'allcount': n}を削る
        naroudat = naroudat.append(pandas.io.json.json_normalize(jsondata))

    df = bookmarks.merge(naroudat, on="ncode")
    df = add_honbun_analyze(df)
    df.to_csv(train_file, index=False)


def get_kyoshi():
    return pandas.read_csv(train_file)


def update_target():
    df = narou.get_ranking("dailypoint", "ter", 20)
    df = add_honbun_analyze(df)
    df.to_csv(target_file, index=False)
    return df


def add_honbun_analyze(df):

    for i in range(len(df)):
        ncode = df.at[i, "ncode"]
        is_series = df.at[i, "novel_type"] == 1
        pages = df.at[i, "general_all_no"]
        honbun = narou.fetch_novel(ncode, is_series, pages)
        ta = TextAnalyzer()
        hinshi = ta.keitaiso_kaiseki(honbun)
        for column in hinshi.keys():
            df.at[i, column] = hinshi[column]

    return df


def get_target():
    return pandas.read_csv(target_file)


def main():
    # kyoshi.csv とtarget.csvを更新
    update_kyoshi()
    update_target()


if __name__ == "__main__":
    main()
