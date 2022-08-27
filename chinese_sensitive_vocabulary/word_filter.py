import flashtext
import jieba
import numpy as np
import requests

word_url = 'http://localhost/words.txt'


class SensitiveWordModel(object):
    def __init__(self, word_url):
        self.word_url = word_url
        self.spam = set()
        self.nospam = {}
        # self.__get_words_info()
        self.__get_words_local()
        self.word_filter = flashtext.KeywordProcessor()
        self.word_filter.add_keywords_from_list(list(self.spam))

    def predict(self, text):
        text = text.lower()
        _ = set(jieba.cut(text))
        return min(sum(sorted([self.nospam.get(w, 0) for w in _][:3], reverse=True)) / 3, 1)

    def __get_words_info(self):
        for s in requests.get(self.word_url, verify=False).text.strip().split('\n'):
            _ = s.split('\t')
            if _[1] == '0':
                self.nospam[_[0]] = np.asarray(_[2:], float).sum()
            else:
                self.spam.add(_[0])

    def __get_words_local(self):
        with open("words.txt", "r+", encoding="UTF-8") as f:
            for s in f.read().split("\n"):
                _ = s.split('\t')
                if _[1] == '0':
                    self.nospam[_[0]] = np.asarray(_[2:], float).sum()
                else:
                    self.spam.add(_[0])


if __name__ == '__main__':
    text = '3年没有夫妻生活，妻子怀疑丈夫有外遇，丈夫说出原因，出乎意外'
    swm = SensitiveWordModel(word_url)
    print(swm.predict(text))
