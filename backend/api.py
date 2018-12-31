#  backend/api.py  - Konlpy Korean parser API
#
#
__author__ = 'jwainwright'

import re
from pprint import pprint, pformat
from collections import defaultdict, namedtuple

from flask import (Flask, request, abort, render_template, Response, jsonify)
from flask_cors import CORS

import nltk
from wiktionaryparser import WiktionaryParser

from tagmap import TagMap
from chunker import Chunker

# ---------- initialize KHaiii phoneme analyzer

# set up KHaiii api
import khaiii
khaiiiAPI = khaiii.KhaiiiApi()
khaiiiAPI.open()

# ---------- instantiate Flask (global) app  --------

parserApp = Flask('app',
               static_folder="./dist/static",
               template_folder="./dist")
CORS(parserApp)
#
parserApp.config.update(
    DEBUG=True,
    SECRET_KEY = "iu877hy3jnd8**yd98y334%$#Rjxhg6222",
    SESSION_COOKIE_HTTPONLY = False
)

def run_dev_server():
    "launch Flask dev server"
    parserApp.run(host = '0.0.0.0',
               port = 9000, #80, # 9000,
               debug = True)

# -------- page request handlers --------

parser = None
nodeData = {}

@parserApp.route('/analyzer')
def analyzer():
    "Konlpy analyzer main page"
    return render_template("/index.html")

# -------- API handlers ----------------

@parserApp.route('/parse/', methods=['POST'])
def parse():
    "parse POSTed Korean sentence"
    # grab sentence to parse
    sentence = request.form.get('sentence')
    if not sentence:
        return jsonify(result="FAIL", msg="Missing sentence")

    # build a string for the KHaiii phoneme analyzer
    if sentence.strip()[-1] not in ['.', '?', '!']:
        sentence += '.'

    # run Khaiii, grab the parts-of-speech list it generates (morphemes + POS tags) and extract original word-to-morpheme groupings
    sentences = []  # handle possible multiple sentences
    posList = []; morphemeGroups = []
    for w in khaiiiAPI.analyze(sentence):
        morphemeGroups.append([w.lex, [m.lex for m in w.morphs if m.tag != 'SF']])
        for m in w.morphs:
            posList.append('{0}:{1}'.format(m.lex.strip(), m.tag))
            if m.tag == 'SF':
                # sentence end, store extractions & reset for possible next sentence
                sentences.append(dict(posList=posList, morphemeGroups=morphemeGroups, posString=';'.join(posList)))
                posList = []; morphemeGroups = []

    for s in sentences:
        # map POS through synthetic tag mapper & extract word groupings
        mappedPosList, morphemeGroups = TagMap.mapTags(s['posString'], s['morphemeGroups'])

        # perform chunk parsing
        chunkTree = Chunker.parse(mappedPosList)

        # apply any synthetic-tag-related node renamings
        TagMap.mapNodeNames(chunkTree)

        # extract popup wiki definitions & references links & notes for implicated nodes
        references = TagMap.getReferences(chunkTree)

        # build descriptive phrase list
        phrases = Chunker.phraseList(chunkTree)

        #
        parseTree = buildParseTree(chunkTree)

        debugging = dict(posList=pformat(s['posList']),
                         mappedPosList=pformat(mappedPosList),
                         phrases=pformat(phrases),
                         morphemeGroups=pformat(morphemeGroups),
                         parseTree=pformat(parseTree),
                         references=references)

        s.update(dict(mappedPosList=mappedPosList,
                      morphemeGroups=morphemeGroups,
                      parseTree=parseTree,
                      references=references,
                      phrases=phrases,
                      debugging=debugging
                      ))

    return jsonify(result="OK",
                   sentences=sentences)

def buildParseTree(chunkTree):
    "constructs display structures from NLTK chunk-tree"
    # first, recursively turn the chunk tree into a Python nested dict so it can be JSONified
    #  gathering terminals list & adding level from root & parent links along the way
    terminals = []; height = [0]; allNodes = []
    def asDict(chunk, parent=None, level=0):
        height[0] = max(height[0], level)
        while isinstance(chunk, nltk.Tree) and len(chunk) == 1:
            # flatten degenerate tree nodes
            chunk = chunk[0]
        if isinstance(chunk, nltk.Tree):
            node = dict(type='tree', tag='Sentence' if chunk.label() == 'S' else chunk.label(), level=level, layer=1, parent=parent)
            node['children'] = [asDict(c, node, level+1) for c in chunk]
            node['id'] = id(node)
            allNodes.append(node)
            return node
        else:
            node = dict(type='word', word=chunk[0].strip(), tag=chunk[1], children=[], parent=parent, level=-1, layer=0)
            node['id'] = id(node)
            terminals.append(node)
            allNodes.append(node)
            return node
    tree = asDict(chunkTree)

    # breadth-first traversal up from terminals to set layer-assignemnt for each node
    nodes = list(terminals)
    maxLayer = 0
    while nodes:
        parents = []
        for n in nodes:
            parent = n['parent']
            if parent:
                parent['layer'] = max(n['layer'] + 1, parent['layer'])
                maxLayer = max(maxLayer, parent['layer'])
                parents.append(parent)
        nodes = list(parents)

    # add nodes to their assigned layer, drop parent field circular refs so structures can be JSONified
    layers = [list() for i in range(maxLayer + 1)]
    for n in allNodes:
        layers[n['layer']].append(n['id'])
        n['parent'] = id(n['parent']) if n['parent'] else None
    #
    return dict(tree=tree, layers=layers)


# ------------ wikitionary definition handler --------------

wiktionary = WiktionaryParser()
# include Korean parts-of-speech
for pos in ('suffix', 'particle', 'determiners', 'counters', 'morphemes', ):
    wiktionary.include_part_of_speech(pos)

# hangul & english unicode ranges
ranges = [(0, 0x036f), (0x3130, 0x318F), (0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x1e00, 0x2c00), (0x2022, 0x2022)]
isHangulOrEnglish = lambda s: all(any(ord(c) >= r[0] and ord(c) <= r[1] for r in ranges) for c in s)

@parserApp.route('/definition/<word>', methods=['GET'])
def definition(word):
    "return the wiktionary definition(s) for the given word"
    definitions = []
    # fetch defs, reformat layout & filter out hanja (for now)
    for defs in wiktionary.fetch(word, 'korean'):
        for d in defs['definitions']:
            definitions.append(dict(partOfSpeech = d['partOfSpeech'].capitalize(),
                                    text = [t for t in d['text'] if isHangulOrEnglish(t)]))
    #
    return jsonify(definitions)

#
if __name__ == "__main__":
    #
    run_dev_server()

#  test phrases
#  저는 친구들과 함께 집에 갔어요  via Kormoran yields:

# 그:NP;가:JKS;규칙:NNG;을:JKO;어기:VV;었:EP;기:ETN;때문:NNB;에:JKB;규칙:NNG;에:JKB;따라서:MAJ;그:NP;를:JKO;
# 처벌:NNG;하:XSV;ㅁ:ETN;으로써:JKB;
# 본보기:NNG;를:JKO;보이:VV;는:ETM;것:NNB;이:VCP;다:EF;.:SF
#   서:VV;어:EC;있:VV;을:ETM;때:NNG

# test sentences
# 제 친구는 아주 예쁜 차를 샀어요.   제 친구는 아주 빠른 차를 샀어요.
# 그분은 선생님이 아닙니다.
# 이것이 제 책이예요.
# 여기는 서울역이예요.
# 빵 하나를 주세요.
# 빵 네 개를 주세요.
# 책 두세 권 있어요.
# 어머니께서 아이에게 밥을 먹이셨습니다.
# 저는 학교에 안 갔어요.
# 탐은 공부하기를 싫어한다.
# 기차가 떠나가 버렸어요.  or
# 인삼은 한국에서만 잘 자랍니다.
# 비가 오는 것을 봤어요.   비가 올까 봐 걱정이다.  비가 올 것이라고 걱정된다.  나는 비가 온 것을 보았다.
# khaiii의 빌드 및 설치에 관해서는 빌드 및 설치 문서를 참고하시기 바랍니다.

# 내일 일요일인데, 뭐 할 거예요?
# 한국어를 배우고 싶지 않아요.
# 저는 숙제를 끝내고 나서 집으로 갈 거예요
# 나는 저녁으로 빵과 물과 밥을 먹었어요.    나는 저녁으로 매운 김치와 국과 밥을 먹고 싶어요.

# 창문 열어도 돼요?

# 중국음식을 먹었다. 중국음식을 좋아하기 때문이에요.      중국음식을 먹었다. 왜냐하면 중국음식을 좋아하기 때문이에요.  (written)
# 중국 음식을 좋아하기 때문에 중국 음식을 먹었어요.   중국 음식은 좋아하기 때문에 중국 음식을 먹었어요.
# 여기 오기 전에 뭐 했어요?     밥을 먹은 후에 손을 씻다.     그는 일하기 전에 달렸다.
# 나는 그것에 대해서 책을 쓸 거야
# 그 회계사는 정부에 대해서 나쁜 말을 했어요
# 네가 요리하는 것 좋아해요
#
#  그가 웜을 먹었기 때문에 아팠다.
#  아침 겸 점심 맛있어요
# 자네 덕분에 잘 놀았#
# 학생 때 돈을 없었어요.
# 제 책을 좋다
# 저는 친구들과 함께 집에 갔어요

# 중국 음식은 좋아하기 때문에 중국 음식을 먹었어요.      한국 음식은 좋아하기 때문에 한국 음식을 많이 먹을 거예요.

# 나는 저녁으로 빵과 물과 밥을 먹었어요.
# 나는 저녁으로 매운 김치와 국과 밥을 먹고 싶어요.
# 나는 요리하는 것에 대해서 책을 쓸 거야.
# 냉장고에 우유밖에 없어요


#  needs work...
# 나는 매우 배가 고파서 김치를 많이 먹을 거야.


