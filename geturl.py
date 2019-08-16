# 教師データ作成用に、output.csvからncodeとurlをcsvに書き出す

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
import csv

df = pd.read_csv('output.csv')

# データを眺める
# df['global_point'].hist(bins=11, figsize=(5,5), color = 'red')
# round(df['global_point'].describe(),2)

# 総合評価点で足切り
df = df[df.global_point > 2000]

# 教師データ作成用に、ncodeとurlをcsvに書き出し
urls = map(lambda x: [x, 'https://ncode.syosetu.com/' + x + '/'], df['ncode'])
f = open('urls.csv', 'a+')
writer = csv.writer(f, lineterminator='\n')
writer.writerows(list(urls))
f.close
