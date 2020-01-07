# 教師データ作成用に、output.csvからncodeとurlをcsvに書き出す

import pandas as pd
import csv

df = pd.read_csv('output.csv')

# データを眺める
# df['global_point'].hist(bins=11, figsize=(5,5), color = 'red')
# round(df['global_point'].describe(),2)

# 総合評価点で足切り
df = df[df.global_point > 2000]

# 文字数で足切り
df = df[df.length > 800]

# 教師データ作成用に、ncodeとurlをcsvに書き出し
base_url = 'https://ncode.syosetu.com/'
urls = map(lambda ncode: [ncode, '', base_url + ncode.lower()], df['ncode'])
f = open('urls.csv', 'a')
writer = csv.writer(f, lineterminator='\n')
writer.writerow(['ncode', 'point', 'url'])
writer.writerows(list(urls))
f.close
