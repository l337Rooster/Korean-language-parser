#  tools/load_corpus.py  - loads raw English-Korean sentence KAIST Corpus (http://semanticweb.kaist.ac.kr/home/index.php/KAIST_Corpus)
#
#
__author__ = 'jwainwright'

import re
import codecs
import glob
import json

# set up KHaiii api
import khaiii
khaiiiAPI = khaiii.KhaiiiApi()
khaiiiAPI.open()

def loadCorpus(files):
    "loads all KAIST English/Korean sentence files specified by given files glob"
    sentences = []
    for filename in glob.iglob(files):
        with codecs.open(filename, encoding='cp949') as f:
            while True:
                try:
                    line = f.readline()
                    if not line:
                        break;
                    if line[0] != '#':
                        continue
                    english = line.strip()[1:]
                    line = f.readline()
                    if not line:
                        break
                    korean = line.strip()
                    if not korean:
                        continue
                    # have English & Korean forms, apply Khaiii POS analyzer to Korean
                    if korean[-1] not in ['.', '?', '!']:
                        korean += '.'
                    words = []
                    for w in khaiiiAPI.analyze(korean):
                        for m in w.morphs:
                            if m.tag != 'SF':
                                words.append('{0}:{1}'.format(m.lex.strip(), m.tag))
                    posString = ';'.join(words)
                    #
                    sentences.append((english, korean, posString))
                except UnicodeDecodeError:
                    continue
                except:
                    raise
    #
    return sentences

#
if __name__ == "__main__":
    #
    sentences = loadCorpus('/Users/jwainwright/Downloads/VUfHM5Uc6HwOcoy/Corpus10/*.txt')
    with open('kaist.corpus.json', 'w') as outf:
        json.dump(sentences, outf)