#  backend/api.py  - Khaiii-based parser API
#
#
__author__ = 'jwainwright'

import re, json
from pprint import pprint, pformat
from datetime import datetime
import http.client, urllib.parse

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

logFile = None

# ------------- main parser page ----------------------

@parserApp.route('/analyzer')
def analyzer():
    "analyzer main page"
    return render_template("/index.html")

# ============== API handlers =========================

# ------------ main sentence parser -------------------

@parserApp.route('/parse/', methods=['POST'])
def parse():
    "parse POSTed Korean sentence"
    # grab sentence to parse
    input = request.form.get('sentence')
    if not input:
        return jsonify(result="FAIL", msg="Missing input sentence(s)")
    showAllLevels = request.form.get('showAllLevels') == 'true'

    # parse input & return parse results to client
    sentences = parseInput(input, showAllLevels=showAllLevels)

    return jsonify(result="OK",
                   sentences=sentences)

# ------------ wikitionary definition lookup --------------

wiktionary = WiktionaryParser()
# include Korean parts-of-speech
for pos in ('suffix', 'particle', 'determiners', 'counters', 'morphemes', 'prefix', ):
    wiktionary.include_part_of_speech(pos)

# hangul & english unicode ranges
ranges = [(0, 0x036f), (0x3130, 0x318F), (0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x1e00, 0x2c00), (0x2022, 0x2022)]
isHangulOrEnglish = lambda s: all(any(ord(c) >= r[0] and ord(c) <= r[1] for r in ranges) for c in s)

@parserApp.route('/definition/<word>', methods=['GET'])
def definition(word):
    "return the wiktionary definition(s) for the given word"
    definitions = []
    # fetch defs, reformat layout & filter out hanja (for now)
    print("sending def request to wiktionary for ", word)
    for defs in wiktionary.fetch(word, 'korean'):
        print("   received wiktionary response for ", word)
        for d in defs['definitions']:
            definitions.append(dict(partOfSpeech = d['partOfSpeech'].capitalize(),
                                    text = [t for t in d['text'] if isHangulOrEnglish(t)]))
    #
    return jsonify(definitions)

# ------------ Naver/Papgo NMT translation --------------

@parserApp.route('/translate/', methods=['POST'])
def tranlsate():
    "call the Naver/Papago NMT API for a translation of the given text"
    #
    sentence = request.form.get('text')
    if not sentence:
        return jsonify(result="FAIL", msg="Missing text")

    translatedText, failReason = getTranslation(sentence)
    log("  translate {0}: {1}".format(sentence.strip(), translatedText.strip() or failReason))
    #
    if failReason:
        return jsonify(dict(result="FAIL", reason=failReason))
    #
    return jsonify(dict(result="OK", translatedText=translatedText))

# ---------  API utility functions ---------------

def parseInput(input, showAllLevels=False):
    "parse input string into list of parsed contained sentence structures"

    # build a string for the KHaiii phoneme analyzer
    input = input.strip()
    if input[-1] not in ['.', '?', '!']:
        input += '.'
    # input = input.replace(',', ' , ').replace(';', ' ; ').replace(':', ' : ') - adding a space before punctuation seems to mess tagging in Khaiii
    log("* parse {0}".format(input))

    # run Khaiii, grab the parts-of-speech list it generates (morphemes + POS tags) and extract original word-to-morpheme groupings
    sentences = []  # handle possible multiple sentences
    posList = []; morphemeGroups = []
    for w in khaiiiAPI.analyze(input):
        morphemeGroups.append([w.lex, [m.lex for m in w.morphs if m.tag != 'SF']])
        for m in w.morphs:
            posList.append('{0}:{1}'.format(m.lex.strip(), m.tag))
            if m.tag == 'SF':
                # sentence end, store extractions & reset for possible next sentence
                sentences.append(dict(posList=posList, morphemeGroups=morphemeGroups, posString=';'.join(posList)))
                posList = []; morphemeGroups = []

    for s in sentences:
        # map POS through synthetic tag mapper & extract word groupings
        mappedPosList, morphemeGroups = TagMap.mapTags(s['posString'], s['morphemeGroups']) #, disableMapping=True)
        log("  {0}".format(s['posString']))
        log("  mapped to {0}".format(mappedPosList))

        if False:  # NLTK chunking
            # perform chunk parsing
            chunkTree = Chunker.parse(mappedPosList, trace=2)
            chunkTree.pprint()
            # apply any synthetic-tag-related node renamings
            TagMap.mapNodeNames(chunkTree)
            # extract popup wiki definitions & references links & notes for implicated nodes
            references = TagMap.getReferences(chunkTree)
            # build descriptive phrase list
            phrases = Chunker.phraseList(chunkTree)
            #
            parseTreeDict = buildParseTree(chunkTree, showAllLevels=showAllLevels)

        else:  # recursive-descent parser
            from rd_grammar import KoreanParser
            parser = KoreanParser([":".join(p) for p in mappedPosList])
            parseTree = parser.parse(verbose=1)
            if parseTree:
                # apply any synthetic-tag-related node renamings
                parseTree.mapNodeNames()
                # extract popup wiki definitions & references links & notes for implicated nodes
                references = parseTree.getReferences()
                # build descriptive phrase list
                phrases = parseTree.phraseList()
                # get noun & verb translations from Naver
                wordDefs = getWordDefs(mappedPosList)
                # build JSONable parse-tree dict
                parseTreeDict = parseTree.buildParseTree(wordDefs=wordDefs, showAllLevels=showAllLevels)
                log("  {0}".format(parseTree))
            else:
                # parsing failed, return unrecognized token
                parseTree = references = parseTreeDict = phrases = None
                s.update(dict(error="Sorry, failed to parse sentence",
                              lastToken=parser.lastTriedToken()))
                log("  ** failed.  Unexpected token {0}".format(parser.lastTriedToken()))

        debugging = dict(posList=pformat(s['posList']),
                         mappedPosList=pformat(mappedPosList),
                         phrases=pformat(phrases),
                         morphemeGroups=pformat(morphemeGroups),
                         parseTree=pformat(parseTreeDict),
                         references=references)

        s.update(dict(mappedPosList=mappedPosList,
                      morphemeGroups=morphemeGroups,
                      parseTree=parseTreeDict,
                      references=references,
                      phrases=phrases,
                      debugging=debugging
                      ))
    #
    return sentences

def buildParseTree(chunkTree, showAllLevels=False):
    "constructs display structures from NLTK chunk-tree"
    # first, recursively turn the chunk tree into a Python nested dict so it can be JSONified
    #  gathering terminals list & adding level from root & parent links along the way
    terminals = []; height = [0]; allNodes = []; nodeIDs = {}
    def asDict(chunk, parent=None, level=0, isLastChild=False):
        height[0] = max(height[0], level)
        if not showAllLevels:
            # elide degenerate tree nodes (those with singleton children)
            while isinstance(chunk, nltk.Tree) and len(chunk) == 1:
                chunk = chunk[0]
        if isinstance(chunk, nltk.Tree):
            tag = chunk.label()
            # ad-hoc label mappings
            if tag == 'S':
                tag = 'Sentence'
            elif tag == 'Predicate' and not isLastChild:
                tag = 'Verb Phrase'
            # build tree node
            node = dict(type='tree', tag=tag, level=level, layer=1, parent=parent)
            node['children'] = [asDict(c, node, level+1, isLastChild=i == len(chunk)-1) for i, c in enumerate(chunk)]
            nodeID = nodeIDs.get(id(node))
            if not nodeID:
                nodeIDs[id(node)] = nodeID = len(nodeIDs) + 1
            node['id'] = nodeID
            allNodes.append(node)
            return node
        else:
            word = chunk[0].strip()
            tag = chunk[1]
            tm = TagMap.POS_labels.get(word + ":" + tag)
            tagLabel = (tm.posLabel if tm else TagMap.partsOfSpeech.get(tag)[0]).split('\n')
            node = dict(type='word', word=word, tag=tag, tagLabel=tagLabel, children=[], parent=parent, level=-1, layer=0)
            nodeID = nodeIDs.get(id(node))
            if not nodeID:
                nodeIDs[id(node)] = nodeID = len(nodeIDs) + 1
            node['id'] = nodeID
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
        n['parent'] = nodeIDs[id(n['parent'])] if n['parent'] else None
    #
    return dict(tree=tree, layers=layers)

def getTranslation(s):
    "retrieves Naver/Papago NMT translation for the given string"
    #
    failReason = translatedText = ''
    data = urllib.parse.urlencode({"source": "ko", "target": "en", "text": s, })
    headers = {"Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
               "X-Naver-Client-Id": "P3YGzu2suEI1diX0DarY",
               "X-Naver-Client-Secret": "9yhV2ea0wC"}
    conn = http.client.HTTPSConnection("openapi.naver.com")
    conn.request("POST", "/v1/papago/n2mt", data, headers)
    response = conn.getresponse()
    #
    if response.status != 200:
        failReason = response.reason
    else:
        try:
            data = response.read()
            result = json.loads(data).get("message", {}).get("result")
            if result:
                translatedText = result.get('translatedText')
                if not translatedText:
                    failReason = "Naver result missing translateText"
            else:
                failReason = "Naver response missing result"
        except:
            failReason = "Ill-formed JSON response from Naver API"
    conn.close()
    #
    return translatedText, failReason

def getWordDefs(mappedPosList):
    "retrieve definitions for nouns & verbs from Naver"
    # pl = [(wpos.split(':')[0], wpos.split(':')[1]) for wpos in posList.split(';')]
    pl = mappedPosList
    wordsToTranslate = [w + ('다' if pos[0] == 'V' else '') for w, pos in pl if pos[0] in ('V', 'N')]
    words = [w for w, pos in pl if pos[0] in ('V', 'N')]
    translatedText, failReason = getTranslation('\n'.join(wordsToTranslate))
    if failReason:
        return {}
    else:
        return {w: d.lower().strip('.') for w, d in zip(words, translatedText.split('\n'))}

def log(msg):
    "logs message"
    global logFile
    if not logFile:
        # open log file
        logFile = open("analyzer.log", "a")
        logFile.write("\n------ Analyzer start {0} -----\n\n".format(datetime.now().isoformat(' ')))
    #
    logFile.write("{0}: {1}\n".format(datetime.now().isoformat(sep=' ', timespec='milliseconds'), msg))
    logFile.flush()

if __name__ == "__main__":
    #
    run_dev_server()

# Naver/Papago NMT API:
# curl "https://openapi.naver.com/v1/papago/n2mt" \
# -H "Content-Type: application/x-www-form-urlencoded; charset=UTF-8" \
# -H "X-Naver-Client-Id: P3YGzu2suEI1diX0DarY" \
# -H "X-Naver-Client-Secret: 9yhV2ea0wC" \
# -d "source=ko&target=en&text=만나서 반갑습니다." -v

testSamples = r"""

# ---- test phrases -----

저 작은 소년 밥을 먹다.
저 작은 소년의 남동생은 밥을 먹다.
제 친구는 아주 예쁜 차를 샀어요.   
   제 친구는 아주 빠른 차를 샀어요.
그분은 선생님이 아닙니다.
이것이 제 책이예요.
여기는 서울역이예요.
빵 하나를 주세요.
빵 네 개를 주세요.   
  맥주 다섯 병를 주세요.  
  그 큰 빵 네 개를 주세요.   
  맥주 5병이요.  
  맥주 다섯 병를 주세요.
책 두세 권 있어요.
어머니께서 아이에게 밥을 먹이셨습니다.
저는 학교에 안 갔어요.
날이 추워서 집에만 있는다.   
  아기가 있어서 강아지는 안 키워요.
남자와 소년과 여자는 걸었다.
참기름을 넣어서 더 맛있게 만들었다.   
탐은 공부하기를 싫어한다.
기차가 떠나가 버렸어요.  
  인삼은 한국에서만 잘 자랍니다.
비가 오는 것을 봤어요.
  비가 올까 봐 걱정이다.  
  비가 올 것이라고 걱정된다.
  나는 뭐, 심각한 일이라고.   <<--- this one is odd, Khaiii says in "뭐," 뭐 is an IC, but with a space "뭐 ," 뭐 is an NP, wtf?
  사실이 아니라고 몇 번을 해명했지만 통하지 않았다.
  나는 비가 온 것을 보았다.
한국어를 배우고 싶지 않아요.
저는 숙제를 끝내고 나서 집으로 갈 거예요
나는 저녁으로 빵과 물과 밥을 먹었어요.    나는 저녁으로 매운 김치와 국과 밥을 먹고 싶어요.

khaiii의 빌드 및 설치에 관해서는 빌드 및 설치 문서를 참고하시기 바랍니다. 

내일 일요일인데, 뭐 할 거예요?

창문 열어도 돼요?

중국음식을 먹었다. 중국음식을 좋아하기 때문이에요.      중국음식을 먹었다. 왜냐하면 중국음식을 좋아하기 때문이에요.  (written)
중국 음식을 좋아하기 때문에 중국 음식을 먹었어요.   중국 음식은 좋아하기 때문에 중국 음식을 먹었어요. <---  up to here with new grammar
여기 오기 전에 뭐 했어요?     
  밥을 먹은 후에 손을 씻는다.     
  그는 일하기 전에 달렸다.
나는 그것에 대해서 책을 쓸 거야
그 회계사는 정부에 대해서 나쁜 말을 했어요
네가 요리하는 것 좋아해요

 그가 웜을 먹었기 때문에 아팠다.
 아침 겸 점심 맛있어요
자네 덕분에 잘 놀았어요
학생 때 돈을 없었어요.
제 책을 좋다
저는 친구들과 함께 집에 갔어요

중국 음식은 좋아하기 때문에 중국 음식을 먹었어요.      한국 음식은 좋아하기 때문에 한국 음식을 많이 먹을 거예요.

나는 저녁으로 빵과 물과 밥을 먹었어요.
나는 저녁으로 매운 김치와 국과 밥을 먹고 싶어요.
나는 요리하는 것에 대해서 책을 쓸 거야.
냉장고에 우유밖에 없어요

nominal forms
비가 오기 시작했어요.  V기 시작하... to start
인호가 착하기는 해요.  걷는 게 빠르기는 하네요!.   v기는 하... indeed
한 번 만나 보기나 하세요.

민수가 미나에게 선물을 주었어요.
미나에게 민수가 선물을 주었어요.
선물을 민수가 미나에게 주었어요.
민수 씨가 미나  씨에게 선물을 주었어요.
미나  씨에게 민수  씨가 선물을 주었어요.
선물을 민수  씨가 미나  씨에게 주었어요.
왜 그렇게 행복해 보여요?
뭔가 잘못괸 게 트림없어     - 뭔가 = 무엇인가 = 무엇이다 (is something) + -ㄴ가 (phrase and sentence ending raising a question/doubt). from https://www.italki.com/question/457643
  친구는 어딘가 (어디인가) 슬퍼 보였다
이것은 너무 작은가요?  그 학교가 좋은가?  그 사람이 우리 엄마인가?
   뭔가 제가 모르는 일이 있었어요?

그 분은 한국말을 이해하시지?  - confirmation-seeking 지:EF  (in a question?, if not then a recommendation)
맞춤법과 문법 오류를 찾지 못했습니다. - negative-marking 지:EC in an a\uxialiary verb
multiple-clause examples (아/어서, ~면, ...)
만약에 노력하면 한국어를 잘 말할 것 같아요.
근데 가서 뭐 하지?
날이 추워서 집에만 있는다.
참기름을 넣어서 더 맛있게 만들었다.
그녀는 어느 모로나 그녀의 여동생처럼 총명하다. - what is the 나:JC connector here?
나는 일하러 달려갈 것이다. 그렇지 않으면 나는 거기에 차를 몰고 갈 것이다.   - the "그렇지 않으면" is just "Or,"
추우면 못 뛰니까 안 뛰겠다.  - two conditionals in one sentene

대한민국 사람들 중에 지하철을 타 본 사람은 다 아실 거예요. - Will's sentence
이야기를 사랑하는 제시카와 앤, 그리고 이 이야기를 가장 먼저 들어준 디에게  - dedication in H.P
금속은 뜨거우면 팽창하고 차가우면 수축한다.  two 면 in a single clause?
프랑스의 세계적인 의상 디자이너 Emanuel Ungaro가 실내 장식용 직물 디자이너로 나서었다.  SWRC parser sample sentence
그녀는 어느 모로나 그녀의 여동생처럼 총명하다 - '어느 모로나' is an idiom which means 'in every respect', need to map in lexer
말포이는 해리와 론이 조금 피곤해 보이기는 했지만 그다음 날에도 아주 기분 좋은 얼굴로 여전히 호그와트에 있는 걸 보자, 자신의 눈을 믿을 수가 없었다.   H.P.

 this OK: 김의 큰 집에서 파티가 있었어   or  김의 큰 집에서도 음식과 음료가 있었어   or 김의 새로운 집에서도 음식과 음료가 있을 거예요.
  but multiple particles in a noun-phrase mess: 김의 큰 집에서도 파티가 있었어

 need work...
말포이는 해리와 론이 조금 피곤해 보이기는 했다.
나는 매우 배가 고파서 김치를 많이 먹을 거야.
나의 딸도 행복해. 저의 딸도 행복해요 - the possessive should nest inside the as-well??  are them some particles that are always last ina anoun-phrase?
선생이에요. - no tree!
김의 큰 집에서도 파티가 있어. - how to notate all the particles/suffixes in one noun-phrase, and can we fold it into the possessive phrase?
    김의 새로운 집에서도 음식과 음료가 있을 거예요.
음식과 음료가 있는 파티가 있을 것이다. - has two subjects, both because they are associated with 있다 ??  how to annotate?
성함이 어떻게 되세요? - the 게 되 are label together as an aixialiay verb
병아리나 물고기도 키워 본 적 없어요?  - gets 키워 본 intermixed wrongly

"""
