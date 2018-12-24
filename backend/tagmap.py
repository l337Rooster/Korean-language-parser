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

    dictionaries = [{"title": "Wiktionary",       "slug": "https://en.wiktionary.org/wiki/${word}"},
                    {"title": "Naver dictionary", "slug": "https://endic.naver.com/search.nhn?sLn=en&searchOption=all&query=${word}" },]

    references = {"ttmik": {"title": "Talk to me in Korean", "hostname": "talktomeinkorean.com"},
                  "htsk":  {"title": "How to study Korean",  "hostname": "www.howtostudykorean.com"}, }

    #  parts-of-speech descriptors
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
        "VCN":      ("Adjective",   "Inflectional",     "The negative copula - 아니다",       "용언: 부정 지정사"),
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
        "XSN":      ("Suffix",      "Dependent form",   "Noun-modifying suffix, e.g. 들, 님", "의존 형태: 명사 파생 접미사"),
        "XSV":      ("Suffix",      "Dependent form",   "Verb-forming suffix, e.g. ~하다",    "의존 형태: 동사 파생 접미사"),
        "XSA":      ("Suffix",      "Dependent form",   "Adjective-forming suffix",         "의존 형태: 형용사 파생 접미사"),
        "XR":       ("Noun",        "Dependent form",   "Noun root for formed verb or adjective", "의존 형태: 어근"),
        "SF":       ("Punctuation", "Mark",             "Period, question mark, exclamation mark", "기호; 마침표, 물음표, 느낌표"),
        "SP":       ("Punctuation", "Mark",             "Comma, colon, semicolon, slash",   "기호: 쉼표, 가운뎃점, 콜론, 빗금"),
        "SS":       ("Punctuation", "Mark",             "Quotes, parentheses, dash",        "기호: 따옴표, 괄호표, 줄표"),
        "SE":       ("Punctuation", "Mark",             "Ellipsis",                         "기호: 줄임표"),
        "SO":       ("Punctuation", "Mark",             "Hyphen, tilde",                    "기호: 붙임표(물결, 숨김, 빠짐)"),
        "SL":       ("Foreign",     "Mark",             "Word in foreign language (non-Hangul)", "기호: 외국어"),
        "SH":       ("Chinese",     "Mark",             "Chinese characters",               "기호: 한자"),
        "SW":       ("Symbol",      "Mark",             "Other symbols (logics, math symbols, currency symbols, etc.)", "기호: 기타 기호(논리, 수학 기호, 화폐 기호 등)"),
        "SWK":      ("Letter",      "Mark",             "Hangul character (자모)",            "기호: 한글 자소"),
        "SN":       ("Numeral",     "Mark",             "Numeral",                          "기호: 숫자"),
        "ZN":       ("Guess",       "Guess",            "Unknown, guessing noun",           "추정: 분석 불능(명사 추정)"),
        "ZV":       ("Guess",       "Guess",            "Unknown, guessing possessive",     "추정: 분석 불능(용언 추정)"),
        "ZZ":       ("Unknown",     "Guess",            "Unknown",                          "추정: 분석 불능(기타)"),
        #
        # note that synthetic tags defined below include a mapping to one of the above basic POS
    }

    def __init__(self, tagPat, repl, basePOS, descr, rename, wikiKey, refs, notes):
        self.tagPat = tagPat
        # uniquify synthetic tag & record it if this mapping includes a chunktree node renaming
        self.repl = repl + ("_%d" % TagMap.tagOrdinal); TagMap.tagOrdinal += 1
        self.newTag = self.repl.split(':')[1] # extract this pattern's synthetic tag
        self.rename = rename
        self.wikiKey = wikiKey
        self.refs = refs
        self.notes = notes
        self.basePos = basePOS
        self.descr = descr
        # add POS definition for synthetic tag, based on basePOS overriding detail descriptor
        baseDef = TagMap.partsOfSpeech[basePOS]
        TagMap.partsOfSpeech[self.newTag] = (baseDef[0], baseDef[1], descr or baseDef[2], baseDef[3])

    @classmethod
    def completeInit(cls):
        "complete tag-mapping setup"
        # build mapping pattern list sorted in reducing pattern length to control transform ordering (todo: might need explicit ordering)
        cls.tagMapPatterns = sorted(((tm.tagPat, tm) for tm in cls.tagMappings.values()), key=lambda x: len(x[0]), reverse=True)
        # build node-name mapping table & extract any refs & wikiKeys
        #   maps uniquified synthetic tag to tables that map ancestor node label to renamed label
        for tm in cls.tagMappings.values():
            if tm.rename and ':' in tm.rename:
                old, new = tm.rename.split(':')
                cls.nodeNameMaps[tm.newTag][old] = new
            if tm.wikiKey:
                cls.wikiKeyMap[tm.newTag] = tm.wikiKey
            if tm.refs:
                cls.refsMap[tm.newTag] = [dict(ref=cls.references[key]['title'],
                                               url="https://" + cls.references[key]['hostname'] + page) for key, page in tm.refs.items()]
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
                    if wk != "none":
                        if wk:
                            word = wk
                        else:
                            word = (st[0] + '다') if st[1][0] == 'V' and st[1][-1] != '다' else st[0]
                        # add dictionary links
                        for d in cls.dictionaries:
                            refList.append(dict(name=d['title'], slug=d['slug'].replace("${word}", word)))
                        #
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



def tm(tagPat=r'', repl=r'', basePOS=None, descr=None, rename=None, wikiKey=None, refs=(), notes=None):
    "build & store a tag-map entry"
    TagMap.tagMappings[tagPat] = TagMap(tagPat, repl, basePOS, descr, rename, wikiKey, refs, notes)

# ================================== tag-mapping specs ==============================

# synthetic tag patterns -
#    patterns of these word:POC strings are preprocessed to define new
#    synthetic word:POC tags used in the chunking grammar below
#  at present, these are applied in the order longest-to-shortest pattern, we should probably make this a listfor explicit ordering

# note that in the in the processing of the defs below, all new tags will have a "_nnn" appended to make them unique and
# assist in unambiguous mapping to the associated metadata in chuck-tree post-processing.  So, any references to these
# new tags in the chunking grammar MUST be included with a trailing ".*" in the chunking grammar so that it
#  matches all gnerated integer-suffixed variations of the base synthetic tag

# ----- tag-sequence foldings --------

tm(  # noun-dervied verbs, N하다, N되다, N당하다, N시키다, etc. - combine XR|NN & VND suffix into a single NDV (noun-derived verb) verb
    tagPat=r'([^:]+):(XR|NNG);([^:]+):XSV', repl=r'\1\3:VND',
    basePOS="NNG", descr="Verb derived from a noun",
    notes="Noun-derived verb - ${1} + ${3}",
)

tm(  # noun-dervied adjective,  - combine XR|NN & XSA suffix into a single VAND (noun-derived adjective) adjective
    tagPat=r'([^:]+):(XR|NNG);([^:]+):XSA', repl=r'\1\3:VAND',
    basePOS="VA", descr="Adjective derived from a noun",
    notes="Noun-derived adjective - ${1} + ${3}",
)

# ----- dependent (aka bound) noun forms --------  map to DNF.* + DependentNounForm node rename

# ----- particles --------  map to PRT.* + NounPhrase node rename

tm( # 들 pluralizer
    tagPat=r'들:(TM|XSN)', repl=r'들:PRT',
    basePOS="VA", descr="Pluralizer",
    rename="NounPhrase:Plural",
    refs={"htsk": "/unit1/unit-1-lessons-9-16/lesson-12/#kp1", },
)

tm( # 에/에서 Location/Time marker
    tagPat=r'(에|에서):JKB', repl=r'\1:PRT',
    basePOS="JKB",
    rename="NounPhrase:Location/Time",
    refs={"ttmik": "/lessons/l1l18", "htsk": "/unit-1-lessons-9-16/lesson-12/#kp3", },
)

# ----- nominal forms -- transforming verbs & adjectives to nouns ---------  mapping (usually) to NOM.*

tm( # 기/음 nominalizer
    tagPat=r'(기|음):(ETN|NNG)', repl=r'\1:NOM',
    basePOS="NNG", descr="Noun derived from a verb",
    refs={"ttmik": "/lessons/level-2-lesson-19", "htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-26-33/lesson-29"},
)

tm( # 는것 nominalizer
    tagPat=r'(ㄴ|는|ㄹ):ETM;것:NNB', repl=r'\1 것:NOM',
    basePOS="NNG", descr="Noun derived from a verb",
    wikiKey='것',
    refs={"ttmik": "/lessons/level-2-lesson-19", "htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-26-33/lesson-26/"},
    notes="",
)

# ----- connection suffixes --------  mapping to CON.* & renaming Connection

tm( # 및 "also" connecting adverb(??)
    tagPat=r'및:MAG', repl=r'및:CON',
    basePOS="MAG", descr="Connecting adverb",
    rename="Connection:Also",
)

tm( # 또는 "alternatives" connecting adverb(??)
    tagPat=r'또는:MAG', repl=r'또는:CON',
    basePOS="MAG", descr="Adverb connecting alternatives",
    rename="Connection:Alternatives",
)

# ----- prepositional phrase suffix patterns -------  mapping to PRP.* & renaming PrepositionalPhrase

tm( # 전 "before X-ing" prepositional suffix
    tagPat=r'전:NNG;에:JKB', repl=r'전에:PRP',
    basePOS="JKB", descr="Adverbial phrase",
    rename="PrepositionalPhrase:Before",
    wikiKey='전',
    refs={"ttmik": "/lessons/level-3-lesson-10", "htsk": "/unit1/unit-1-lessons-17-25-2/lesson-24/#242"},
    notes="a time prepositional phrase suffix attached to a series of noun forms to indicate a time before that implied associated with the noun sequence",
)

tm( # 후|다음|뒤)에 "after X-ing" prepositional suffix
    tagPat=r'(후|다음|뒤):NNG;에:JKB', repl=r'\1에:PRP',
    basePOS="JKB", descr="Adverbial phrase",
    rename="PrepositionalPhrase:After",
    wikiKey='후',
    refs={"ttmik": "/lessons/level-3-lesson-19;ticket=153893", "htsk": "/unit1/unit-1-lessons-17-25-2/lesson-24/"},
)

tm( # 때문에 "because X" prepositional suffix
    tagPat=r'때문:NNB;에:JKB', repl=r'때문에:PRP',
    basePOS="JKB", descr="Adverbial phrase",
    rename="PrepositionalPhrase:Because",
    wikiKey='때문',
    refs={"htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-34-41/lesson-38/"},
)

tm( # 에대해 "about X" prepositional suffix
    tagPat=r'에:JKB;(대하|관하):VV;([^:]+):EC', repl=r'에 \1\2:PRP',
    basePOS="EC", descr="Prepostional connecting suffix",
    rename="PrepositionalPhrase:About",
    wikiKey='대하다',
    refs={"htsk": "/unit1/unit-1-lessons-9-16/lesson-13/#kp6"},
)
# ------ predicate ending forms ------  mapping to PSX.* & renaming VerbSuffix

tm( # 었 past-tense suffix
    tagPat=r'(았|었):EP', repl=r'\1:PSX',
    basePOS="EP", descr="Past-tense particle",
    rename="VerbSuffix:PastTense",
    refs={"ttmik": "/lessons/l1l17", "htsk": "/unit1/unit-1-lessons-1-8/unit-1-lesson-5/#vpast"},
    notes="",
)

tm( # ㄹ/를 거 이다 future-tense suffix pattern
    tagPat=r'(ㄹ|을|를):ETM;거:NNB;이:VCP', repl=r'\1 거 이:PSX',
    basePOS="VX", descr="Future-tense predicate suffix",
    rename="VerbSuffix:FutureTense",
    wikiKey="none",
    refs={"ttmik": "/lessons/level-2-lesson-1-future-tense", "htsk": "/unit1/unit-1-lessons-9-16/unit-1-lesson-9/#ifut"},
    notes="",
)

tm( # 고 싶다 want-to suffix pattern
    tagPat=r'고:EC;싶:VX', repl=r'고 싶:PSX',
    basePOS="VX", descr="Want-to predicate suffix",
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

# # -------- parts-of-speech descriptors ---------------
#
# partsOfSpeech = {
#   #  POS-tag    (Wiktionary POS, Khaiii class,         Detail,                          Korean class:POS)
#     "NNG":      ("Noun",        "Substantive",      "General noun",                     "체언: 일반 명사"),
#     "NNP":      ("Proper Noun", "Substantive",      "Proper noun",                      "체언: 고유 명사"),
#     "NNB":      ("Noun",        "Substantive",      "Bound noun, e.g. 것",               "체언: 의존 명사"),
#     "NP":       ("Pronoun",     "Substantive",      "Pronoun",                          "체언	: 대명사"),
#     "NR":       ("Noun",        "Substantive",      "Number",                           "체언	: 수사"),
#     "VV":       ("Verb",        "Inflectional",     "Verb",                             "용언	: 동사"),
#     "VA":       ("Adjective",   "Inflectional",     "Descriptive verb / Adjective",     "용언	: 형용사"),
#     "VX":       ("Verb",        "Inflectional",     "Auxiliary or supplimental verb",   "용언: 보조 용언"),
#     "VCP":      ("Adjective",   "Inflectional",     "The positive copula - 이다",        "용언: 긍정 지정사"),
#     "VCN":      ("Adjective",   "Inflectional",     "The negative copula - 아니다",       "용언: 부정 지정사"),
#     "MM":       ("Determiner",  "Modifier",         "Determiner",                       "수식언: 관형사"),
#     "MAG":      ("Adverb",      "Modifier",         "General adverb",                   "수식언: 일반 부사"),
#     "MAJ":      ("Adverb",      "Modifier",         "Joining adverb, e.g. 그래서",        "수식언: 접속 부사"),
#     "IC":       ("Interjection","Independent",      "Interjection e.g. 야!",             "독립언: 감탄사"),
#     "JKS":      ("Particle",    "Post-position",    "Subject-marking particle",         "관계언: 주격 조사"),
#     "JKC":      ("Particle",    "Post-position",    "Subject-marker for complement words", "관계언: 보격 조사"),
#     "JKG":      ("Particle",    "Post-position",    "Possessive-marker 의",              "관계언: 관형격 조사"),
#     "JKO":      ("Particle",    "Post-position",    "Object-marking particle",          "관계언: 목적격 조사"),
#     "JKB":      ("Particle",    "Post-position",    "Adverbial particle",               "관계언: 부사격 조사"),
#     "JKV":      ("Particle",    "Post-position",    "Vocative case marker",             "관계언: 호격 조사"),
#     "JKQ":      ("Particle",    "Post-position",    "Quotation marker",                 "관계언: 인용격 조사"),
#     "JX":       ("Particle",    "Post-position",    "Topic-marking particle",           "관계언: 보조사"),
#     "EP":       ("Suffix",      "Dependent form",   "Suffix-head, e.g. 었 or 시",        "의존 형태	: 선어말 어미"),
#     "EF":       ("Suffix",      "Dependent form",   "Predicate-closing suffix",         "의존 형태	: 종결 어미"),
#     "EC":       ("Suffix",      "Dependent form",   "Verb/Auxiliary connecting suffix", "의존 형태	: 연결 어미"),
#     "ETN":      ("Suffix",      "Dependent form",   "Verb-nominalizing suffix, e.g. 기", "의존 형태: 명사형 전성 어미"),
#     "ETM":      ("Suffix",      "Dependent form",   "Verb-to-adjective transforming suffix, e.g. 은", "의존 형태: 관형형 전성 어미"),
#     "XPN":      ("Prefix",      "Dependent form",   "Substantive prefix",               "의존 형태	: 체언 접두사"),
#     "XSN":      ("Suffix",      "Dependent form",   "Noun-modifying suffix, e.g. 들, 님", "의존 형태: 명사 파생 접미사"),
#     "XSV":      ("Suffix",      "Dependent form",   "Verb-forming suffix, e.g. ~하다",    "의존 형태: 동사 파생 접미사"),
#     "XSA":      ("Suffix",      "Dependent form",   "Adjective-forming suffix",         "의존 형태: 형용사 파생 접미사"),
#     "XR":       ("Noun",        "Dependent form",   "Noun root for formed verb or adjective", "의존 형태: 어근"),
#     "SF":       ("Punctuation", "Mark",             "Period, question mark, exclamation mark", "기호; 마침표, 물음표, 느낌표"),
#     "SP":       ("Punctuation", "Mark",             "Comma, colon, semicolon, slash",   "기호: 쉼표, 가운뎃점, 콜론, 빗금"),
#     "SS":       ("Punctuation", "Mark",             "Quotes, parentheses, dash",        "기호: 따옴표, 괄호표, 줄표"),
#     "SE":       ("Punctuation", "Mark",             "Ellipsis",                         "기호: 줄임표"),
#     "SO":       ("Punctuation", "Mark",             "Hyphen, tilde",                    "기호: 붙임표(물결, 숨김, 빠짐)"),
#     "SL":       ("Foreign",     "Mark",             "Word in foreign language (non-Hangul)", "기호: 외국어"),
#     "SH":       ("Chinese",     "Mark",             "Chinese characters",               "기호: 한자"),
#     "SW":       ("Symbol",      "Mark",             "Other symbols (logics, math symbols, currency symbols, etc.)", "기호: 기타 기호(논리, 수학 기호, 화폐 기호 등)"),
#     "SWK":      ("Letter",      "Mark",             "Hangul character (자모)",            "기호: 한글 자소"),
#     "SN":       ("Numeral",     "Mark",             "Numeral",                          "기호: 숫자"),
#     "ZN":       ("Guess",       "Guess",            "Unknown, guessing noun",           "추정: 분석 불능(명사 추정)"),
#     "ZV":       ("Guess",       "Guess",            "Unknown, guessing possessive",     "추정: 분석 불능(용언 추정)"),
#     "ZZ":       ("Unknown",     "Guess",            "Unknown",                          "추정: 분석 불능(기타)"),
#     #
#     # note that synthetic tags defined above include a mapping to one of the above basic POS
# }

##  Questions
#
#   점심을 먹은 다음에, 도서관에 갔어요.  - should 'after' also bind the related (opening) object?;   Should N에 phrase be called "Location"? - ambiguous with AtTime