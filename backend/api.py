#  backend/api.py  - Konlpy Korean parser API
#
#
__author__ = 'jwainwright'

import re
from flask import (Flask, request, abort, render_template, Response, jsonify)
from flask_cors import CORS

import konlpy  # see  http://konlpy.org/en/latest/
import nltk

# instantiate Flask (global) app
konlpyApp = Flask('app',
               static_folder="./dist/static",
               template_folder="./dist")
CORS(konlpyApp)
#
konlpyApp.config.update(
    DEBUG=True,
    SECRET_KEY = "iu877hy3jnd8**yd98y334%$#Rjxhg6222",
    SESSION_COOKIE_HTTPONLY = False
)

def run_dev_server():
    "launch Flask dev server"
    konlpyApp.run(host = '0.0.0.0',
               port = 9000,
               debug = True)

# -------- page request handlers --------

parser = None
nodeData = {}

@konlpyApp.route('/analyzer')
def analyzer():
    "Konlpy analyzer main page"
    return render_template("/index.html")

# -------- API handlers ----------------

@konlpyApp.route('/parse/', methods=['POST'])
def parse():
    "parse POSTed Korean sentence"
    # grab sentence to parse
    sentence = request.form.get('sentence')
    if not sentence:
        return jsonify(result="FAIL", msg="Missing sentence")

    # for now, just use the Kkma parser, todo: make this a parameter
    # extract tagged parts of speech
    #words = konlpy.tag.Kkma().pos(sentence)
    #words = konlpy.tag.Kkma().pos(sentence, flatten=False)
    #words = konlpy.tag.Hannanum().pos(sentence, ntags=22)
    # words = konlpy.tag.Hannanum().pos(sentence, ntags=22, flatten=False)
    words = konlpy.tag.Komoran().pos(sentence)
    #words = konlpy.tag.Komoran().pos(sentence, flatten=False)
    #words = konlpy.tag.Mecab().pos(sentence)
    #words = konlpy.tag.Mecab().pos(sentence, flatten=False)
    #words = konlpy.tag.Twitter().pos(sentence)

    konlpy.utils.pprint(words)
    posString = ';'.join((w[0] + ':' + w[1]) for w in words)
    print(posString)

    # define an nltk chunking grammar (again just for Kkma for now)
    # todo: needs building out, is parser-specific
    grammar = """
    np: {<N.*><J.*>?}   	# Noun phrase
    vp: {<V.*><E.*>?}       # Verb phrase
    ap: {<A.*>*}            # Adjectival phrase
    """
    # special-case tag mappings
    tagMapping = {
        r'들:(TM|XSN)':              r'들:PLU',       # pluralizer
        r'기:ETN':                   r'기:GNOM',      # nominalizer
        r'는:ETM;것:NNB':             r'는 것:GNOM',    # nominalizer
        r'때문:NNB;에:JK(M|B)':        r'때문에:BEC',     # because
        r'에:JKM;따르:VV;아서:ECD':     r'에 따라서:BYF',   # depending on, by following  KKama
        r'에:JKM;따르:VV;아:ECS':      r'에 따라:BYF',   #   "  " (alt)
        r'에:JKB;따라서:MAJ':          r'에 따라서:BYF',  # "  " (alt)  Kormoran
        r'에:JKB;따르:VV;아:EC':       r'에 따라:BYF',  # "  " (alt)  Kormoran
        r'(은|는|이|가):JX':           r'\1:JKS',       # subject marker
        r'(았|었):EPT?':              r'\1:TM',       # tense marker
        r'ㅁ:ETN;으로써:JKB':          r'ㅁ 으로써:BYI'  # by V-ing
    }

    tagString = ';' + posString + ';'
    for old, new in tagMapping.items():
        tagString = re.sub(';' + old + ';', ';' + new + ';', tagString)
    mappedWords = [tuple(pos.split(':')) for pos in tagString.strip(';').split(';')]
    print(mappedWords)

    grammar = r"""
        Noun:           {<N.*>}
        Verb:           {<V.*>}
                        {<N.*><XSV>}  # ㅎ다 verb
        TenseMarker:    {<TM>}
        NominalizedVerb: {<Verb><TenseMarker>?<GNOM>}
        PluralNoun:     {<Noun|NominalizedVerb><PLU>}
        ObjectNoun:     {<Noun|PluralNoun|NominalizedVerb><JKO>}
        SubjectNoun:    {<Noun|PluralNoun|NominalizedVerb><JKS>}
        NounPhrase:     {<Noun|NominalizedVerb|PluralNoun|ObjectNoun|SubjectNoun>}
        Because:        {<NounPhrase><BEC>}
        ByFollowing:    {<NounPhrase><BYF>}
        ByDoing:        {<Verb><BYI>}
    """

    # [('그', 'NP'), ('가', 'JKS'), ('규칙', 'NNG'), ('을', 'JKO'), ('어기', 'VV'), ('었', 'TM'), ('기', 'NOM'), ('때문에', 'BEC'), ('규칙', 'NNG'), ('에', 'JKB'), ('따라서', 'MAJ'), ('그', 'NP'), ('를', 'JKO'), ('처벌', 'NNG'), ('하', 'XSV'), ('ㅁ', 'ETN'), ('으로써', 'JKB'), ('본보기', 'NNG'), ('를', 'JKO'), ('보이', 'VV'), ('는', 'ETM'), ('것', 'NNB'), ('이', 'VCP'), ('다', 'EF'), ('.', 'SF')]

    # gen chunk tree from the word-POS list under the above chunking grammar
    parser = nltk.RegexpParser(grammar)
    chunkTree = parser.parse(mappedWords)
    print(chunkTree.pprint())

    # recursively turn the chunk tree into a Python nested dict for the JSON response
    def asDict(chunk):
        while isinstance(chunk, nltk.Tree) and len(chunk) == 1:
            # flatten degenerate tree nodes
            chunk = chunk[0]
        if isinstance(chunk, nltk.Tree):
            return dict(type='tree', tag=chunk.label(), children=[asDict(t) for t in chunk])
        else:
            return dict(type='pos', word=chunk[0].strip(), tag=chunk[1])
    #
    # flatten top-level subtrees
    def flatten(t, result=''):
        for i, st in enumerate(t):
            if i > 0:
                result += ' + '
            if isinstance(st, nltk.Tree):
                result = flatten(st, result)
                result += ' (' + st.label() + ')'
            else:
                result += st[0].strip() # st[1][0] if st[1][0] in ('N', 'V') else st[0].strip()
        return result
    #
    phrases = []
    for t in chunkTree:
        if isinstance(t, nltk.Tree):
            phrases.append(flatten(t) + ' (' + t.label() + ')')
        else:
            phrases.append(t[0].strip())
    print(phrases)


    #import pprint
    #pprint.pprint(asDict(chunkTree))

    # tree = chunkParser.parse(tagged)
    #
    # for subtree in tree.subtrees():
    #     if subtree.label() == "RELATION":
    #         print("RELATION: "+str(subtree.leaves()))

    # build phrase patterns
    # 그거 아직 안 버렸어요
    # 그거: NP
    # 아직: MAG
    # 안: MAG
    # 버리: VXV
    # 었: EPT
    # 어요: EFN
    #
    #  그거:  Noun
    #  아직 안: Adverbs
    #  버리 었 어요: Verb, past tense, polite
    #
    #"그가 규칙을 어겼기 때문에 규칙에 따라서 그를 처벌함으로써 본보기를 보이는 것이다."
    #
    # 그가 : N+가
    # 규칙을 : N+을
    # "어겼기 때문에" : V+기 때문에
    # "규칙에 따라서" : N+에 따라(서)
    # 그를 : N+를
    # "처벌함으로써 : V+ ㅁ으로써"
    # 본보기를 : N+를
    # "보이는 것이다" : V+는 것이다.
    #
    #  Kormoran:
    # 그: NP
    # 가: JKS
    # 규칙: NNG
    # 을: JKO
    # 어기: VV
    # 었: EP
    # 기: ETN
    # 때문: NNB
    # 에: JKB
    # 규칙: NNG
    # 에: JKB
    # 따라서: MAJ
    # 그: NP
    # 를: JKO
    # 처벌: NNG
    # 하: XSV
    # ㅁ: ETN
    # 으로써: JKB
    # 본보기: NNG
    # 를: JKO
    # 보이: VV
    # 는: ETM
    # 것: NNB
    # 이: VCP
    # 다: EF
    # .: SF

    #  KKama:
    # 그: NP
    # 가: JKS
    # 규칙: NNG
    # 을: JKO
    # 어기: VV
    # 었: EPT
    # 기: ETN
    # 때문: NNB
    # 에: JKM
    # 규칙: NNG
    # 에: JKM
    # 따르: VV
    # 아서: ECD
    # 그르: VV
    # ㄹ: ETD
    # 처벌: NNG
    # 하: XSV
    # ㅁ: ETN

    #

    def noun(w=r'[^:]+'):
        return r'(?P<noun>{0}):(?P<nounTag>N[^;]*);*'.format(w)
    def verb(w=r'[^:]+'):
        return r'(?P<verb>{0}):(?P<verbTag>V[^;]*);*'.format(w)
    def subjMrkr():
        return r'(?P<subjMrkr>[^:]+):(?P<subjMrkrTag>JKS[^;]*);*'
    def objMrkr():
        return r'(?P<objMrkr>[^:]+):(?P<objMrkrTag>JKO[^;]*);*'
    def tenseMrkr(m=r'[^:]+'):
        return r'(?P<tenseMrkr>{0}):(?P<tenseMrkrTag>EPT[^;]*);*'.format(m)
    def marker(m=r'[^:]+', t=r'(J|E)[^:]+'):
        return r'(?P<mrkr>{0}):(?P<mrkrTag>{1});*'.format(m, t)
    def nominalizer(n=r'기'):
        return r'(?P<nominalizer>{0}):(?P<nominalizerTag>ETN[^;]*);*'.format(n)   # todo: hey, don't forget 는것
    def because():
        return r'때문:NNB;에:JKM;*'

    def plural():
        return r''

    def optional(*optionals):
        return ''.join('(' + o + ')*' for o in optionals)
    def optionalOr(*optionals):
        return '(' + '|'.join('(' + o + ')' for o in optionals) + ')'

    # def nounPhrase():
    #     return \
    #     ((noun() + optional(plural()) + optionalOr(subjMrkr(), objMrkr())),
    #         (verb(), optional(tenseMrkr('었|았'), optional(nominalizer()))


# noun = '*:N*;'
# verb = '*:V*;'
# because = '때문:NNB;에:JKM;'
# plural = '들:XSN;'
#
# nounPhrase = noun + optional(plural) + optionalOr(subjMrkr, objMrkr),
#
# grammar = r"""
#   NP: {<DT|JJ|NN.*>+}          # Chunk sequences of DT, JJ, NN
#   PP: {<IN><NP>}               # Chunk prepositions followed by NP
#   VP: {<VB.*><NP|PP|CLAUSE>+$} # Chunk verbs and their arguments
#   CLAUSE: {<NP><VP>}           # Chunk NP, VP
#   """
#
# grammar = """MEDIA: {<DT>?<JJ>*<NN.*>+}
#                RELATION: {<V.*>}
#                          {<DT>?<JJ>*<NN.*>+}
#                ENTITY: {<NN.*>}"""
#

    # 사람:NNG;들:XSN;은:JX;오:VX;았:EP;어요:EF;.:SF

    # special-case tag mappings
    tagMapping = {
        '들:XSN':            '들:PLU',  # pluralizer
        '기:ETN':            '기:NOM',  # nominalizer
        '때문:NNB;에:JKM':    '때문에:BEC'  # because
    }

    grammar = r"""
        Noun: {<N.*>}
        Verb: {<V.*>}
        TenseMarker: {<EPT>}
        NominalizedVerb: {<Verb><TenseMarker>?<NOM>}
        PluralNoun: {<Noun|NominalizedVerb><PLU>}
        ObjectNoun: {<Noun|PluralNoun|NominalizedVerb><JKO>}
        SubjectNoun: {<Noun|PluralNoun|NominalizedVerb><JKS>}
        NounPhrase: {<Noun|NominalizedVerb|PluralNoun|ObjectNoun|SubjectNoun>}
        Because: {<NounPhrase><BEC>}
    """

    phrasePatterns = [
        (noun() + subjMrkr(), ('{noun}','{subjMrkr}'), ('N', '{subjMrkr} (subject)')),
        (noun() + objMrkr(), ('{noun}','{objMrkr}'), ('N', '{objMrkr} (object)')),
        (verb() + tenseMrkr('었|았') + nominalizer() + because(),
            ('{verb}','{tenseMrkr}','{nominalizer}','때문에'), ('V', '{tenseMrkr} (past)', '{nominalizer} (nominalizer)', '때문에 (because of)')),
        # (noun() + subjMrkr(), ('{noun}','{subjMrkr}'), ('N', '{subjMrkr} (subject)')),
        #
        (r'(?P<rest>.*)', ('rest',), ('{rest}',)),
    ]

    varPat = re.compile(r'\{(?P<var>[^\}]+)\}')

    parseList = []
    while posString:
        #print('=>', posString)
        for p, phrase, comments in phrasePatterns:
            m = re.match(p, posString)
            if m:
                def expand(vm):
                    var = vm.group('var')
                    # print('   ', var, '  ', m.group(var))
                    return m.group(var) or var
                phrase = [varPat.sub(expand, w) for w in phrase]
                commentary = ' + '.join(varPat.sub(expand, c) for c in comments if '{' not in varPat.sub(expand, c))
                parseList.append((phrase, commentary))
                posString = posString[m.end():].strip(';')
                break
    #
    print(parseList)

    # match.end([group])

    #  'JKS' - subject marker
    #  'JKO' - object marker

    # 그:NP;가:JKS;규칙:NNG;을:JKO;어기:VV;었:EPT;기:ETN;때문:NNB;에:JKM;규칙:NNG;에:JKM;따르:VV;아서:ECD;그르:VV;ㄹ:ETD;처벌:NNG;하:XSV;ㅁ:ETN;으로써:JKM;본보기:NNG;를:JKO;보이:VV;는:ETD;것:NNB;이:VCP;다:EFN;.:SF

    #
    # 그: NP
    # 가: JKS
    # 규칙: NNG
    # 을: JKO
    # 어기: VV
    # 었: EPT
    # 기: ETN
    # 때문: NNB
    # 에: JKM
    # 규칙: NNG
    # 에: JKM
    # 따르: VV
    # 아서: ECD
    # 그르: VV
    # ㄹ: ETD
    # 처벌: NNG
    # 하: XSV
    # ㅁ: ETN
    # 으로써: JKM
    # 본보기: NNG
    # 를: JKO
    # 보이: VV
    # 는: ETD
    # 것: NNB
    # 이: VCP
    # 다: EFN
    # .: SF

    return jsonify(result="OK", posList=words, parseList=parseList, phrases=phrases, parseTree=asDict(chunkTree))

#
if __name__ == "__main__":
    #
    run_dev_server()
