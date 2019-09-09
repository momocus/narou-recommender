# -*- coding: utf-8 -*-

import requests
import gzip
import json
import os
import sys
import time
import pandas
import statistics
import math


def delay(s=10):
    """
    なろう小説APIを叩いたあとに一定時間待つ

    Parameters
    ----------
    s: int, default 3
        時間[s]
    """
    time.sleep(s)


def get_jsondata(get_params):
    """
    指定したGETパラメータでなろう小説APIからJSONデータを取る

    GETパラメータにはgzip圧縮5、出力json、を追加で指定して通信する。

    アクセスがエラーだった場合は、エラーメッセージを出力して
    プログラムを終了する。
    例えば、GETパラメータが不正だったり、ネットワークが落ちていたり、
    アクセスが拒否されたときに起こる。

    Parameters
    ----------
    get_params: dict
        なろう小説APIを叩くGETのパラメータ

    Returns
    -------
    json
        APIから帰ってきたJSON
    """
    get_params = dict(get_params)  # コピー
    get_params["gzip"] = 5
    get_params["out"] = "json"
    api_url = "https://api.syosetu.com/novelapi/api/"
    res = requests.get(api_url, params=get_params)
    if res.ok:
        jsondata = json.loads(gzip.decompress(res.content))
        return jsondata
    else:                       # アクセスエラー
        print("Error: API response is BAD.")
        print("  request with " + str(get_params))
        sys.exit(1)


def get_allcount(get_params):
    """
    指定されたGETパラメータで全作品数を取得して返す

    GETパラメータにはgzip圧縮5、出力json、上限数1、出力ncode、を追加で指定して
    通信量を減らす。

    Parameters
    ----------
    get_params: dict
        なろう小説APIを叩くGETのパラメータ

    Returns
    -------
    int
        全作品数
    """
    get_params = dict(get_params)  # コピー
    get_params["lim"] = 1
    get_params["of"] = "n"
    jsondata = get_jsondata(get_params)
    allcount = jsondata[0]["allcount"]
    return allcount


def write_json(jsondata, filename):
    """
    なろう小説APIにて取得したJSONデータをファイルに書き込む関数

    JSONデータをpandasにて取り込みを経由してCSVへと変換して追記で書き込む。
    なろう小説APIから帰ってきたallcountを含むデータを、JSONデータとして与える。
    保存されたファイルはヘッダーつきのcsvファイルになる。

    Parameters
    ----------
    jsondata: dict
        なろう小説APIにて取得したJSONデータ
    filename: str
        保存先のファイル名
    """
    if len(jsondata) == 1:  # [{'allcount': 0}]のとき
        return
    else:
        jsondata = jsondata[1:]  # 先頭の{'allcount': n}を削る
        df = pandas.io.json.json_normalize(jsondata)
        header = not(os.path.exists(filename))
        df.to_csv(filename, index=False, header=header, mode="a")


def count_cache(filename):
    """
    キャッシュしている作品数を返す

    作品情報のcsvファイルは先頭行にヘッダーが入っている前提でカウントする。

    作品情報のcsvファイルは改行を含んだ文字列を持っているため、ファイルの
    行数カウントとこの関数の結果は一致しない。

    Parameters
    ----------
    filename: str
        作品情報をキャッシュしているcsvファイルの名前

    Returns
    -------
    int
        キャッシュしている作品数
        キャッシュファイルが存在しないときは0を返す。
    """
    try:
        df = pandas.read_csv(filename)
        return len(df)
    except FileNotFoundError:
        return 0


def get_statistics(get_params):
    """
    作品の長さを1000件サンプリングして、中央値とlogスケールの標準偏差を返す。

    与えられたGETパラメータを使って、なろう小説APIから500件取得を2回行う。
    そのため、この関数を呼び出す前に、与えるGETパラメータによって十分な
    作品件数が取得できるかをチェックしておく。

    件数が1件しかないと、statistics.stdevがstatistics.StatisticsError例外を
    投げる。
    件数が500件に満たないと、get_jsondataでプログラムがエラー終了する。

    Parameters
    ----------
    get_params: dict
        標本対象とするなろう小説APIのGETパラメータ

    Returns
    -------
    int, float
        中央値と、logスケールでの標本標準偏差
    """
    get_params = dict(get_params)  # コピー
    # 1000件の作品長さをサンプリングする
    lengths = []
    for i in range(2):
        get_params["of"] = "l"
        get_params["lim"] = 500
        get_params["st"] = 500 * i + 1
        jsondata = get_jsondata(get_params)
        jsondata = jsondata[1:]     # 先頭のallcountを削る
        lengths += [elem["length"] for elem in jsondata]
        delay()
    # 中央値を取る
    median = statistics.median(lengths)
    # logスケールでの標準偏差をとる
    log_lengths = [math.log(l) for l in lengths]
    log_stdev = statistics.stdev(log_lengths)
    return (median, log_stdev)


def make_splitlengths(allcount, median, log_stdev):
    """
    作品長さに対する作品数の傾向から、ほどよい分割ができる作品長さ範囲を作成する

    この関数は作品の長さが小さい方から、作品数を2^n分割しようとする。
    このときのnは分割された各区間の作品数が1500件前後になるように狙う。
    また分割された各区間の作品数は、それぞれおおよそ同じになるように狙う。

    なろう小説の作品長さの傾向として、logスケールで正規分布に従っている。
    ただし、分布はフタコブラクダになりがちである。
    よって、正規分布に従うデータを等分割するために、累積分布の値が1/2^nになる
    作品長さで区切る。
    そのため、分割された各区間の作品数は等しくならない。

    Parameters
    ----------
    allcount: int
        全作品数
    median: float
        作品の長さの中央値
    log_stdev: float
        logスケールでの標準偏差

    Returns
    -------
    list[str]
        なろう小説APIのパラメータのlengthに与えることができる文字列のリスト
    """
    # HACK:
    #   この固定値sigma_biasesは標準正規分布における累積分布の表から求めた。
    #   この数値によって正規分布に従うデータをおおよそ2^n等分できる。
    #   表のURLは
    #     https://www.koka.ac.jp/morigiwa/sjs/standard_normal_distribution.htm
    #   現状、全作品数に対して約24000件までの対応としている。
    #   それを越えると下記配列siguma_biasesの範囲外アクセスとなる。
    #   2019/09/05現在、なろう小説APIから帰ってくる全件数は、GETパラメータの調整で
    #   12000件ほどまで抑えられている。
    #   そのため、しばらくはこの制限を越えることはないと思われる。
    sigma_biases = [
        [0],
        [-0.68, 0, 0.68],
        [-1.16, -0.68, -0.32, 0, 0.32, 0.68, 1.16],
        [-1.54, -1.16, -0.89, -0.68, -0.49, -0.32, -0.16, 0,
         0.16, 0.32, 0.49, 0.68, 0.89, 1.16, 1.54]
    ]
    split_n = allcount / 1500  # APIは最大2499件とれるが、余裕ある1500件を狙う
    split_index = math.ceil(math.log2(split_n)) - 1  # n分割以上となる2^m分割
    sigma_bias = sigma_biases[split_index]
    split_lengths = [round(median * math.exp(log_stdev * bias))
                     for bias in sigma_bias]
    starts = [""] + [str(start + 1) for start in split_lengths]
    ends = [str(end) for end in split_lengths] + [""]
    ranges = [start + "-" + end for (start, end) in zip(starts, ends)]
    return ranges


def get_write_lessthan2500(get_params, allcount, filename):
    """
    与えられたGETパラメータで2500件未満の小説情報を取得する

    なろう小説APIは、制限により1種類の検索につき2499件までしか取れない。
    そのため、GETパラメータによる小説数が2500件未満の場合にのみ、
    この関数を使って素直に全小説を取得することができる。
    GETパラメータによる小説が2500件以上の場合は、エラーメッセージを出力して
    プログラムを終了する。
    超えなろう小説APIへのアクセスが404となる。
    その後、get_jsondataにてエラー終了となる。

    上記制限により、2499件を変則的な分割で取得する。
    具体的には、1-499（499件）、500-999（500件）、1000-1499（500件）、
    1500-1999（500件）、2000-2499（500件）で取得しようとする。

    Parameters
    ----------
    get_params: dict
        なろう小説APIのGETパラメータ
    allcount: int
        get_paramsによる作品件数
    filename: str
        保存先のファイル名
    """
    if allcount == 0:
        return
    elif allcount >= 2500:
        print("Error: allcount is over API limit, equal or more than 2500")
        print("  request with " + str(get_params))
        sys.exit(1)
    get_params = dict(get_params)  # コピー
    n = math.ceil((allcount + 1) / 500)
    for i in range(n):
        # HACK:
        #   st: 1~2000、lim:1~500のため、区間を等分できない
        #   st=1のときは499件という特殊な区間にする
        get_params["lim"] = 499 if i == 0 else 500
        get_params["st"] = 500 * i
        jsondata = get_jsondata(get_params)
        write_json(jsondata, filename)
        delay()


def get_data(genre, kaiwa, buntai, ty, dirname):
    """
    なろう小説APIを使って小説情報を取得してファイルに保存する

    ファイル名は以下のようになり、outputディレクトリに保存される
      [ジャンル]_[会話率]_[文体]_[タイプ].csv
    例：ジャンル9801、会話率31-40、文体1、タイプreの場合
      ./output/9801_31-40_1_re.csv

    また、保存されるcsvファイルは、先頭にヘッダーを含んでいる。
    このヘッダーはなろう小説APIが返す文字列をそのまま使っている。

    取得の際には、ローカルにキャッシュがあるかを先に確認する。
    キャッシュに対して、現在のなろう小説の件数が5%以上増加していないと
    再取得しない。

    なろう小説APIは、制限により1種類の検索につき2499件までしか取れない。
    これはAPIのGETパラメータのlim（最大出力数）とst（表示開始位置）から
    きている。
    そこで、2500件以上のデータは、作品長さの指定を行い、おおよそ2000件
    以下ずつ取得する。
    おおよそ、各ジャンル、会話率は10%ずつ区切り、各文体、各タイプで
    この関数を呼び出せば、全作品の情報を取得できる。

    引数の詳細は以下URLのAPI仕様における、ジャンル、会話率、文体、タイプを参照。
    https://dev.syosetu.com/man/api/

    Parameters
    ----------
    genre: str
        小説のジャンル、"201"など
    kaiwa: str
        小説の会話率、"N-M"形式（単位%）で指定する
    buntai: int
        小説の文体、1/2/4/6のどれか
    ty: str
        小説のタイプ、"t"と"re"で全作品を網羅できる
    """
    print("ジャンル:{0:<4},会話率:{1:<6},文体:{2},タイプ:{3:<2}".
          format(genre, kaiwa, buntai, ty), end="")

    # ファイル名
    filename = genre + "_" + kaiwa + "_" + str(buntai) + "_" + ty + ".csv"
    filename = os.path.join(dirname, filename)

    # 前回取得した作品数
    cached_allcount = count_cache(filename)
    print(" | cache:" + "{0:>6}".format(cached_allcount), end="")

    # 最新の作品数
    get_params = {"genre": genre, "kaiwaritu": kaiwa,
                  "buntai": buntai, "type": ty}
    allcount = get_allcount(get_params)
    print(" | allcount:" + "{0:>6}".format(allcount), end="")
    delay(1)

    # 5%以上の増分がなければ再取得しない
    if allcount < cached_allcount * 1.05:
        print(" | SKIP")
        return
    else:
        print(" | GET")

    # キャッシュを削除する
    if os.path.exists(filename):
        os.remove(filename)

    get_params = {"genre": genre, "kaiwaritu": kaiwa,
                  "buntai": buntai, "type": ty}
    if allcount < 2500:         # 分割取得の必要なし
        get_write_lessthan2500(get_params, allcount, filename)
    else:                       # 作品の長さで分割して取得する
        if genre == "9902":     # ADHOCK: ジャンル9902は分布が特殊なので固定分割
            r = range(100, 1001, 20)
            starts = [str(start + 1) for start in r[0:len(r)-1]]
            ends = [str(end) for end in r[1:]]
            lengths = [start + "-" + end for (start, end) in zip(starts, ends)]
            lengths = ["-100"] + lengths + ["1001-"]
        else:                   # 作品の長さに対して正規分布を仮定して分割
            median, log_stdev = get_statistics(get_params)
            delay()
            lengths = make_splitlengths(allcount, median, log_stdev)
        for length in lengths:
            get_params["length"] = length  # lengthを追加
            count = get_allcount(get_params)
            delay(1)
            get_write_lessthan2500(get_params, count, filename)


def make_directory(dirname):
    """
    出力先のディレクトリを作成する

    出力先のディレクトリと同じ名前のファイルがある場合は、
    エラーメッセージを出力してプログラムを終了する。

    Parameters
    ----------
    dirname: str
        ディレクトリ名
    """
    if os.path.exists(dirname):
        if os.path.isfile(dirname):
            print("Error: Try to create 'output' directory, \
but file already exists.")
            sys.exit(1)
    else:
        os.mkdir(dirname)


def main():
    # ディレクトリの作成
    dirname = "output"
    make_directory(dirname)

    genres = [
        "101", "102",
        "201", "202",
        "301", "302", "303", "304", "305", "306", "307",
        "401", "402", "403", "404",
        "9901", "9902", "9903", "9904",
        "9999",
        "9801"
    ]
    kaiwas = ["0-10", "11-20", "21-30", "31-40", "41-50",
              "51-60", "61-70", "71-80", "81-90", "91-100"]
    buntais = [1, 2, 4, 6]
    types = ["t", "re"]

    for genre in genres:
        for kaiwa in kaiwas:
            for buntai in buntais:
                for ty in types:
                    get_data(genre, kaiwa, buntai, ty, dirname)


if __name__ == "__main__":
    main()
