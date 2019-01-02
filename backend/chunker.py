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
    
         NounDerivedVerb:    {<VND.*>}
         AuxiliaryVerb:      {<EC><VX|VV>}
         Adverb:             {<MAG>}
         NounDerivedAdjective: {<VAND.*>}
         Adjective:          {<Adverb>*<VA|VV|NounDerivedAdjective|NounDerivedVerb><ETM>}
         DescriptiveVerb:    {<VA>}
         Verb:               {<VV|VCN|NounDerivedVerb|DescriptiveVerb>}
         NominalizedVerb:    {<Verb><EP|PSX.*>*<NOM.*>}
       
         VerbSuffix:         {<EP|PSX.*>*<EF|EC>}
    
         Noun:               {<NN.*|NR|SL>}       
         Pronoun:            {<NP>}
         Substantive:        {<Noun><Noun>*}
                             {<Pronoun>}
                             {<NominalizedVerb>}            
         NounPhrase:         {<MM>*<XPN>*<MAG>*<Adjective>*<Substantive><XSN>*<JKB>*<JX|PRT.*>*}
    
         Component:          {<NounPhrase|Possessive><JC|CON.*>}
         Connection:         {<Component><Component>*<NounPhrase|Possessive>}
    
         Possessive:         {<NounPhrase><JKG><NounPhrase>}
         Constituent:        {<NounPhrase|Possessive|Connection>}
    
         PrepositionalPhrase: {<Constituent|Object|Adjective>*<Constituent|Object|Adjective><PRP.*>}
         AdverbialPhrase:    {<Verb><AuxiliaryVerb>*<ADVEC.*>}
    
         Complement:         {<Constituent><JKC>} 
         Object:             {<Constituent|PrepositionalPhrase><JKO>}  
         Subject:            {<Constituent|PrepositionalPhrase><JKS>}
         Topic:              {<Constituent|PrepositionalPhrase><TOP.*>}
    
         Copula:             {<Constituent><Adverb>*<VCP><AuxiliaryVerb>*<VerbSuffix>}
         Predicate:          {<Adverb|AdverbialPhrase>*<Verb><AuxiliaryVerb>*<VerbSuffix>}
    
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
            cls.parser = nltk.RegexpParser(cls.grammar, trace=trace)
        #
        chunkTree = cls.parser.parse(posList)

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
