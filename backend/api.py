#  backend/api.py  - Konlpy Korean parser API
#
#
__author__ = 'jwainwright'

import re
from pprint import pprint, pformat

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
               port = 9000, #80, # 9000,
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

    # for now, just use the Komoran parser, todo: make this a parameter
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
    # print(posString)

    # define an nltk chunking grammar (again just for Komoran for now)
    # todo: needs building out, is parser-specific
    grammar = """
    np: {<N.*><J.*>?}   	# Noun phrase
    vp: {<V.*><E.*>?}       # Verb phrase
    ap: {<A.*>*}            # Adjectival phrase
    """
    # synthetic tag patterns -
    #    patterns of these word:POC strings are preprocessed to define new
    #    synthetic word:POC tags used in the chunking grammar below
    tagMappings = {
        r'들:(TM|XSN)':              r'들:PLU',       # pluralizer
        r'기:(ETN|NNG)':             r'기:GNOM',      # nominalizer
        # r'(는|ㄹ):ETM;것:NNB;이:VCP;기:ETN': r'\1 것이기:GNOM',    # 갔이다 nominalizer
        r'로:JKB':                   r'로:WIT',       # with/in/by particle
        r'(는|ㄹ):ETM;것:NNB':         r'\1 것:GNOM',    # nominalizer
        r'때문:NNB;에:JK(M|B)':        r'때문에:BEC',     # because
        r'에:JKM;따르:VV;아서:ECD':     r'에 따라서:BYF',   # depending on, by following  KKama
        r'에:JKM;따르:VV;아:ECS':      r'에 따라:BYF',   #   "  " (alt)
        r'에:JKB;따라서:MAJ':          r'에 따라서:BYF',  # "  " (alt)  Kormoran
        r'에:JKB;따르:VV;아:EC':       r'에 따라:BYF',  # "  " (alt)  Kormoran
        r'(은|는|이|가):JX':           r'\1:JKS',       # subject marker
        r'(았|었|ㄹ):(EPT?|ETM)':      r'\1:TM',       # tense marker
        r'ㅁ:ETN;으로써:JKB':          r'ㅁ 으로써:BYI',  # by V-ing
        r'면:EC':                    r'면:CON',       # conditional
        r'거나:EC':                   r'거나:OR',       # disjunction (either/or)
        r'는:ETM;것:NNB;이:VCP;다:EF': r'는 것이다:THI',   # not sure!!! todo: ask Philjae
        r'(아|어|고):EC;있:V(V|X);([^:]+):EF': r'\1 있\3:PRO', # progressive
        r'을:ETM;때:NNG':             r'을 때:WHI',     # while/when/at the time of
        r'(아|어):EC;보:VV;시:EP;어요:EF': r'\1 보세요:PLT',  # please try to    아:EC;보:VV;시:EP;어요:EF
        r'(아|어):EC;보:VV;았:EP;어요:EF':   r'\1 보다:TRY',    # try
    }

    # generate a version of the parser's original word:POC string including synthetic tag mappings above
    tagString = ';' + posString + ';'
    for old, new in sorted(tagMappings.items(), key=lambda x:len(x[0]), reverse=True):
        tagString = re.sub(';' + old + ';', ';' + new + ';', tagString)
    mappedWords = [tuple(pos.split(':')) for pos in tagString.strip(';').split(';')]
    # print(mappedWords)

    grammar = r"""
        TenseMarker:    {<TM>}
        Adjective:      {<VA><ETM>}
        PlainNoun:      {<N.*><XSN>?}
        SimpleVerb:     {<V.*><TenseMarker>?<EF|EC>?}
        HadaVerb:       {<PlainNoun><XSV><EF|EC>?}
        PlainVerb:      {<SimpleVerb|HadaVerb>}
        Progressive:    {<PlainVerb><PRO>}
        Verb:           {<PlainVerb|Progressive>}
        NominalizedVerb: {<Verb><GNOM><EF>?}
        PluralNoun:     {<PlainNoun|NominalizedVerb><PLU>}
        Noun:           {<PlainNoun|PluralNoun|NominalizedVerb>}
        Object:         {<Noun><JKO>}
        Subject:        {<Noun><JKS>}
        Location:       {<Noun><JKB>}
        With:           {<Noun><WIT>}
        Possessive:     {<Noun><JKG>}
        NounPhrase:     {<Noun|Object|Subject|Location>}
        AdjectivalPhrase: {<MM><NounPhrase>}
        Conditional:    {<Verb><CON>}
        Or:             {<Verb><OR>}
        Because:        {<NounPhrase><BEC>}
        ByFollowing:    {<NounPhrase><BYF>}
        ByDoing:        {<Verb><BYI>}
        Thinging:       {<Verb><THI>}
        While:          {<Verb><WHI>}
        Try:            {<Verb><TRY>}
        PleaseTry:      {<Verb><PLT>}
        VerbPhrase:     {<MAG>?<Verb>}
    """
    # 그:NP;가:JKS;규칙:NNG;을:JKO;어기:VV;었:EP;기:ETN;때문:NNB;에:JKB;규칙:NNG;에:JKB;따라서:MAJ;그:NP;를:JKO;
    # 처벌:NNG;하:XSV;ㅁ:ETN;으로써:JKB;
    # 본보기:NNG;를:JKO;보이:VV;는:ETM;것:NNB;이:VCP;다:EF;.:SF
    #   서:VV;어:EC;있:VV;을:ETM;때:NNG

    # gen chunk tree from the word-POS list under the above chunking grammar
    parser = nltk.RegexpParser(grammar, trace=1)
    print(parser._stages)
    chunkTree = parser.parse(mappedWords)
    print(chunkTree.pprint())

    # flatten top-level subtrees into phrase structure descriptions
    hiddenTags = { 'NounPhrase', 'VerbPhrase', 'PlainNoun', 'PlainVerb', }
    def flatten(t, phrase):
        for st in t:
            if isinstance(st, nltk.Tree):
                phrase = flatten(st, phrase)
                if st.label() not in hiddenTags:
                    phrase.append(('label', st.label()))
            else:
                phrase.append(('word', st[0].strip())) # st[1][0] if st[1][0] in ('N', 'V') else st[0].strip()
        return phrase
    #
    phrases = []
    for t in chunkTree:
        if isinstance(t, nltk.Tree):
            phrase = flatten(t, [])
            if t.label() not in hiddenTags:
                phrase.append(('label', t.label()))
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
            return dict(type='tree', tag=chunk.label(), children=[asDict(t) for t in chunk])
        else:
            return dict(type='pos', word=chunk[0].strip(), tag=chunk[1])
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

#  'JKS' - subject marker
#  'JKO' - object marker

# noun = '*:N*;'
# verb = '*:V*;'
# because = '때문:NNB;에:JKM;'
# plural = '들:XSN;'
#
# nounPhrase = noun + optional(plural) + optionalOr(subjMrkr, objMrkr),
# example
# grammar = r"""
#   NP: {<DT|JJ|NN.*>+}          # Chunk sequences of DT, JJ, NN
#   PP: {<IN><NP>}               # Chunk prepositions followed by NP
#   VP: {<VB.*><NP|PP|CLAUSE>+$} # Chunk verbs and their arguments
#   CLAUSE: {<NP><VP>}           # Chunk NP, VP
#   """


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

    parseTree = asDict(chunkTree)
    debugging = dict(posList=pformat(words),
                     mappedPosList=pformat(mappedWords),
                     parseList=pformat(parseList),
                     phrases=pformat(phrases),
                     parseTree=pformat(parseTree))

    return jsonify(result="OK",
                   posList=words,
                   mappedPosList=mappedWords,
                   parseList=parseList,
                   phrases=phrases,
                   parseTree=parseTree,
                   debugging=debugging)

#
if __name__ == "__main__":
    #
    run_dev_server()

#  test phrase
#  제 집에 저랑 같이 친구들 갈 거예요