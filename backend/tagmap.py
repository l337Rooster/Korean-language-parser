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
    tagOrdinal = 0

    def __init__(self, tagPat, repl, rename, wikiKey, refs, notes):
        self.tagPat = tagPat
        if rename:
            # uniquify synthetic tag & record it if this mapping includes a chunktree node renaming
            self.repl = repl + ("_%d" % TagMap.tagOrdinal); TagMap.tagOrdinal += 1
            self.newTag = self.repl.split(':')[1] # extract this pattern's synthetic tag
        else:
            self.repl = repl
        self.rename = rename
        self.wikiKey = wikiKey
        self.refs = refs
        self.notes = notes

    @classmethod
    def completeInit(cls):
        "complete tag-mapping setup"
        # build mapping pattern list sorted in reducing pattern length to control transform ordering (todo: might need explicit ordering)
        cls.tagMapPatterns = sorted(((tm.tagPat, tm) for tm in cls.tagMappings.values()), key=lambda x: len(x[0]), reverse=True)
        # build node-name mapping table
        #   maps uniquified synthetic tag to tables that map ancestor node label to renamed label
        for tm in cls.tagMappings.values():
            if tm.rename and ':' in tm.rename:
                old, new = tm.rename.split(':')
                cls.nodeNameMaps[tm.newTag][old] = new
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
                                # found matching parent node, rename node & trim POS tag
                                p.set_label(nm[p.label()])
                                t[i] = (st[0], st[1].split('_')[0])
                                return
        #
        walkTree(tree, [tree])

def tm(tagPat=r'', repl=r'', rename=None, wikiKey=None, refs=(), notes=None):
    "build & store a tag-map entry"
    TagMap.tagMappings[tagPat] = TagMap(tagPat, repl, rename, wikiKey, refs, notes)

# -------- parts-of-speech descriptors ---------------

partsOfSpeech = {
    "NNG": "Noun",
    "NNP": "Noun",
    "NNB": "Bound Noun",
    "NR": "Number",
    "NP": "Pronoun",
    "VV": "Verb",
    "VA": "Adjective",
    "VX": "Auxiliar Verb",
    "VCP": "VCP",
    "VCN": "VCN",
    "MM": "MM",
    "MAG": "MAG",
    "MAJ": "MAJ",
    "IC": "IC",
    "JKS": "JKS",
    "JKC": "JKC",
    "JKG": "JKG",
    "JKO": "JKO",
    "JKB": "JKB",
    "JKV": "JKV",
    "JKQ": "JKQ",
    "JC": "JC",
    "JX": "JX",
    "EP": "EP",
    "EF": "EF",
    "EC": "EC",
    "ETN": "ETN",
    "ETM": "ETM",
    "XPN": "XPN",
    "XSN": "XSN",
    "XSV": "XSV",
    "XSA": "XSA",
    "XR": "XR",
    "SF": "SF",
    "SE": "SE",
    "SS": "SS",
    "SP": "SP",
    "SO": "SO",
    "SW": "SW",
    "SH": "SH",
    "SL": "SL",
    "SN": "SN",
    "NF": "NF",
    "NV": "NV",
    "NA": "NA",
}

"""
NNG	일반 명사	General noun
NNP	고유 명사	Distinguished noun
NNB	의존 명사	Dependent noun
NR	수사	Numerals
NP	대명사	Pronoun
VV	동사	Verb
VA	형용사	Adjective
VX	보조 용언	Secondary verb
VCP	긍정 지정사	Positive determiner
VCN	부정 지정사	Negative designator
MM	관형사	Pre-noun (관형사) 
MAG	일반 부사	General adverb
MAJ	접속 부사	Junction adverb
		
IC	감탄사	Interjection (감탄사) 
JKS	주격 조사	Subject Postposition (주격 조사): -이/가, -께서 (honorific) 
JKC	보격 조사	Complement Postposition (보격 조사): -이/가 (after consonant/vowel, respectively) 
JKG	관형격 조사	Pre-nounal Postposition (관형격 조사): -의[of]
JKO	목적격 조사	Object Postposition (목적격 조사): -을/를 (after consonant/vowel, respectively) 
JKB	부사격 조사	Adverbial Postposition (부사격 조사) -에[at, to], -에게[to], -께[to], -에서[at, from], -로/으로[to] 
JKV	호격 조사	Vocative Postposition (호격 조사): -아/야, -(이)여, -(이)시여
JKQ	인용격 조사	
JC	접속 조사	Connection Postposition (접속 조사): -와/과: after vowel and after consonant, respectively 
		
JX	보조사	Supplement Postposition (보조사) auxiliary particles
		
EP	선어말 어미	"pre ending", "head suffix" often tense-head suffix like 었 or 시
EF	종결 어미	predicate closing suffix
EC	연결 어미	connecting suffix
ETN	명사형 전성 어미	Noun form of Transmutation Suffix
ETM	관형형 전성 어미	Pre-noun form of Transmutation Suffix
XPN	체언 접두사	Substantive prefix
		
XSN	명사파생 접미사	noun-derived suffix
"""

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
    refs=("htsk:/unit1/unit-1-lessons-9-16/lesson-12/#kp1", ),
)

tm( # 에/에서 Location/Time marker
    tagPat=r'(에|에서):JKB', repl=r'\1:PRT',
    rename="NounPhrase:Location/Time",
    refs=("ttmik:/lessons/l1l18", "htsk:/unit-1-lessons-9-16/lesson-12/#kp3", ),
)

# ----- nominal forms -- transforming verbs & adjectives to nouns ---------  mapping (usually) to NOM.*

tm( # 기/음 nominalizer
    tagPat=r'(기|음):(ETN|NNG)', repl=r'\1:NOM',
    refs=("ttmik:/lessons/level-2-lesson-19", "htsk:/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-26-33/lesson-29"),
)

tm( # 는것 nominalizer
    tagPat=r'(ㄴ|는|ㄹ):ETM;것:NNB', repl=r'\1 것:NOM',
    wikiKey='것',
    refs=("ttmik:/lessons/level-2-lesson-19", "htsk:/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-26-33/lesson-26/"),
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
    refs=("ttmik:lessons/level-3-lesson-10", "htsk:unit1/unit-1-lessons-17-25-2/lesson-24/#242"),
    notes="a time prepositional phrase suffix attached to a series of noun forms to indicate a time before that implied associated with the noun sequence",
)

tm( # 후|다음|뒤)에 "after X-ing" prepositional suffix
    tagPat=r'(후|다음|뒤):NNG;에:JKB', repl=r'\1에:PRP',
    rename="PrepositionalPhrase:After",
    wikiKey='후',
    refs=("ttmik:/lessons/level-3-lesson-19;ticket=153893", "htsk:/unit1/unit-1-lessons-17-25-2/lesson-24/"),
)

tm( # 때문에 "because X" prepositional suffix
    tagPat=r'때문:NNB;에:JKB', repl=r'때문에:PRP',
    rename="PrepositionalPhrase:Because",
    wikiKey='때문',
    refs=("htsk:/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-34-41/lesson-38/"),
)

tm( # 에대해 "about X" prepositional suffix
    tagPat=r'에:JKB;(대하|관하):VV;([^:]+):EC', repl=r'에 \1\2:PRP',
    rename="PrepositionalPhrase:About",
    wikiKey='대하다',
    refs=("htsk:/unit1/unit-1-lessons-9-16/lesson-13/#kp6"),
)
# ------ predicate ending forms ------  mapping to PSX.* & renaming VerbSuffix

tm( # 었 past-tense suffix
    tagPat=r'(았|었):EP', repl=r'\1:PSX',
    rename="VerbSuffix:PastTense",
    refs=("ttmik:/lessons/l1l17", "htsk:/unit1/unit-1-lessons-1-8/unit-1-lesson-5/#vpast"),
    notes="",
)

tm( # ㄹ/를 거 이다 future-tense suffix pattern
    tagPat=r'(ㄹ|을|를):ETM;거:NNB;이:VCP', repl=r'\1 거 이:PSX',
    rename="VerbSuffix:FutureTense",
    refs=("ttmik:/lessons/level-2-lesson-1-future-tense", "htsk:/unit1/unit-1-lessons-9-16/unit-1-lesson-9/#ifut"),
    notes="",
)

tm( # 고 싶다 want-to suffix pattern
    tagPat=r'고:EC;싶:VX', repl=r'고 싶:PSX',
    rename="VerbSuffix:WantTo",
    wikiKey="싶다",
    refs=("ttmik:/lessons/l1l13", "htsk:/unit1/unit-1-lessons-17-25-2/lesson-17/#co5"),
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

##  Questions
#
#   점심을 먹은 다음에, 도서관에 갔어요.  - should 'after' also bind the related (opening) object?;   Should N에 phrase be called "Location"? - ambiguous with AtTime