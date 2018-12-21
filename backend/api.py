#  backend/api.py  - Konlpy Korean parser API
#
#
__author__ = 'jwainwright'

import re
from pprint import pprint, pformat

from flask import (Flask, request, abort, render_template, Response, jsonify)
from flask_cors import CORS

import nltk
from wiktionaryparser import WiktionaryParser

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
KONLPY_ENABLED = False

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

    # run Khaiii
    words = []
    for w in khaiiiAPI.analyze(sentence):
        for m in w.morphs:
            words.append('{0}:{1}'.format(m.lex.strip(), m.tag))
    posString = ';'.join(words)

    # synthetic tag patterns -
    #    patterns of these word:POC strings are preprocessed to define new
    #    synthetic word:POC tags used in the chunking grammar below
    #  at present, these are applied in the order longest-to-shortest pattern, we should probably make this a listfor explicit ordering

    tagMappings = {
        r'들:(TM|XSN)':                  r'들:PLU',  # pluralizer
        r'기:(ETN|NNG)':                  r'기:GNOM',  # nominalizer
        r'(ㄴ|는|ㄹ):ETM;것:NNB':         r'\1 것:GNOM',  # nominalizer
        r'(은|는):JX':                   r'\1:JKS',  # turn topic-marking partcile into subject-marker (I think this is right??)
        r'(ㄹ|을|를):ETM;거:NNB;이:VCP':   r'\1 거 이:FUT',  # ㄹ/를 거 이다 future-tense conjugator (hack!)
        r'전:NNG;에:JKB':                r'전에:BEF',  # before
        r'때문:NNB;에:JKB':               r'때문에:BEC',  # because
        r'및:MAG':                       r'및:ALS',  # also connector (why is it an adverb??)
        r'또는:MAG':                      r'또는:ALT',  # alternative connector (why is it an adverb??)
        r'에:JKB;(대하|관하):VV;([^:]+):EC': r'에 \1\2:PRP',  # preposition "about
    }

    # prepositional phrase suffix-patterns  (generate a <PRPP> pos-tag + metadata to label the parsing

    #    tag-pattern                  replacement          subtree name-mapping             reference links
    # (r'전:NNG;에:JKB',              r'전에:PRP',      "PrepositionalPhrase:Before",  ("ttmik:lessons/level-3-lesson-10", "htsk:unit1/unit-1-lessons-17-25-2/lesson-24/#242"))     # before

    # special predicate forms



    # generate a version of the parser's original word:POC string including synthetic tag mappings above
    tagString = ';' + posString + ';'
    for old, new in sorted(tagMappings.items(), key=lambda x:len(x[0]), reverse=True):
        tagString = re.sub(';' + old + ';', ';' + new + ';', tagString)
    mappedWords = [tuple(pos.split(':')) for pos in tagString.strip(';').split(';')]

    # Korean phrase NLTK chunking grammar

    grammar = r"""

        HadaVerb:           {<NN.*><XSV>}
        AuxiliaryVerb:      {<EC><VX|VV>}
        Adverb:             {<MAG>}
        NominalizedVerb:    {<VV|HadaVerb><EP|FUT>*<GNOM>}
        Adjective:          {<Adverb>*<VA><ETM>}
        DescriptiveVerb:    {<VA>}
        Verb:               {<VV|VCN|HadaVerb|DescriptiveVerb>}
        VerbSuffix:         {<EP|FUT>*<EF|EC>}

        Location:           {<JKB>}
        Title:              {<XSN>}
        
        Preposition:        {<PRP>}

        Noun:               {<NN.*|NR|SL>}       
        Pronoun:            {<NP>}
        Substantive:        {<Noun><Noun>*}
                            {<Pronoun>}
                            {<NominalizedVerb>}            
        NounPhrase:         {<XPN>*<MAG>*<Adjective>*<Substantive><Title>*<Location>*<PLU>*<JX>*<Preposition>*}
                            
        Possessive:         {<NounPhrase><JKG><NounPhrase>}
        Component:          {<NounPhrase|Possessive><JC|ALS|ALT>}
        Connection:         {<Component><Component>*<NounPhrase|Possessive>}
        
        Constituent:        {<NounPhrase|Possessive|Connection>}
        
        Complement:         {<Constituent><JKC>} 
        Object:             {<Constituent><JKO>}  
        Subject:            {<Constituent><JKS>}
        
        Before:             {<Constituent|Object|Subject>*<Constituent><BEF>}
        Because:            {<Constituent|Object|Subject>*<Constituent><BEC>}
    
        Copula:             {<Constituent><Adverb>*<VCP><AuxiliaryVerb>*<VerbSuffix>}
        Predicate:          {<Adverb>*<Verb><AuxiliaryVerb>*<VerbSuffix>}

        """

    # Component: { < NounPhrase > < JC | ALS > }
    # Connection: { < Component > < Component > * < NounPhrase > }
    # Possessive: { < NounPhrase | Connection > < JKG > < NounPhrase | Connection > }

    # Constituent:        {<Subject|Object|Complement>}
    # Clause:             {<Constituent>*<Predicate>}
    # Sentence:           {<Clause><Clause>*}

    # gen chunk tree from the word-POS list under the above chunking grammar
    parser = nltk.RegexpParser(grammar, trace=1)
    print(parser._stages)
    chunkTree = parser.parse(mappedWords)

    # heuristic subtree simplifications
    # toss sentence end node
    if not isinstance(chunkTree[-1], nltk.Tree) and chunkTree[-1][1] == 'SF':
        chunkTree.remove(chunkTree[-1])
    # flatten connection trees
    def flattenConnections(t):
        for st in t:
            if isinstance(st, nltk.Tree):
                if st.label() == 'Connection':
                    # if Connection node, pull up component tuples into one long connection sequence
                    for i, c in enumerate(list(st)[:-1]):
                        st[2 * i] = c[0]
                        st.insert(2 * i + 1, c[1])
                else:
                    flattenConnections(st)
    flattenConnections(chunkTree)

    # generate phrase-descriptors from top-level subtrees
    hiddenTags = { 'Substantive', 'Constituent', 'NounPhrase', 'Connection', }
    def flattenPhrase(t, phrase):
        for st in t:
            if isinstance(st, nltk.Tree):
                phrase = flattenPhrase(st, phrase)
                if st.label() not in hiddenTags:
                    phrase.append({"type": 'label', "word": st.label()})
            else:
                phrase.append({"type": 'word', "word": st[0].strip(), "tag": st[1]}) # st[1][0] if st[1][0] in ('N', 'V') else st[0].strip()
        return phrase
    #
    phrases = []
    for t in chunkTree:
        if isinstance(t, nltk.Tree):
            phrase = flattenPhrase(t, [])
            if t.label() not in hiddenTags:
                phrase.append({"type": 'label', "word": t.label()})
            phrases.append(phrase)
        else:
            phrases.append(('word', t[0].strip()))
    for p in phrases:
        print(p)

    # recursively turn the chunk tree into a Python nested dict for the JSON response
    def asDict(chunk):
        while isinstance(chunk, nltk.Tree) and len(chunk) == 1:
            # flatten degenerate tree nodes
            chunk = chunk[0]
        if isinstance(chunk, nltk.Tree):
            return dict(type='tree', tag='Sentence' if chunk.label() == 'S' else chunk.label(), children=[asDict(t) for t in chunk])
        else:
            return dict(type='pos', word=chunk[0].strip(), tag=chunk[1])
    #
    parseTree = asDict(chunkTree)
    debugging = dict(posList=pformat(words),
                     mappedPosList=pformat(mappedWords),
                     phrases=pformat(phrases),
                     parseTree=pformat(parseTree))

    return jsonify(result="OK",
                   posList=words,
                   mappedPosList=mappedWords,
                   phrases=phrases,
                   parseTree=parseTree,
                   debugging=debugging)

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
#  그가 웜을 먹었 기 때문에 아팠다.
#





