#  backend/chunker.py  - takes a mapped POS list and builds an NLTK chunk under a Korean chunking grammar
#
#
__author__ = 'jwainwright'

import nltk

# Korean phrase NLTK chunking grammar

class Chunker(object):
    "finds phrase chunks in the POS list produced by the KHaiii phoneme analyzer"

    grammar = r"""
    
         NounDerivedVerb:    {<VND>}
         AuxiliaryVerb:      {<EC><VX|VV>}
         Adverb:             {<MAG>}
         NounDerivedAdjective: {<VAND>}
         Adjective:          {<Adverb>*<VA|VV|NounDerivedAdjective|NounDerivedVerb><ETM>}
         DescriptiveVerb:    {<VA>}
         Verb:               {<VV|VCN|NounDerivedVerb|DescriptiveVerb>}
         NominalizedVerb:    {<Verb><EP|PSX.*>*<NOM.*>}
       
         VerbSuffix:         {<EP|PSX.*>*<EF|EC>}
    
         Location:           {<JKB>}
         Title:              {<XSN>}
         Preposition:        {<PRPxx>}
         Particle:           {<PRT.*>}
    
         Noun:               {<NN.*|NR|SL>}       
         Pronoun:            {<NP>}
         Substantive:        {<Noun><Noun>*}
                             {<Pronoun>}
                             {<NominalizedVerb>}            
         NounPhrase:         {<XPN>*<MAG>*<Adjective>*<Substantive><Title>*<Location>*<Particle>*<JX>*<Preposition>*}
    
         Possessive:         {<NounPhrase><JKG><NounPhrase>}
         Component:          {<NounPhrase|Possessive><JC|CON.*>}
         Connection:         {<Component><Component>*<NounPhrase|Possessive>}
    
         Constituent:        {<NounPhrase|Possessive|Connection>}
    
         PrepositionalPhrase: {<Constituent|Object|Adjective>*<Constituent|Object|Adjective><PRP.*>}
    
         Complement:         {<Constituent><JKC>} 
         Object:             {<Constituent|PrepositionalPhrase><JKO>}  
         Subject:            {<Constituent|PrepositionalPhrase><JKS>}
    
         Copula:             {<Constituent><Adverb>*<VCP><AuxiliaryVerb>*<VerbSuffix>}
         Predicate:          {<Adverb>*<Verb><AuxiliaryVerb>*<VerbSuffix>}
    
         """

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
                        phrase.append({"type": 'label', "word": st.label()})
                else:
                    phrase.append({"type": 'word', "word": st[0].strip(), "tag": st[1]}) # st[1][0] if st[1][0] in ('N', 'V') else st[0].strip()
            return phrase
        #
        phrases = []
        for t in chunkTree:
            if isinstance(t, nltk.Tree):
                phrase = flattenPhrase(t, [])
                if t.label() not in hiddenTags:
                    phrase.append({"type": 'label', "word": t.label()})
                phrases.append(phrase)
            else:
                phrases.append(('word', t[0].strip()))
        #
        return phrases
