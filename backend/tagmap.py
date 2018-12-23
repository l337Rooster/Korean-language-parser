#  backend/tagmap.py  - manages POS special-case tag mapping
#
#
__author__ = 'jwainwright'

import re
from collections import defaultdict
from pprint import pprint

import nltk

class TagMap(object):
    "holds a tag-mapping spec"

    tagMappings = {}
    tagMapPatterns = []
    nodeNameMaps = defaultdict(dict)
    refsMap = {}
    wikiKeyMap = {}
    tagOrdinal = 0

    references = {"ttmik": ["Talk to me in Korean", "talktomeinkorean.com"],
                  "htsk": ["How to study Korean", "www.howtostudykorean.com"] }

    def __init__(self, tagPat, repl, rename, wikiKey, refs, notes):
        self.tagPat = tagPat
        if rename or refs or wikiKey:
            # uniquify synthetic tag & record it if this mapping includes a chunktree node renaming
            self.repl = repl + ("_%d" % TagMap.tagOrdinal); TagMap.tagOrdinal += 1
            self.newTag = self.repl.split(':')[1] # extract this pattern's synthetic tag
        else:
            self.repl = repl
            self.newTag = None
        self.rename = rename
        self.wikiKey = wikiKey
        self.refs = refs
        self.notes = notes

    @classmethod
    def completeInit(cls):
        "complete tag-mapping setup"
        # build mapping pattern list sorted in reducing pattern length to control transform ordering (todo: might need explicit ordering)
        cls.tagMapPatterns = sorted(((tm.tagPat, tm) for tm in cls.tagMappings.values()), key=lambda x: len(x[0]), reverse=True)
        # build node-name mapping table & extract any refs & wikiKeys
        #   maps uniquified synthetic tag to tables that map ancestor node label to renamed label
        for tm in cls.tagMappings.values():
            if tm.newTag:
                if tm.rename and ':' in tm.rename:
                    old, new = tm.rename.split(':')
                    cls.nodeNameMaps[tm.newTag][old] = new
                if tm.wikiKey:
                    cls.wikiKeyMap[tm.newTag] = tm.wikiKey
                if tm.refs:
                    cls.refsMap[tm.newTag] = [dict(ref=cls.references[key][0], url="https://" + cls.references[key][1] + page) for key, page in tm.refs.items()]
        #
        pprint(cls.nodeNameMaps)

    @classmethod
    def mapTags(cls, posString):
        "generate a version of the parser's original word:POC string under the below-defined synthetic tag mappings"
        # returns a list of (tag,word) tuples
        tagString = ';' + posString + ';'
        for tagPat, tm in cls.tagMapPatterns:
            tagString = re.sub(';' + tagPat + ';', ';' + tm.repl + ';', tagString)
        #
        return [tuple(pos.split(':')) for pos in tagString.strip(';').split(';')]

    @classmethod
    def mapNodeNames(cls, tree):
        "maps NLTK ChunkTree node names under tag-mapping 'rename' definitions"
        #
        def walkTree(t, parentList):
            # walk tree looking for terminal nodes with tags that are in the nodeNameMap table
            #   search up for ancestor node with label in the above-selected nodeNameMap entry, taking label rename
            for i, st in enumerate(t):
                if isinstance(st, nltk.Tree):
                    walkTree(st, [st] + parentList)
                else:
                    nm = cls.nodeNameMaps.get(st[1])
                    if nm:
                        # we have a terminal node for a synthetic tag, run up parents looking for the map's old label
                        for p in parentList:
                            if p.label() in nm:
                                # found matching parent node, rename node
                                p.set_label(nm[p.label()])
                                return
        #
        walkTree(tree, [tree])

    @classmethod
    def getReferences(cls, tree):
        "traverse NLTK ChunkTree for reference link defs"
        #
        references = {}
        wikiKeys = {}
        def walkTree(t):
            # walk tree looking for terminal nodes with tags that are in the refMap or wikiKey tables & build popup menu items
            for i, st in enumerate(t):
                if isinstance(st, nltk.Tree):
                    walkTree(st)
                else:
                    refList = []
                    wk = cls.wikiKeyMap.get(st[1])
                    if wk:
                        word = wk
                    else:
                        word = (st[0] + '다') if st[1][0] == 'V' and st[1][-1] != '다' else st[0]
                    refList.append(dict(name="Wiktionary", slug="https://en.wiktionary.org/wiki/" + word))
                    wikiKeys[st[0]] = word
                    #
                    refs = cls.refsMap.get(st[1])
                    if refs:
                        for ref in refs:
                            refList.append(dict(name=ref['ref'], slug=ref['url']))
                    if refList:
                        references[st[0]] = refList
                    if '_' in st[1]:
                        # trim indexed POS tags
                        pass # not for now.....t[i] = (st[0], st[1].split('_')[0])

        #
        walkTree(tree)
        return references, wikiKeys



def tm(tagPat=r'', repl=r'', rename=None, wikiKey=None, refs=(), notes=None):
    "build & store a tag-map entry"
    TagMap.tagMappings[tagPat] = TagMap(tagPat, repl, rename, wikiKey, refs, notes)

# ================================== tag-mapping specs ==============================

# synthetic tag patterns -
#    patterns of these word:POC strings are preprocessed to define new
#    synthetic word:POC tags used in the chunking grammar below
#  at present, these are applied in the order longest-to-shortest pattern, we should probably make this a listfor explicit ordering

# ----- simple tag transforms --------

tm(  # 은/는 - turn topic-marking partcile into subject-marker (I think this is right??)
    tagPat=r'(은|는):JX', repl=r'\1:JKS',
)

# note that in the defs below, any def that includes a node rename field will add a unique integer suffix to the replacing synthetic tag
#  so that unambiguous node renaming is possible.  Such synthetic tags MUST be included with a trailing ".*" in the chunking grammar so that it
#  matches all gnerated integer-suffixed variations of the base synthetic tag

# ----- dependent (aka bound) noun forms --------  map to DNF.* + DependentNounForm node rename

# ----- particles --------  map to PRT.* + NounPhrase node rename

tm( # 들 pluralizer
    tagPat=r'들:(TM|XSN)', repl=r'들:PRT',
    rename="NounPhrase:Plural",
    refs={"htsk": "/unit1/unit-1-lessons-9-16/lesson-12/#kp1", },
)

tm( # 에/에서 Location/Time marker
    tagPat=r'(에|에서):JKB', repl=r'\1:PRT',
    rename="NounPhrase:Location/Time",
    refs={"ttmik": "/lessons/l1l18", "htsk": "/unit-1-lessons-9-16/lesson-12/#kp3", },
)

# ----- nominal forms -- transforming verbs & adjectives to nouns ---------  mapping (usually) to NOM.*

tm( # 기/음 nominalizer
    tagPat=r'(기|음):(ETN|NNG)', repl=r'\1:NOM',
    refs={"ttmik": "/lessons/level-2-lesson-19", "htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-26-33/lesson-29"},
)

tm( # 는것 nominalizer
    tagPat=r'(ㄴ|는|ㄹ):ETM;것:NNB', repl=r'\1 것:NOM',
    wikiKey='것',
    refs={"ttmik": "/lessons/level-2-lesson-19", "htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-26-33/lesson-26/"},
    notes="",
)

# ----- connection suffixes --------  mapping to CON.* & renaming Connection

tm( # 및 "also" connecting adverb(??)
    tagPat=r'및:MAG', repl=r'및:CON',
    rename="Connection:Also",
)

tm( # 또는 "alternatives" connecting adverb(??)
    tagPat=r'또는:MAG', repl=r'또는:CON',
    rename="Connection:Alternatives",
)

# ----- prepositional phrase suffix patterns -------  mapping to PRP.* & renaming PrepositionalPhrase

tm( # 전 "before X-ing" prepositional suffix
    tagPat=r'전:NNG;에:JKB', repl=r'전에:PRP',
    rename="PrepositionalPhrase:Before",
    wikiKey='전',
    refs={"ttmik": "/lessons/level-3-lesson-10", "htsk": "/unit1/unit-1-lessons-17-25-2/lesson-24/#242"},
    notes="a time prepositional phrase suffix attached to a series of noun forms to indicate a time before that implied associated with the noun sequence",
)

tm( # 후|다음|뒤)에 "after X-ing" prepositional suffix
    tagPat=r'(후|다음|뒤):NNG;에:JKB', repl=r'\1에:PRP',
    rename="PrepositionalPhrase:After",
    wikiKey='후',
    refs={"ttmik": "/lessons/level-3-lesson-19;ticket=153893", "htsk": "/unit1/unit-1-lessons-17-25-2/lesson-24/"},
)

tm( # 때문에 "because X" prepositional suffix
    tagPat=r'때문:NNB;에:JKB', repl=r'때문에:PRP',
    rename="PrepositionalPhrase:Because",
    wikiKey='때문',
    refs={"htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-34-41/lesson-38/"},
)

tm( # 에대해 "about X" prepositional suffix
    tagPat=r'에:JKB;(대하|관하):VV;([^:]+):EC', repl=r'에 \1\2:PRP',
    rename="PrepositionalPhrase:About",
    wikiKey='대하다',
    refs={"htsk": "/unit1/unit-1-lessons-9-16/lesson-13/#kp6"},
)
# ------ predicate ending forms ------  mapping to PSX.* & renaming VerbSuffix

tm( # 었 past-tense suffix
    tagPat=r'(았|었):EP', repl=r'\1:PSX',
    rename="VerbSuffix:PastTense",
    refs={"ttmik": "/lessons/l1l17", "htsk": "/unit1/unit-1-lessons-1-8/unit-1-lesson-5/#vpast"},
    notes="",
)

tm( # ㄹ/를 거 이다 future-tense suffix pattern
    tagPat=r'(ㄹ|을|를):ETM;거:NNB;이:VCP', repl=r'\1 거 이:PSX',
    rename="VerbSuffix:FutureTense",
    refs={"ttmik": "/lessons/level-2-lesson-1-future-tense", "htsk": "/unit1/unit-1-lessons-9-16/unit-1-lesson-9/#ifut"},
    notes="",
)

tm( # 고 싶다 want-to suffix pattern
    tagPat=r'고:EC;싶:VX', repl=r'고 싶:PSX',
    rename="VerbSuffix:WantTo",
    wikiKey="싶다",
    refs={"ttmik": "/lessons/l1l13", "htsk": "/unit1/unit-1-lessons-17-25-2/lesson-17/#co5"},
    notes="",
)

# ------------

TagMap.completeInit()

# tm(  #
#     tagPat=r'', repl=r':NSX',
#     rename="NounSuffix:",
#     wikiKey='',
#     refs=("ttmik:", "htsk:"),
#     notes="",
# )
#

# -------- parts-of-speech descriptors ---------------

partsOfSpeech = {
  #  POS-tag    (Wiktionary POS, Khaiii class,         Detail,                          Korean class:POS)
    "NNG":      ("Noun",        "Substantive",      "General noun",                     "체언: 일반 명사"),
    "NNP":      ("Proper Noun", "Substantive",      "Proper noun",                      "체언: 고유 명사"),
    "NNB":      ("Noun",        "Substantive",      "Bound noun, e.g. 것",               "체언: 의존 명사"),
    "NP":       ("Pronoun",     "Substantive",      "Pronoun",                          "체언	: 대명사"),
    "NR":       ("Noun",        "Substantive",      "Number",                           "체언	: 수사"),
    "VV":       ("Verb",        "Inflectional",     "Verb",                             "용언	: 동사"),
    "VA":       ("Adjective",   "Inflectional",     "Descriptive verb / Adjective",     "용언	: 형용사"),
    "VX":       ("Verb",        "Inflectional",     "Auxiliary or supplimental verb",   "용언: 보조 용언"),
    "VCP":      ("Adjective",   "Inflectional",     "The positive copula - 이다",        "용언: 긍정 지정사"),
    "VCN":      ("Adjective",   "Inflectional",     "The negative copula - 아니다",       "용언:	부정 지정사"),
    "MM":       ("Determiner",  "Modifier",         "Determiner",                       "수식언: 관형사"),
    "MAG":      ("Adverb",      "Modifier",         "General adverb",                   "수식언: 일반 부사"),
    "MAJ":      ("Adverb",      "Modifier",         "Joining adverb, e.g. 그래서",        "수식언: 접속 부사"),
    "IC":       ("Interjection","Independent",      "Interjection e.g. 야!",             "독립언: 감탄사"),
    "JKS":      ("Particle",    "Post-position",    "Subject-marking particle",         "관계언: 주격 조사"),
    "JKC":      ("Particle",    "Post-position",    "Subject-marker for complement words", "관계언: 보격 조사"),
    "JKG":      ("Particle",    "Post-position",    "Possessive-marker 의",              "관계언: 관형격 조사"),
    "JKO":      ("Particle",    "Post-position",    "Object-marking particle",          "관계언: 목적격 조사"),
    "JKB":      ("Particle",    "Post-position",    "Adverbial particle",               "관계언: 부사격 조사"),
    "JKV":      ("Particle",    "Post-position",    "Vocative case marker",             "관계언: 호격 조사"),
    "JKQ":      ("Particle",    "Post-position",    "Quotation marker",                 "관계언: 인용격 조사"),
    "JX":       ("Particle",    "Post-position",    "Topic-marking particle",           "관계언: 보조사"),
    "EP":       ("Suffix",      "Dependent form",   "Suffix-head, e.g. 었 or 시",        "의존 형태	: 선어말 어미"),
    "EF":       ("Suffix",      "Dependent form",   "Predicate-closing suffix",         "의존 형태	: 종결 어미"),
    "EC":       ("Suffix",      "Dependent form",   "Verb/Auxiliary connecting suffix", "의존 형태	: 연결 어미"),
    "ETN":      ("Suffix",      "Dependent form",   "Verb-nominalizing suffix, e.g. 기", "의존 형태: 명사형 전성 어미"),
    "ETM":      ("Suffix",      "Dependent form",   "Verb-to-adjective transforming suffix, e.g. 은", "의존 형태: 관형형 전성 어미"),
    "XPN":      ("Prefix",      "Dependent form",   "Substantive prefix",               "의존 형태	: 체언 접두사"),
    "XSN":      ("", "Dependent form", "", "의존 형태: 명사 파생 접미사"),
    "XSV":      ("", "Dependent form", "", "의존 형태: 동사 파생 접미사"),
    "XSA":      ("", "Dependent form", "", "의존 형태: 형용사 파생 접미사"),
    "XR":       ("", "Dependent form", "", "의존 형태: 어근"),
    "SF":       ("", "Punctuation", "", "기호; 마침표, 물음표, 느낌표"),
    "SP":       ("", "Punctuation", "", "기호: 쉼표, 가운뎃점, 콜론, 빗금"),
    "SS":       ("", "Punctuation", "", "기호: 따옴표, 괄호표, 줄표"),
    "SE":       ("", "Punctuation", "", "기호: 줄임표"),
    "SO":       ("", "Punctuation", "", "기호: 붙임표(물결, 숨김, 빠짐)"),
    "SL":       ("", "Punctuation", "", "기호: 외국어"),
    "SH":       ("", "Punctuation", "", "기호: 한자"),
    "SW":       ("", "Punctuation", "", "기호: 기타 기호(논리, 수학 기호, 화폐 기호 등)"),
    "SWK":      ("", "Punctuation", "", "기호: 한글 자소"),
    "SN":       ("", "Punctuation", "", "기호: 숫자"),
    "ZN":       ("", "", "", "추정: 분석 불능(명사 추정)"),
    "ZV":       ("", "", "", "추정: 분석 불능(용언 추정)"),
    "ZZ":       ("", "", "", "추정: 분석 불능(기타)"),
}

##  Questions
#
#   점심을 먹은 다음에, 도서관에 갔어요.  - should 'after' also bind the related (opening) object?;   Should N에 phrase be called "Location"? - ambiguous with AtTime