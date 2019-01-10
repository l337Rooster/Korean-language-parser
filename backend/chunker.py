#  backend/chunker.py  - takes a mapped POS list and builds an NLTK chunk under a Korean chunking grammar
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
        NominalizedVerb:    {<Verb><NOM.*>}
        AuxiliaryVerb:      {<EC><Verb>}
                            {<AUX.*>}
        VerbAndAuxiliary:   {<Verb><AuxiliaryVerb>}
        
        Adverb:             {<MAG>}
                            {<VA|VAND.*><EC>}
        VerbPhrase:         {<Adverb>*<Verb|VerbAndAuxiliary><EP|PSX.*>*}
        
        Count:              {<NN.*><MM|NUM.*|SN><NNB|NNG>*}  # Count
        Noun:               {<NN.*|NR|SL|NP|NominalizedVerb>}       # Noun
        
        Possessive:         {<Noun><JKG>}
        Adjective:          {<VerbPhrase><ETM>}
                            {<Adverb>}
                            {<Possessive>}
        AdjectivalPhrase:   {<Adjective><Adjective>*<Noun|Count>}
                            
        Determiner:         {<MM>}
        
        NounPhrase:         {<Determiner>*<Noun|Count|AdjectivalPhrase><XSN>*<JX|PRT.*>*}  # NounPhrase
        TopicPhrase:        {<NounPhrase><TOP.*>}
        SubjectPhrase:      {<NounPhrase><JKS>}
        ComplementPhrase:   {<NounPhrase><JKC>}
        ObjectPhrase:       {<NounPhrase><JKO>}     # ObjectPhrase
        
        Phrase:             {<NounPhrase|ObjectPhrase|ComplementPhrase|SubjectPhrase|TopicPhrase>}
                            {<Punctuation>*<Phrase><Phrase>*<Punctuation>} 
        
        EndingSuffix:       {<EF>}
        ConnectingSuffix:   {<EC|ADVEC.*>}
        
        SubordinateClause:  {<Phrase><Phrase>*<VerbPhrase><ConnectingSuffix>}
        Predicate:          {<VerbPhrase><EndingSuffix>}
        MainClause:         {<Phrase><Phrase>*<Predicate>}
        Sentence:           {<SubordinateClause>*<MainClause>}
            

    """


    grammarXXX = r"""

         NounDerivedVerb:    {<VND.*>}
         AuxiliaryVerb:      {<EC><VX|VV>}
                             {<AUX.*>}
         Adverb:             {<MAG>}
         NounDerivedAdjective: {<VAND.*>}
         AdjectivalPhrase:   {<Adverb>*<Object>*<VA|VV|AuxiliaryVerbForm|NounDerivedAdjective|NounDerivedVerb><ETM>}
         DescriptiveVerb:    {<VA|NounDerivedAdjective>}
         Verb:               {<VV|VCN|VX|NounDerivedVerb|DescriptiveVerb>}
         NominalizedVerb:    {<Verb><EP|PSX.*>*<NOM.*>}
                             {<AuxiliaryVerbForm><NOM.*>}

         VerbSuffix:         {<EP|PSX.*>*<EF|EC>*}

         Noun:               {<NN.*|NR|SL>}       
         Pronoun:            {<NP>}
         Substantive:        {<Noun><Noun>*}
                             {<Pronoun>}
                             {<NominalizedVerb>}            
         NounPhrase:         {<MM>*<XPN>*<Adverb>*<AdjectivalPhrase>*<Substantive><XSN>*<JKB>*<JX|PRT.*>*}

         Component:          {<NounPhrase|Possessive><JC|CON.*>}
         Connection:         {<Component><Component>*<NounPhrase|Possessive>}

         Possessive:         {<NounPhrase><JKG><NounPhrase>}
         Constituent:        {<NounPhrase|Possessive|Connection>}

         PrepositionalPhrase: {<Constituent|Object|AdjectivalPhrase>*<Constituent|Object|AdjectivalPhrase><PRP.*>}
         AdverbialPhrase:    {<Verb><AuxiliaryVerb>*<VerbSuffix>*<ADVEC.*>}

         Complement:         {<Constituent><JKC>} 
         Object:             {<Constituent|PrepositionalPhrase><JKO>}  
         Subject:            {<Constituent|PrepositionalPhrase><JKS>}
         Topic:              {<Constituent|PrepositionalPhrase><TOP.*>}

         Copula:             {<Constituent><Adverb>*<VCP><AuxiliaryVerb>*<VerbSuffix>}
         AuxiliaryVerbForm:  {<Verb><AuxiliaryVerb>}
         NominalVerbForm:    {<Verb|AuxiliaryVerbForm><NMF.*>}
         Predicate:          {<Adverb|AdverbialPhrase>*<Verb|AuxiliaryVerbForm|NominalVerbForm>*<VerbSuffix>}

         """

    # Location:           {<JKB>}
    # Title:              {<XSN>}
    # Possessive:         {<JKG>}
    # Particle:           {<JX|PRT.*>}

    # NounPhrase:     {<MM>*<XPN>*<MAG>*<Adjective>*<Substantive>}
    #                    {<Location_|Possessive_|Title_|NounWithParticle_>}
    # Title_:                  {<NounPhrase><XSN>}
    # Possessive_:                   {<NounPhrase><JKG>}
    #  Location_:                   {<NounPhrase><JKB>}
    #  NounWithParticle_: {<NounPhrase><JX|PRT.*><JX|PRT.*>*}


    #         Possessive:         {<NounPhrase><JKG><NounPhrase>}

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
            if isinstance(t, nltk.Tree):
                phrase = flattenPhrase(t, [])
                if t.label() not in hiddenTags:
                    phrase.append({"type": 'tree', "tag": t.label()})
                phrases.append(phrase)
            else:
                phrases.append({"type": 'word', "word": t[0].strip(), "tag": t[1]})
        #
        return phrases
