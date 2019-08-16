# This is open source software distributed by karupoimou.
# A original source is below.
#
# https://github.com/karupoimou/NarouDataAllDownLoad
#
#
# MIT License
#
# Copyright (c) 2019 karupoimou
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# 『なろう小説API』を用いて、なろうの『全作品情報データを一括取得する』Pythonスクリプト
import requests
import json
import time as tm
import datetime
import gzip
import csv

from http.client import RemoteDisconnected

# 出力ファイル名
filename = 'Narou_All_OUTPUT.xlsx'

# リクエストの秒数間隔
interval = 1

title_list = []

# 出力の際の項目名を指定
column_name = ['title', 'ncode', 'userid', 'writer', 'story', 'biggenre',
               'genre', 'gensaku', 'keyword', 'general_firstup',
               'general_lastup', 'novel_type', 'end', 'general_all_no',
               'length', 'time', 'isstop', 'isr15', 'isbl', 'isgl',
               'iszankoku', 'istensei', 'istenni', 'pc_or_k',
               'global_point', 'fav_novel_cnt', 'review_cnt', 'all_point',
               'all_hyoka_cnt', 'sasie_cnt', 'kaiwaritu', 'novelupdated_at',
               'updated_at', 'weekly_unique']

# リスト途中経過を見るための変数
processed_num = 0

# GETパラメータ　詳しくは「なろうディベロッパー」を参照
genre_setA = ['101', '102', '201', '202', '301', '302', '305', '307', '9999']
genre_setB = ['303', '304', '306', '401', '402', '403', '404']
genre_setC = ['9801']
genre_setD = ['9901', '9902', '9903', '9904']

kaiwa_setA = ['0', '1-10', '11-20', '21-30',
              '31-35', '36-40', '41-50', '51-70', '71-100']
length_setA = ['-250', '251-400', '401-450', '451-500', '501-600', '601-700',
               '701-1000', '1001-1300', '1301-1500', '1501-2000', '2001-3000', '3001-5000',
               '5001-7000', '7001-10000', '10001-13000', '13001-16000',
               '16001-20000', '20001-30000', '30001-50000', '50001-70000',
               '70001-100000', '100001-150000', '150001-200000',
               '200001-400000', '400001-500000', '500001-1000000',
               '1000001-3000000', '3000001-10000000', '10000001 -']

kaiwa_setB = ['0', '1-30', '31-45', '46-60', '61-100']
length_setB = ['-1000', '1001-10000', '10001-100000', '100001-']

kaiwa_setC = ['0', '1-10', '11-20', '21-30', '31-35',
              '36-40', '41-45', '46-50', '51-70', '71-100']
length_setC = ['-199', '200', '201-203', '204-205', '206-210', '211-220',
               '221-230', '231-240', '241-250', '251-260', '261-270',
               '271-280', '281-290', '291-300', '301-320', '321-340',
               '341-350', '351-370', '371-400', '401-430', '431-470',
               '471-500', '501-550', '551-600', '601-650', '651-700',
               '701-750', '751-800', '801-900', '901-1000',
               '1001-1100', '1101-1300', '1301-1600', '1601-2000',
               '2001-2500', '2501-3000', '3001-3500', '3501-4000', '4001-5000',
               '5001-6500', '6501-8000', '8001-9000', '9001-10000',
               '10001-15000', '15001-20000', '20001-30000', '30001-40000',
               '40001-50000', '50001-100000', '100001-120000', '120001-200000',
               '200001-500000', '500001-1000000', '1000001-']

kaiwa_setD = ['0', '1-20', '21-40', '41-70', '71-100']
length_setD = ['-199', '200', '201-205', '206-210', '211-215', '216-220',
               '221-230', '231-240', '241-260', '261-280', '281-300',
               '301-320', '321-350', '351-370', '371-400', '401-450',
               '451-500', '501-600', '601-700', '701-1000', '1001-1500',
               '1501-2000', '2001-3500', '3501-5000', '5001-20000',
               '20001-200000', '200001-']

shousetu_type_set = ['t', 'r', 'er']
st_set = [1, 501, 1001, 1501]


def record_time(s):  # 時刻の書き込みに使う関数
    dt_now = datetime.datetime.now()
    nowtime = dt_now.strftime('%Y-%m-%d %H:%M:%S')
    print(s + " " + nowtime)


def writedat(dat):
    f = open('output.csv', 'a+')
    writer = csv.writer(f, lineterminator='\n')
    # 出力
    writer.writerow(dat)
    # ファイルクローズ
    f.close()


def dump_to_list(r):  # 書き込み処理の関数
    for data in json.loads(r):
        try:
            row = []
            title_list.append(data['title'])
            row.append(data['title'])
            row.append(data['ncode'])
            row.append(data['userid'])
            row.append(data['writer'])
            row.append(data['story'])
            row.append(data['biggenre'])
            row.append(data['genre'])
            row.append(data['gensaku'])
            row.append(data['keyword'])
            row.append(data['general_firstup'])
            row.append(data['general_lastup'])
            row.append(data['novel_type'])
            row.append(data['end'])
            row.append(data['general_all_no'])
            row.append(data['length'])
            row.append(data['time'])
            row.append(data['isstop'])
            row.append(data['isr15'])
            row.append(data['isbl'])
            row.append(data['isgl'])
            row.append(data['iszankoku'])
            row.append(data['istensei'])
            row.append(data['istenni'])
            row.append(data['pc_or_k'])
            row.append(data['global_point'])
            row.append(data['fav_novel_cnt'])
            row.append(data['review_cnt'])
            row.append(data['all_point'])
            row.append(data['all_hyoka_cnt'])
            row.append(data['sasie_cnt'])
            row.append(data['kaiwaritu'])
            row.append(data['novelupdated_at'])
            row.append(data['updated_at'])
            row.append(data['weekly_unique'])
            writedat(row)
        except KeyError:
            pass


def start_process():  # 最初に処理される関数
    record_time('Start')  # 処理開始時刻
    # 全体の数をメモ
    payload = {'out': 'json', 'of': 'n', 'lim': 1}
    allnum = requests.get(
        'https://api.syosetu.com/novelapi/api/', params=payload).text
    print('対象数作品  ', allnum)


def genre_count(g):  # ジャンルごとに作品数を算出する関数
    payload = {'out': 'json', 'of': 'n', 'lim': 1, 'genre': g}
    g_num = requests.get(
        'https://api.syosetu.com/novelapi/api/', params=payload).text
    record_time('genre_start')
    list_length = len(title_list)
    global processed_num
    zoubun = list_length - processed_num
    print('前回からの増分 ', str(zoubun))
    print('現在の取得数 ' + str(list_length))
    processed_num = list_length  # 次回の計算のために現在作品数を記録
    print('\n対象数作品  ', g_num)  # 次ジャンルの作品総数を表示


def genre_A():  # 多いジャンルの作品情報を取得する関数
    for gen in genre_setA:
        genre_count(gen)  # 開始時間　ジャンル内の作品数を記録

        for kai in kaiwa_setA:
            for leng in length_setA:
                print(gen + " " + kai + " " + leng)  # 進行状況の表示
                for sho in shousetu_type_set:

                    for sts in st_set:
                        payload = {'out': 'json', 'gzip': 5, 'opt': 'weekly', 'lim': 500,
                                   'genre': gen, 'kaiwaritu': kai, 'length': leng, 'st': sts, 'type': sho}
                        try:
                            res = requests.get(
                                'https://api.syosetu.com/novelapi/api/', params=payload).content
                        except RemoteDisconnected:
                            tm.sleep(120)
                            res = requests.get(
                                'https://api.syosetu.com/novelapi/api/', params=payload).content

                        r = gzip.decompress(res).decode("utf-8")
                        dump_to_list(r)
                        tm.sleep(interval)


def genre_B():  # 少ないジャンルの作品情報を取得する関数
    for gen in genre_setB:
        genre_count(gen)  # 開始時間　ジャンル内の作品数を記録

        for kai in kaiwa_setB:
            for leng in length_setB:
                print(gen + " " + kai + " " + leng)  # 進行状況の表示
                for sho in shousetu_type_set:

                    for sts in st_set:
                        payload = {'out': 'json', 'gzip': 5, 'opt': 'weekly', 'lim': 500,
                                   'genre': gen, 'kaiwaritu': kai, 'length': leng, 'type': sho, 'st': sts}
                        try:
                            res = requests.get(
                                'https://api.syosetu.com/novelapi/api/', params=payload).content
                        except RemoteDisconnected:
                            tm.sleep(120)
                            res = requests.get(
                                'https://api.syosetu.com/novelapi/api/', params=payload).content

                        r = gzip.decompress(res).decode("utf-8")
                        dump_to_list(r)
                        tm.sleep(interval)


# 『ノンジャンル：9801』の作品情報を取得する関数
def genre_C():
    for gen in genre_setC:
        genre_count(gen)  # 開始時間　ジャンル内の作品数を記録

        for kai in kaiwa_setC:
            for leng in length_setC:
                print(gen + " " + kai + " " + leng)  # 進行状況の表示
                for sho in shousetu_type_set:

                    for sts in st_set:
                        payload = {'out': 'json', 'gzip': 5, 'opt': 'weekly', 'lim': 500,
                                   'genre': gen, 'kaiwaritu': kai, 'length': leng, 'type': sho, 'st': sts}
                        try:
                            res = requests.get(
                                'https://api.syosetu.com/novelapi/api/', params=payload).content
                        except RemoteDisconnected:
                            tm.sleep(120)
                            res = requests.get(
                                'https://api.syosetu.com/novelapi/api/', params=payload).content

                        r = gzip.decompress(res).decode("utf-8")
                        dump_to_list(r)
                        tm.sleep(interval)


def genre_D():  # 99XXジャンルを取得する関数
    for gen in genre_setD:
        genre_count(gen)  # 開始時間　ジャンル内の作品数を記録

        if gen == '9904':  # リプレイジャンルのみ数が少ないので飛ばす
            for sts in st_set:
                print(gen)  # 進行状況の表示

                payload = {'out': 'json', 'gzip': 5, 'opt': 'weekly',
                           'lim': 500, 'genre': gen, 'st': sts}
                res = requests.get(
                    'https://api.syosetu.com/novelapi/api/', params=payload).content
                r = gzip.decompress(res).decode("utf-8")
                dump_to_list(r)
                tm.sleep(interval)
        else:
            for kai in kaiwa_setD:
                for leng in length_setD:
                    print(gen + " " + kai + " " + leng)  # 進行状況の表示
                    for sho in shousetu_type_set:

                        for sts in st_set:
                            payload = {'out': 'json', 'gzip': 5, 'opt': 'weekly', 'lim': 500,
                                       'genre': gen, 'kaiwaritu': kai, 'length': leng, 'st': sts, 'type': sho}
                            try:
                                res = requests.get(
                                    'https://api.syosetu.com/novelapi/api/', params=payload).content
                            except RemoteDisconnected:
                                tm.sleep(120)
                                res = requests.get(
                                    'https://api.syosetu.com/novelapi/api/', params=payload).content

                            r = gzip.decompress(res).decode("utf-8")
                            dump_to_list(r)
                            tm.sleep(interval)

# ######実行する関数をここで指定する##########
# 必要がないものはコメントアウトしてください
# また分割して取得する際にご利用ください


start_process()

genre_A()
# genre_B();
# genre_C();
# genre_D();
