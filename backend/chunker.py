#  backend/chunker.py  - takes a mapped POS list and builds an NLTK chunking under a RegExp Korean chunking grammar
#
#
__author__ = 'jwainwright'

import nltk

# Korean phrase NLTK chunking grammar
 
class Chunker(object):
    "finds phrase chunks in the POS list produced by the KHaiii phoneme analyzer"

    # the main NLTK chunking grammar


    grammar = r"""

        Punctuation:        {<SP|SS|SE|SO|SW|SWK>}

        DescriptiveVerb:    {<VA|VCP|VCN|VAND.*>}
        Verb:               {<VV|VX|DescriptiveVerb|VND.*>}
        NominalizedVerb:    {<Verb><PNOM.*>}
        AuxiliaryVerb:      {<EC|NEC.*><Verb>}
                            {<AUX.*>}
        VerbAndAuxiliary:   {<Verb><AuxiliaryVerb>}

        Adverb:             {<MAG>}
                            {<VA|VAND.*><EC>}
        VerbPhrase:         {<Adverb|AdverbialPhrase>*<Verb|VerbAndAuxiliary><EP|PSX.*>*}

        Count:              {<NN.*><MM|NUM.*|SN><NNB|NNG>*}  # Count
        Noun:               {<NN.*|NR|SL|NP|NominalizedVerb>}       # Noun

        Possessive:         {<Noun><JKG>}
        Adjective:          {<VerbPhrase><ETM>}
                            {<Adverb>}
                            {<Possessive>}
        AdjectivalPhrase:   {<Adjective><Adjective>*<Noun|Count>}

        AdverbialPhrase:    {<AdjectivalPhrase|Noun><EC|ADVEC.*><JX>*}

        Determiner:         {<MM>}

        NounPhrase:         {<Determiner>*<Noun|Count|AdjectivalPhrase><Noun>*<XSN>*<JKB>*<JX|PRT.*>*<AdverbialPhrase>*}  # NounPhrase
        Conjunction:        {<NounPhrase><JC|CON.*>}

        TopicPhrase:        {<Conjunction>*<NounPhrase><TOP.*>}
        SubjectPhrase:      {<Conjunction>*<NounPhrase><JKS>}
        ComplementPhrase:   {<Conjunction>*<NounPhrase><JKC>}
        ObjectPhrase:       {<Conjunction>*<NounPhrase><JKO>}     # ObjectPhrase

        Phrase:             {<AdverbialPhrase|NounPhrase|ObjectPhrase|ComplementPhrase|SubjectPhrase|TopicPhrase>}
                            {<Punctuation>*<Phrase><Phrase>*<Punctuation>}

        EndingSuffix:       {<EF>}
        ConnectingSuffix:   {<EC|ADVEC.*|CEC.*>}

        SubordinateClause:  {<Phrase><Phrase>*<VerbPhrase><ConnectingSuffix>}
        Predicate:          {<VerbPhrase><EndingSuffix>}
        MainClause:         {<Phrase><Phrase>*<Predicate>}
        Sentence:           {<SubordinateClause>*<MainClause>}


    """

    # the following is an attempt to reproduce the recursive-descent grammar.  It doesn't work, largely because of ambiguities that are
    #  resolved in the R.D. parser by full backtracking and looking for longest alternatives in all 'anyOneOf' rules
    #  may still be usable with some re-ordering effort & further context-sensitve tag-mapping
    #
    # grammar = r"""
    #     AdverbialPhrase:    {<AdjectivalPhrase|Noun><EC|ADVEC.*><JX|PRT.*>*}
    #
    #     NominalizedVerb:    {<Verb><EP|PSX.*>*<PNOM.*>}
    #     SimpleNoun:         {<NN.*|NR|SL|NP>}
    #
    #     Possessive:         {<Noun><JKG>}
    #
    #     AuxiliaryVerbPattern: {<AUX.*>}
    #     AuxiliaryVerb:      {<EC|NEC.*><Verb>}
    #                         {<AuxiliaryVerbPattern>}
    #     VerbAndAuxiliary:   {<Verb><AuxiliaryVerb><AuxiliaryVerb>*}
    #     Adverb:             {<MAG>}
    #                         {<VA|VCP|VCN|VAND.*><EC>}
    #     Adverbial:          {<Adverb|AdverbialPhrase>}
    #     VerbPhrase:         {<Adverbial>*<Verb|VerbAndAuxiliary><EP|PSX.*>*}
    #     Adjective:          {<VerbPhrase><ETM>}
    #                         {<Adverb>}
    #                         {<Possessive>}
    #     AdjectivalPhrase:   {<Adjective><Adjective>*<Noun|Count>}
    #
    #
    #     Counter:            {<NNB|NNG>}
    #     Number:             {<MM|NUM.*|SN>}
    #     Count:              {<SimpleNoun><Number><Counter>*}
    #     Noun:               {<SimpleNoun|NominalizedVerb>}       # Noun
    #     Determiner:         {<MM>}
    #
    #     SimpleNounPhrase:   {<Determiner>*<Noun|Count|AdjectivalPhrase><Noun>*<XSN>*<JKB>*<JX|PRT.*>*<AdverbialPhrase>*}  # NounPhrase
    #     NounPhrase:         {<SimpleNounPhrase|CombinedNounPhrase|PrepositionalPhrase>}
    #     PrepositionalPhrase: {<SimpleNounPhrase><PRP.*>}
    #     Conjunction:        {<NounPhrase><JC|CON.*>}
    #     CombinedNounPhrase: {<Conjunction>*<SimpleNounPhrase>}
    #
    #     Interjection:       {<IC>}
    #     Punctuation:        {<SP|SS|SE|SO|SW|SWK>}
    #
    #     TopicPhrase:        {<Conjunction>*<NounPhrase><TOP.*>}
    #     SubjectPhrase:      {<Conjunction>*<NounPhrase><JKS>}
    #     ComplementPhrase:   {<Conjunction>*<NounPhrase><JKC>}
    #     ObjectPhrase:       {<Conjunction>*<NounPhrase><JKO>}     # ObjectPhrase
    #
    #     Phrase:             {<Punctuation>*<AdverbialPhrase|NounPhrase|ObjectPhrase|ComplementPhrase|SubjectPhrase|TopicPhrase><Interjection>*<Punctuation>*}
    #
    #     EndingSuffix:       {<EF>}
    #     ConnectingSuffix:   {<EC|ADVEC.*|CEC.*>}
    #
    #     Predicate:          {<VerbPhrase><EndingSuffix>}
    #     MainClause:         {<Phrase><Phrase>*<Predicate>}
    #     SubordinateClause:  {<Phrase>*<VerbPhrase><ConnectingSuffix><Punctuation>*}
    #     Sentence:           {<SubordinateClause>*<MainClause>}
    # """

    # annotations for above rules will appear in hover popups in displayedp arse tree
    ruleAnnotations = {
        "Adjective":    {"descr": "An adjective formed from a descriptive verb-stem and an adverbial particle",
                         "refs": {"ttmik": "/lessons/level-3-lesson-13",
                                  "htsk": "/unit1/unit-1-lessons-1-8/unit-1-lesson-4/#ua"},},
        "Possessive":    {"descr": "A noun followed by the '의' particle indicates possession, similar to 's in English",
                         "refs": { "ttmik": "/lessons/l6l3",
                                   "htsk": "unit1/unit-1-lessons-1-8/unit-1-lesson-3/#의" }, },
    }

    parser = None

    @classmethod
    def parse(cls, posList, trace=1):
        "apply the NLTK chunking parser under above grammar"
        if not cls.parser:
            cls.parser = nltk.RegexpParser(cls.grammar, loop=2)
        #
        print(cls.parser)
        chunkTree = cls.parser.parse(posList, trace=trace)

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
        #
        return chunkTree

    @classmethod
    def phraseList(cls, chunkTree):
        "generates phrase list from given chunkTree"
        # generate phrase-descriptors from top-level subtrees
        hiddenTags = { 'Substantive', 'Constituent', 'NounPhrase', 'Connection', }
        def flattenPhrase(t, phrase):
            for st in t:
                if isinstance(st, nltk.Tree):
                    phrase = flattenPhrase(st, phrase)
                    if st.label() not in hiddenTags:
                        phrase.append({"type": 'tree', "tag": st.label()})
                else:
                    phrase.append({"type": 'word', "word": st[0].strip(), "tag": st[1]}) # st[1][0] if st[1][0] in ('N', 'V') else st[0].strip()
            return phrase
        #
        phrases = []
        for t in chunkTree:
            # elide degenerate tree nodes (those with singleton children)
            while isinstance(t, nltk.Tree) and len(t) == 1:
                t = t[0]
            if isinstance(t, nltk.Tree):
                phrase = flattenPhrase(t, [])
                if t.label() not in hiddenTags:
                    phrase.append({"type": 'tree', "tag": t.label()})
                phrases.append(phrase)
            else:
                phrases.append([{"type": 'word', "word": t[0].strip(), "tag": t[1]}])
        #
        return phrases
