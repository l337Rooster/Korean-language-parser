#  backend/tagmap.py  - manages POS special-case tag mapping
#
#
__author__ = 'jwainwright'


class TagMap(object):
    "holds a tag-mapping spec"

    tagMappings = {}

    def __init__(self, tagPat, repl, rename, wikiKey, refs, notes):
        self.tagPat = tagPat
        self.repl = repl
        self.rename = rename
        self.wikiKey = wikiKey
        self.refs = refs
        self.notes = notes


def tm(tagPat=r'', repl=r'', rename=None, wikiKey=None, refs=[], notes=None):
    "build & store a tag-map entry"
    TagMap.tagMappings[tagPat] = TagMap(tagPat, repl, rename, wikiKey, refs, notes)


# synthetic tag patterns -
#    patterns of these word:POC strings are preprocessed to define new
#    synthetic word:POC tags used in the chunking grammar below
#  at present, these are applied in the order longest-to-shortest pattern, we should probably make this a listfor explicit ordering

tagMappings = {
    r'들:(TM|XSN)': r'들:PLU',  # pluralizer
    r'기:(ETN|NNG)': r'기:GNOM',  # nominalizer
    r'(ㄴ|는|ㄹ):ETM;것:NNB': r'\1 것:GNOM',  # nominalizer
    r'(은|는):JX': r'\1:JKS',  # turn topic-marking partcile into subject-marker (I think this is right??)
    r'(ㄹ|을|를):ETM;거:NNB;이:VCP': r'\1 거 이:FUT',  # ㄹ/를 거 이다 future-tense conjugator (hack!)
    r'전:NNG;에:JKB': r'전에:BEF',  # before
    r'때문:NNB;에:JKB': r'때문에:BEC',  # because
    r'및:MAG': r'및:ALS',  # also connector (why is it an adverb??)
    r'또는:MAG': r'또는:ALT',  # alternative connector (why is it an adverb??)
    r'에:JKB;(대하|관하):VV;([^:]+):EC': r'에 \1\2:PRP',  # preposition "about
}


# ----- noun sufffixes --------  map to NSX + NounSuffix node rename

tm(  # 들 pluralizer
    tagPat=r'들:(TM|XSN)', repl=r'들:NSX',
    rename="NounSuffix:Plural",
    wikiKey='',
    refs=("ttmik:", "htsk:"),
    notes="",
)

tm(  # 들 pluralizer
    tagPat=r'들', repl=r':NSX',
    rename="NounSuffix:",
    wikiKey='',
    refs=("ttmik:", "htsk:"),
    notes="",
)

tm(  # 들 pluralizer
    tagPat=r'들', repl=r':NSX',
    rename="NounSuffix:",
    wikiKey='',
    refs=("ttmik:", "htsk:"),
    notes="",
)

tm(  # 들 pluralizer
    tagPat=r'들', repl=r':NSX',
    rename="NounSuffix:",
    wikiKey='',
    refs=("ttmik:", "htsk:"),
    notes="",
)


# ----- verb part-of-speech transformation suffixes ---------

# ----- connection suffixes --------

# ----- prepositional phrase suffix patterns -------

tm(  # 전 "before X-ing" prepositional suffix
    tagPat=r'전:NNG;에:JKB', repl=r'전에:PRPP',
    rename="PrepositionalPhrase:Before",
    wikiKey='전',
    refs=("ttmik:lessons/level-3-lesson-10", "htsk:unit1/unit-1-lessons-17-25-2/lesson-24/#242"),
    notes="a time prepositional phrase suffix attached to a series of noun forms to indicate a time before that implied associated with the noun sequence",
)

# ------ special predicate forms ------



