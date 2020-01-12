
import pickle
import analyze_data
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score
from sklearn.metrics import recall_score, f1_score, roc_curve, auc

# 参考：　https://qiita.com/0NE_shoT_/items/b702ab482466df6e5569


class LogisticRegressionModel(object):

    def __init__(self):
        self.kyoshi = analyze_data.get_kyoshi()

    def pick_data(self):
        # 目的変数
        # pointが1か2か(好きかめっちゃ好きか)はといったん区別しないでおく
        objective = self.kyoshi.point.apply(lambda x: x > 0)

        # 説明変数
        # 数値変換できない説明変数,使えなさそうな説明変数は削除
        explanatory = self.kyoshi.drop(
            ["title", "story", "userid", "gensaku",
             "keyword", "general_firstup", "general_lastup", "time",
             "isbl", "isgl", "pc_or_k", "novelupdated_at", "updated_at",
             "istensei", "istenni", "iszankoku", "isr15",
             "writer", "point", "ncode"], axis=1)

        # 80%のデータを学習データに、20%を検証データにする
        self.exp_train, self.exp_test, self.obj_train, self.obj_test = \
            train_test_split(explanatory, objective,
                             test_size=0.2, random_state=0)

    def make_model(self):
        # モデルの作成（トレーニング）
        lr = LogisticRegression()
        lr.fit(self.exp_train, self.obj_train)  # モデルの重みを学習
        with open('lr.pickle', mode='wb') as fp:
            pickle.dump(lr, fp)

    def load_model(self):
        with open('lr.pickle', mode='rb') as fp:
            lr = pickle.load(fp)
        self.model = lr

    def test_model(self):

        # モデルの性能評価
        obj_pred = self.model.predict(self.exp_test)
        # 評価結果の表示
        # 混同行列（confusion matrix）
        # 正解率（accuracy）
        # 適合率（precision）
        # 再現率（recall）
        # F1スコア（F1-score）
        print("confusion matrix = \n", confusion_matrix(
            y_true=self.obj_test, y_pred=obj_pred))
        print("accuracy = ", accuracy_score(
            y_true=self.obj_test, y_pred=obj_pred))
        print("precision = ", precision_score(
            y_true=self.obj_test, y_pred=obj_pred))
        print("recall = ", recall_score(y_true=self.obj_test, y_pred=obj_pred))

        print("f1 score = ", f1_score(y_true=self.obj_test, y_pred=obj_pred))

        # AUC（曲線下面積）
        obj_score = self.model.predict_proba(
            self.exp_test)[:, 1]  # 検証データがクラス1に属する確率
        fpr, tpr, thresholds = roc_curve(
            y_true=self.obj_test, y_score=obj_score)

        plt.plot(fpr, tpr, label="roc curve (area = %0.3f)" % auc(fpr, tpr))
        plt.plot([0, 1], [0, 1], linestyle="--", label="random")
        plt.plot([0, 0, 1], [0, 1, 1], linestyle="--", label="ideal")
        plt.legend()
        plt.xlabel("false positive rate")
        plt.ylabel("true positive rate")
        plt.show()

    def classfy(self):
        target = analyze_data.get_target()
        explanatory = target.drop(
            ["title", "story", "userid", "gensaku",
             "keyword", "general_firstup", "general_lastup", "time",
             "isbl", "isgl", "pc_or_k", "novelupdated_at", "updated_at",
             "istensei", "istenni", "iszankoku", "isr15",
             "writer", ], axis=1)
        return self.model.predict(explanatory)


def main():
    lr = LogisticRegressionModel()
    lr.pick_data()


if __name__ == "__main__":
    main()
