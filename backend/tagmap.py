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
            for st in t:
                if isinstance(st, nltk.Tree):
                    walkTree(st, [st] + parentList)
                else:
                    nm = cls.nodeNameMaps.get(st[1])
                    if nm:
                        # we have a terminal node for a synthetic tag, run up parents looking for the map's old label
                        for p in parentList:
                            if p.label() in nm:
                                # found matching parent node, rename
                                p.set_label(nm[p.label()])
                                return
        #
        walkTree(tree, [tree])


# --------------- tag-mapping specs ----------------

# synthetic tag patterns -
#    patterns of these word:POC strings are preprocessed to define new
#    synthetic word:POC tags used in the chunking grammar below
#  at present, these are applied in the order longest-to-shortest pattern, we should probably make this a listfor explicit ordering

def tm(tagPat=r'', repl=r'', rename=None, wikiKey=None, refs=(), notes=None):
    "build & store a tag-map entry"
    TagMap.tagMappings[tagPat] = TagMap(tagPat, repl, rename, wikiKey, refs, notes)

# ----- simple tag transforms --------

tm(  # 은/는 - turn topic-marking partcile into subject-marker (I think this is right??)
    tagPat=r'(은|는):JX', repl=r'\1:JKS',
)

# note that in the defs below, any def that includes a node rename field will add a unique integer suffix to the replacing synthetic tag
#  so that unambiguous node renaming is possible.  Such synthetic tags MUST be included with a trailing ".*" in the chunking grammar so that it
#  matches all gnerated integer-suffixed variations of the base synthetic tag

# ----- dependent (aka bound) noun forms --------  map to DNF.* + DependentNounForm node rename

# ----- particles --------  map to PRT.* + Particle node rename

tm( # 들 pluralizer
    tagPat=r'들:(TM|XSN)', repl=r'들:PRT',
    rename="Particle:Plural",
    refs=("htsk:/unit1/unit-1-lessons-9-16/lesson-12/#kp1", ),
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