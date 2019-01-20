#  backend/tagmap.py  - manages POS special-case tag mapping
#
#
__author__ = 'jwainwright'

import re
from collections import defaultdict
from pprint import pprint

import nltk

from chunker import Chunker

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
                  "htsk":  {"title": "How to study Korean",  "hostname": "www.howtostudykorean.com"},
                  "kacg":  {"title": "Korean: A Comprehensive Grammar"},
                  "itlk":  {"title": "italki.com answers", "hostname": "www.italki.com"}}

    #  parts-of-speech descriptors
    partsOfSpeech = {
      #  POS-tag    (Wiktionary POS, Khaiii class,         Detail,                          Korean class:POS)
        "NNG":      ("Noun",        "Substantive",      "General noun",                     "체언: 일반 명사"),
        "NNP":      ("Proper Noun", "Substantive",      "Proper noun",                      "체언: 고유 명사"),
        "NNB":      ("Noun",        "Substantive",      "Bound noun, e.g. 것",               "체언: 의존 명사"),
        "NP":       ("Pronoun",     "Substantive",      "Pronoun",                          "체언	: 대명사"),
        "NR":       ("Noun",        "Substantive",      "Number",                           "체언	: 수사"),
        "VV":       ("Verb",        "Inflectional",     "Verb",                             "용언	: 동사"),
        "VA":       ("Adjective",   "Inflectional", "Descriptive verb / Adjective",   "용언	: 형용사"),
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
        "JX":       ("Particle",    "Post-position",    "Auxiliary particle",               "관계언: 보조사"),
        "JC":       ("Particle",    "Post-position",    "Connecting particle",              "관계언: 보조사"),
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
        # note that synthetic tags defined below include a mapping to one of the above basic POS or the additional labeling tags below

        # extra synthetic POS, mostly to label suffix phrases built from the mapping rules
        "AVS":      ("Adverbial\nsuffix",       "Post-position",    "Adverbial suffix",                 ""),
        "VMS":      ("Verb-modifying\nsuffix",  "Post-position",    "Verb-modifying suffix",            ""),
    }

    # explicit labels for select individual phoneme:tag pairs, filled in by TagMap::__init__ for un-mapped definitions
    POS_labels = { }

    def __init__(self, tagPat=r'', repl=r'', basePOS=None, posLabel=None, descr=None, nodeRename="", annotation="", wikiKey=None, refs=(), notes=None):
        self.tagPat = tagPat
        if repl:
            # uniquify synthetic tag & record it if this mapping includes a chunktree node renaming
            self.repl = repl + ("_%d" % TagMap.tagOrdinal); TagMap.tagOrdinal += 1
            self.newTag = self.repl.split(':')[-1] # extract this pattern's synthetic tag
            self.nodeRename = nodeRename; self.annotation = annotation
            self.basePos = basePOS
            # add TM's with replacement tags to the tagMappings table
            TagMap.tagMappings[tagPat] = self
        else:
            # a simple morpheme:tag metadata definition, add to POS_label table
            self.repl = self.newTag = self.nodeRename = self.basePos = None
            # allow alternate morpheme patterns in this case - (m1|m2|..|mn):TAG, splitting them into separate singleton morpheme:TAG entries
            morphemes, tag = tagPat.split(':')
            for m in morphemes.strip('(').strip(')').split('|'):
                TagMap.POS_labels[m + ':' + tag] = self
        self.wikiKey = wikiKey
        self.refs = refs
        self.notes = notes
        self.posLabel = posLabel
        self.descr = descr
        if basePOS:
            # add POS definition for synthetic tag, based on basePOS overriding detail descriptor
            baseDef = TagMap.partsOfSpeech[basePOS]
            TagMap.partsOfSpeech[self.newTag] = (posLabel or baseDef[0], baseDef[1], descr or baseDef[2], baseDef[3])
        if nodeRename:
            # add any renamed rule annotation
            if ':' in nodeRename and annotation:
                Chunker.ruleAnnotations[nodeRename.split(':')[1]] = dict(descr=annotation, refs=refs)

    @classmethod
    def completeInit(cls):
        "complete tag-mapping setup"
        # build mapping pattern list sorted in reducing pattern length (# semis, then char length) to control transform ordering (todo: might need explicit ordering)
        cls.tagMapPatterns = sorted(((tm.tagPat, tm) for tm in cls.tagMappings.values()), key=lambda x: (len(x[0].split(';')), len(x[0])), reverse=True)
        pprint(cls.tagMapPatterns)
        # build node-name mapping table & extract any refs & wikiKeys
        #   maps uniquified synthetic tag to tables that map ancestor node label to renamed label
        for tm in cls.tagMappings.values():
            if tm.nodeRename and ':' in tm.nodeRename:
                old, new = tm.nodeRename.split(':')
                cls.nodeNameMaps[tm.newTag][old] = new
            if tm.wikiKey:
                cls.wikiKeyMap[tm.newTag] = tm.wikiKey
            if tm.refs:
                cls.refsMap[tm.newTag] = cls.getRefsMapEntries(tm.refs)
        #

    @classmethod
    def getRefsMapEntries(cls, refs):
        "build full reference entries from definition ref spec"
        fullRefs = []
        for key, page in refs.items():
            fr = dict(title=cls.references[key]['title'])
            hostname = cls.references[key].get('hostname')
            if hostname:
                fr['slug'] = "https://" + cls.references[key]['hostname'] + page
            else:
                fr['page'] = page
            fullRefs.append(fr)
        return fullRefs

    @classmethod
    def mapTags(cls, posString, morphemeGroups, disableMapping=False):
        "generate a version of the parser's original word:POC string under the below-defined synthetic tag mappings"
        # returns a list of (tag,word) tuples
        tagString = ';' + posString + ';'
        if not disableMapping:
            for tagPat, tm in cls.tagMapPatterns:
                def replTags(m):
                    return m.expand(';' + tm.repl + ';')
                tagString = re.sub(';' + tagPat + ';', replTags, tagString)
        #
        mappedPosList = [tuple(pos.split(':')) for pos in tagString.strip(';').split(';')]
        #
        # build simplified morpheme grouping table for original text layout in tree display
        newGroups = []; tic = 0; ti = 0; tchars = mappedPosList[0][0]
        for word, morphemeList in morphemeGroups:
            morphemes = ''.join(morphemeList)
            newMorphemes = ''; mic = 0
            while True:
                if tic >= len(tchars):
                    ti += 1
                    tchars = mappedPosList[ti][0]
                    tic = 0
                if mic == len(morphemes):
                    break
                newMorphemes += tchars[tic]
                if morphemes[mic] == tchars[tic]:
                    mic += 1
                tic += 1
            newGroups.append([word, newMorphemes])

        pprint(newGroups)
        return mappedPosList, newGroups

    @classmethod
    def mapNodeNames(cls, tree):
        "maps NLTK ChunkTree node names under tag-mapping 'nodeRename' definitions"
        #
        def camelCaseSpacer(label):
            matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', label)
            return ' '.join(m.group(0) for m in matches)
        #
        def walkTree(t, parentList):
            # walk tree looking for terminal nodes with tags that are in the nodeNameMap table
            #   search up for ancestor node with label in the above-selected nodeNameMap entry, taking label rename
            for i, st in enumerate(t):
                if isinstance(st, nltk.Tree):
                    st.set_label(camelCaseSpacer(st.label()))
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
        posTable = {}
        ruleAnnotations = {}
        def walkTree(t):
            # walk tree looking for terminal nodes with tags that are in the refMap or wikiKey tables & build reference items
            for i, st in enumerate(t):
                if isinstance(st, nltk.Tree):
                    # add any tree node grammar rule annotations & refs
                    tag = st.label()
                    annotation = Chunker.ruleAnnotations.get(tag)
                    if annotation:
                        ruleAnnotations[tag] = dict(descr=annotation['descr'],
                                                    refList=cls.getRefsMapEntries(annotation['refs']))
                    # recurse down th etree
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
                            refList.append(dict(title=d['title'], slug=d['slug'].replace("${word}", word)))
                        #
                        wikiKeys[st[0]] = word
                    #
                    refs = cls.refsMap.get(st[1])
                    if refs:
                        refList.extend(refs)
                    if refList:
                        references[st[0]] = refList
                    # add POS reference table entries
                    posEntry = {}
                    tm = cls.tagMappings.get(st[1])
                    if tm:
                        posEntry['notes'] = tm.notes
                    posDef = cls.partsOfSpeech.get(st[1])
                    if posDef:
                        posEntry['wikiPOS'] = posDef[0]
                        posEntry['descr'] = posDef[2]
                    posTable[st[1]] = posEntry
        #
        walkTree(tree)
        #
        return dict(references=references, wikiKeys=wikiKeys, posTable=posTable, ruleAnnotations=ruleAnnotations, )


# ================================== Custom POS tag definitions ==============================

tm = TagMap

# ---------- labeling & reference metadata for specific, un-mapped morpheme:TAG pairs ----------
#
#  note that the apparent RE patterns below are NOT, only |-separated alternate phonemes in parens are supported
tm(tagPat="이:VCP",          posLabel="Copula\nTo be", notes="The positive copula, to be. Always attached directly to the equated noun form")
tm(tagPat="아니:VCN",          posLabel="Copula\nTo not be", notes="The negative copula, to not be. Always attached directly to the equated noun form")

tm(tagPat="의:JKG",          posLabel="Possessive\nParticle", notes="The possessive suffix, attached to the owning entity, indicates ownership of the following entity")
tm(tagPat="(으시|시):EP",      posLabel="Honorific\nMarker", )

tm(tagPat="(이|가):JKS",      posLabel="Subject\nMarker", )
tm(tagPat="(께서):JKS",       posLabel="Honorific\nSubject", )
tm(tagPat="(을|를):JKO",      posLabel="Object\nMarker", refs={})
tm(tagPat="(은|는):JKO",      posLabel="Subject\nMarker", )
tm(tagPat="(이|가):JKC",      posLabel="Complement\nMarker", )

tm(tagPat="(아요|어요|에요):EF", posLabel="Polite\nEnding", )
tm(tagPat="(아|어|야):EF",    posLabel="Informal\nEnding", )
tm(tagPat="다:EF",           posLabel="Plain-form\nEnding", )
tm(tagPat="습니다:EF",        posLabel="Formal\nEnding", )
tm(tagPat="ㄹ게:EF",         posLabel="Future Tense\nSuffix", )
tm(tagPat="네요:EF",          posLabel="Surprised\nEnding", )

tm(tagPat="겠:EP",           posLabel="Intension\nMarker", refs={})
tm(tagPat="(으면|면):EC",     posLabel="If\nSuffix", )

tm(tagPat="(ㄴ|은|는|ㄹ):ETM", posLabel="Adjectival\nSuffix", )
tm(tagPat="(와|과):JC",       posLabel="And/With\nParticle", )
tm(tagPat="만약:NNG",         posLabel="If\nPrefix", )
tm(tagPat="보다:JKB",         posLabel="Comparison\nParticle", )
tm(tagPat="부터:JX",          posLabel="Since\nParticle", )

# -------------- synthetic tag patterns ----------------

#    patterns of these word:POC strings are preprocessed to define new
#    synthetic word:POC tags used in the chunking grammar below
#  at present, these are applied in the order longest-to-shortest pattern, we should probably make this a listfor explicit ordering

# note that in the in the processing of the defs below, all new tags will have a "_nnn" appended to make them unique and
# assist in unambiguous mapping to the associated metadata in chuck-tree post-processing.  So, any references to these
# new tags in the chunking grammar MUST be included with a trailing ".*" in the chunking grammar so that it
#  matches all generated integer-suffixed variations of the base synthetic tag

# ------------ tag-sequence foldings & renamings ---------------

tm(  # noun-derived verbs, N하다, N되다, N당하다, N시키다, etc. - combine XR|NN & VND suffix into a single NDV (noun-derived verb) verb
    tagPat=r'([^:]+):(XR|NNG);([^:]+):XSV', repl=r'\1\3:VND',
    basePOS="VV", descr="Verb derived from a noun",
    notes="Noun-derived verb - ${1} + ${3}",
)

tm(  # noun-derived adjectives,  - combine XR|NN & XSA suffix into a single VAND (noun-derived adjective) adjective
    tagPat=r'([^:]+):(XR|NNG);([^:]+):XSA', repl=r'\1\3:VAND',
    basePOS="VA", descr="Adjective derived from a noun",
    notes="Noun-derived adjective - ${1} + ${3}",
)

tm(  # numbers
    tagPat=r'(.*):NR', repl=r'\1:NUM', basePOS="NR", posLabel="Number",
)

tm(  # V 지:EC negation connector  NEC.*
    tagPat=r'(지):EC', repl=r'\1:NEC', basePOS="EC", posLabel="Negation\nConnector",
)

# ----- dependent (aka bound) noun forms --------  map to DNF.* + DependentNounForm node rename

# ----- particles --------  usually map to PRT.* + NounPhrase node rename

tm( # 은/는 topic marker
    tagPat=r'(ㄴ|은|는):JX', repl=r'\1:TOP',
    basePOS="JX", posLabel="Topic\nMarker",
    nodeRename="Noun Phrase:Topic", descr="Topic-marker",
)

tm( # 들 pluralizer
    tagPat=r'들:(TM|XSN)', repl=r'들:PRT',
    basePOS="VA", posLabel="Plural\nParticle", descr="Pluralizer",
    # nodeRename="Noun Phrase:Plural",
    refs={"htsk": "/unit1/unit-1-lessons-9-16/lesson-12/#kp1", },
)

tm( # 밖에 other-than particle
    tagPat=r'밖에:JX', repl=r'밖에:PRT',
    basePOS="JX",
    nodeRename="Noun Phrase:Other Than", annotation="Noun + 밖에 + negative predicate implies the predicate applies to everything outside or other-than the noun",
    refs={"ttmik": "/lessons/level-2-lesson-13", "htsk": "/unit-3-intermediate-korean-grammar/lessons-67-75/lesson-69/#691", },
)

tm( # ~도 as-well/also/too particle
    tagPat=r'도:JX', repl=r'도:PRT',
    basePOS="JX", posLabel="Also/Too\nSuffix",
    #nodeRename="NounPhrase:As Well",
    annotation='Noun + 도 is similar to the English noun-qualifying phrases "in addition", "as well" and "too".',
    refs={"htsk": "/unit-1-lessons-1-8/unit-1-lesson-4/#do", },
)


# ----- nominal forms -- transforming verbs & adjectives to nouns ---------  mapping (usually) to PNOM.*

tm( # 기/음 nominalizer
    tagPat=r'(기|음):(ETN|NNG)', repl=r'\1:PNOM',
    basePOS="VMS", descr="Suffix transforming a verb into a noun",
    refs={"ttmik": "/lessons/level-2-lesson-19", "htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-26-33/lesson-29"},
)

tm( # 는것 nominalizer
    tagPat=r'(ㄴ|는|ㄹ):ETM;것:NNB', repl=r'\1 것:PNOM',
    basePOS="VMS", descr="Suffix transforming a verb into a noun",
    wikiKey='것',
    refs={"ttmik": "/lessons/level-2-lesson-19", "htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-26-33/lesson-26/"},
    notes="",
)

# ----- connection suffixes --------  mapping to CON.* & renaming Connection

tm( # 및 "also" connecting adverb(??)
    tagPat=r'및:MAG', repl=r'및:CON',
    basePOS="MAG", descr="Connecting adverb",
    nodeRename="Connection:Also",
)

tm( # 또는 "alternatives" connecting adverb(??)
    tagPat=r'또는:MAG', repl=r'또는:CON',
    basePOS="MAG", posLabel="Alternates\nAdverb", descr="Adverb connecting alternatives",
    nodeRename="Connection:Alternatives",
)

# ----- adverbial predicate-phrase connectors --------  mapping to ADVEC.* & renaming AdverbialPhrase

tm( # 에/에서/서 Location/Time marker
    tagPat=r'(서|에|에서):JKB', repl=r'\1:ADVEC',
    basePOS="JKB", posLabel="Time/Place\nMarker",
    # nodeRename="NounPhrase:Location/Time",
    refs={"ttmik": "/lessons/l1l18", "htsk": "/unit-1-lessons-9-16/lesson-12/#kp3", },
)

tm( # 에게:JKB "to/at/for" particle
    tagPat=r'(에게|한테|께):JKB', repl=r'\1:ADVEC',
    basePOS="JKB",
    #nodeRename="Noun Phrase:To/for/at",
    refs={"ttmik": "/lessons/level-2-lesson-7", "htsk": "/unit1/unit-1-lessons-9-16/lesson-13/#kp3", },
)

tm( # 어서 "reason" adverbial verb-phrase suffix
    tagPat=r'어서:EC', repl=r'어서:ADVEC',
    basePOS="EC", posLabel="Reason-giving\nSuffix", descr="Reason-giving connecting suffix",
    #nodeRename="Adverbial Phrase:Reason",
    refs={},
)

tm( # ~ㄹ/을 때 "when/during the time" adverbial verb-phrase suffix
    tagPat=r'(ㄹ|을):ETM;때:NNG', repl=r'\1 때:ADVEC',
    basePOS="EC", posLabel="When\nSuffix", descr="At-a-time-when connecting suffix",
    #nodeRename="Adverbial Phrase:When",
    refs={"htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-42-50/lesson-42/#422",
          "kacg": "Section 7.2.1, pp 346"},
)

tm( # ~ㄹ/을 때부터 "since the time when ~" adverbial verb-phrase suffix
    tagPat=r'(ㄹ|을):ETM;때:NNG;부터:JX', repl=r'\1 때부터:ADVEC',
    basePOS="EC", posLabel="Since Time When\nSuffix", descr="Since-the-time-when connecting suffix",
    #nodeRename="Adverbial Phrase:Since When Phrase",
    refs={},
)

# ------ sequential connectors --------------  mapping to CEC.*

tm(  # ~라고 subordinate clause connector  CEC.*
    tagPat=r'(라고):EC', repl=r'\1:CEC', basePOS="EC", posLabel="Clause\nConnector",
)

tm(  # ~지만 subordinate clause connector  CEC.*  # todo: these will probably move into specific pattern definitions
    tagPat=r'(지만):EC', repl=r'\1:CEC', basePOS="EC", posLabel="Clause\nConnector",
)

tm(  # ~ㄴ/는 데:EC subordinate clause connector  CEC.*
    tagPat=r'(ㄴ데|은 데|는 데):EC', repl=r'\1:CEC', basePOS="EC", posLabel="Clause\nConnector",
)


# ----- prepositional phrase suffix patterns -------  mapping to PRP.* & renaming PrepositionalPhrase

tm( # 전 "before X-ing" prepositional suffix
    tagPat=r'전:NNG;에:JKB', repl=r'전에:PRP',
    basePOS="MAG", descr="Adverbial phrase", posLabel="Before\nSuffix",
    nodeRename="Prepositional Phrase:Before Phrase",
    wikiKey='전',
    refs={"ttmik": "/lessons/level-3-lesson-10", "htsk": "/unit1/unit-1-lessons-17-25-2/lesson-24/#242"},
    notes="a time prepositional phrase suffix attached to a series of noun forms to indicate a time before that implied associated with the noun sequence",
)

tm( # 후|다음|뒤)에 "after X-ing" prepositional suffix
    tagPat=r'(후|다음|뒤):NNG;에:JKB', repl=r'\1에:PRP',
    basePOS="MAG", descr="Adverbial phrase", posLabel="After\nSuffix",
    nodeRename="Prepositional Phrase:After Phrase",
    wikiKey='후',
    refs={"ttmik": "/lessons/level-3-lesson-19;ticket=153893", "htsk": "/unit1/unit-1-lessons-17-25-2/lesson-24/"},
)

tm( # 때문에 "because X" prepositional suffix
    tagPat=r'때문:NNB;에:JKB', repl=r'때문에:PRP',
    basePOS="MAG", descr="Adverbial phrase",
    nodeRename="Prepositional Phrase:Because Phrase",
    wikiKey='때문',
    refs={"htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-34-41/lesson-38/"},
)

tm( # 에대해 "about X" prepositional suffix
    tagPat=r'에:JKB;(대하|관하):VV;([^:]+):(EC|ETM)', repl=r'에 \1\2:PRP',
    basePOS="EC", descr="Prepositional connecting suffix",
    nodeRename="Prepositional Phrase:About Phrase",
    wikiKey='대하다',
    refs={"htsk": "/unit1/unit-1-lessons-9-16/lesson-13/#kp6"},
)

# ------ auxiliary verb forms ---------  usually mapping to AUX.*

tm( # ~아/어 보이다 to seem/look like
    tagPat=r'(아|어|여):EC;보이:(VV|VX)', repl=r'\1 보이:AUX',
    basePOS="VX", posLabel="Seems Like\nLooks Like", descr="Auxiliary verb pattern: to seem like or look like",
    #nodeRename="Verb With Auxiliary:Verb + Auxiliary",
    wikiKey='보이다',
    refs={"htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-34-41/lesson-36/#363", "ttmik": "/lessons/ttmik-l9l12"},
)

tm( # ~아/어 보다 to try
    tagPat=r'(아|어|여):EC;보:(VV|VX)', repl=r'\1 보:AUX',
    basePOS="VX", posLabel="Try/Attempt", descr="Auxiliary verb pattern: to try or to attempt",
    #nodeRename="VerbWithAuxiliary:Verb + Auxiliary",
    wikiKey='보다',
    refs={"htsk": "/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-26-33/lesson-32/#323"},
)

tm( # ~아/어 버리다 done to completion
    tagPat=r'(아|어|여):EC;버리:(VV|VX)', repl=r'\1 버리:AUX',
    basePOS="VX", posLabel="To Complete", descr="Auxiliary verb pattern: done to completion",
    #nodeRename="Verb With Auxiliary:Verb + Auxiliary",
    wikiKey='버리다',
    refs={},
)

tm( # 고 싶다 want-to auxiliary form
    tagPat=r'고:EC;싶:VX', repl=r'고 싶:AUX',
    basePOS="VX", posLabel="Want to", descr="Want-to auxiliary verb form",
    #nodeRename="Verb Suffix:WantTo",
    wikiKey="싶다",
    refs={"ttmik": "/lessons/l1l13", "htsk": "/unit1/unit-1-lessons-17-25-2/lesson-17/#co5"},
    notes="",
)

# A/V + 아/어 버리다
#

# ------ nominal verb forms V 기 ... ---------  usually mapping to NMF.*

tm( # ~기는 하- indeed
    tagPat=r'기:ETN;는:JX;하:VX', repl=r'기는 하:NMF',
    basePOS="VX", posLabel="Indeed", descr="Nominal verb pattern: indicates an emphatic feeling and is used when the speaker realizes, accepts or concedes that a piece of information (often provided by the interlocutor) is indeed correct.",
    wikiKey='',
    refs={"kacg": "Section 2.2.4.12, pp 64" },
)

tm( # ~기나 하-  just
    tagPat=r'기:ETN;나:JX;하:VX', repl=r'기나 하:NMF',
    basePOS="VX", posLabel="Just",
    wikiKey='',
    refs={ },
)

# ------ predicate ending forms ------  mapping to PSX.* & renaming VerbSuffix

tm( # 었 past-tense suffix
    tagPat=r'(았|었):EP', repl=r'\1:PSX',
    basePOS="EP", posLabel="Past tense\nMarker", descr="Past-tense particle",
    nodeRename="Verb Suffix:Past Tense",
    refs={"ttmik": "/lessons/l1l17", "htsk": "/unit1/unit-1-lessons-1-8/unit-1-lesson-5/#vpast"},
    notes="",
)

tm( # ㄹ/를 거 이다 future-tense suffix pattern
    tagPat=r'(ㄹ|을|를):ETM;거:NNB;이:VCP', repl=r'\1 거 이:PSX',
    basePOS="VX", posLabel="Future tense\nAuxiliary", descr="Future-tense predicate suffix",
    nodeRename="Verb Suffix:Future Tense",
    wikiKey="none",
    refs={"ttmik": "/lessons/level-2-lesson-1-future-tense", "htsk": "/unit1/unit-1-lessons-9-16/unit-1-lesson-9/#ifut"},
    notes="",
)

tm( # ~ㄴ/은가(요) question-ending descriptive-verb suffix
    tagPat=r'(ㄴ가|은가|은가요):(EC|EF)', repl=r'\1:PSX',
    basePOS="EF", posLabel="Question\nSuffix", descr="Question-forming suffix, used after descriptive verbs or the copula (이다); a softer form than ~(으)냐",
    #nodeRename="AuxiliaryVerbForm:Seems/Looks",
    wikiKey='',
    refs={"htsk": "/unit1/unit-1-lessons-17-25-2/lesson-21-asking-questions-in-korean-why-when-where-and-who/#214",
          "itlk": "/question/457643" },
)

# ------------

TagMap.completeInit()

##  Questions
#
#   점심을 먹은 다음에, 도서관에 갔어요.  - should 'after' also bind the related (opening) object?;   Should N에 phrase be called "Location"? - ambiguous with AtTime