#  backend/rd_grammar.py  - praser subclass for Korean sentence parsing
#
#
__author__ = 'jwainwright'

from rd_parser import *

class KoreanParser(Parser):
    "performs ad-hoc recursive descent of a given Korean sentence POS-list"

    # -----------  grammar rules ---------

    @grammarRule
    def sentence(self):
        "parses top-level sentence"
        # sentence ::=  [subordinateClause]* mainClause
        # subordinateClause ::= [phrase]* verbPhrase CONNECTING_SUFFIX
        # mainClause ::= [phrase]* predicate
        # predicate ::= verbPhrase ENDING_SUFFIX

        s = sequence(zeroOrMore(self.subordinateClause), self.mainClause())
        return s


    @grammarRule
    def subordinateClause(self):
        "subordinate clause"
        # subordinateClause ::= [phrase]* verbPhrase CONNECTING_SUFFIX
        sc = sequence(zeroOrMore(self.phrase), self.verbPhrase(), self.connectingSuffix())
        return sc


    @grammarRule
    def mainClause(self):
        "main clause"
        # mainClause ::= [phrase]* predicate
        mc = sequence(zeroOrMore(self.phrase), self.predicate())
        return mc


    @grammarRule
    def predicate(self):
        "predicate"
        # predicate ::= verbPhrase ENDING_SUFFIX
        p = sequence(self.verbPhrase(), self.endingSuffix())
        return p


    @grammarRule
    def connectingSuffix(self):
        return self.lexer.next(r'.*:(EC|ADVEC.*|CEC.*)')


    @grammarRule
    def endingSuffix(self):
        return self.lexer.next(r'.*:(EF)')


    @grammarRule
    def phrase(self):
        "parse a phrase"
        p = sequence(zeroOrMore(self.punctuation),
                     anyOneOf(self.nounPhrase,
                              self.objectPhrase,
                              self.subjectPhrase,
                              self.topicPhrase,
                              self.adverbialPhrase,
                              self.complementPhrase),
                     zeroOrMore(self.punctuation))
        return p

    @grammarRule
    def punctuation(self):
        return self.lexer.next(r'.*:(SP|SS|SE|SO|SW|SWK)')

    @grammarRule
    def nounPhrase(self):
        "parse a noun-phrase"
        np = sequence(optional(self.determiner),
                      anyOneOf(self.noun, self.count, self.adjectivalPhrase),
                      zeroOrMore(self.noun),
                      zeroOrMore(self.nounModifyingSuffix),
                      zeroOrMore(self.auxiliaryParticle),
                      optional(self.adverbialPhrase)
                      )
        return np

    @grammarRule
    def determiner(self):
        return self.lexer.next(r'.*:(MM)')

    @grammarRule
    def noun(self):
        "parse a noun"
        n = anyOneOf(self.simpleNoun,
                     self.nominalizedVerb)
        return n

    @grammarRule
    def count(self):
        "parse a count"
        c = sequence(self.simpleNoun(),
                     self.number(),
                     optional(self.counter))
        return c

    @grammarRule
    def number(self):
        return self.lexer.next(r'.*:(MM|NUM.*|SN)')

    @grammarRule
    def counter(self):
        return self.lexer.next(r'.*:(NNB|NNG)')

    @grammarRule
    def adjectivalPhrase(self):
        "parse an adjectival phrase"
        ap = sequence(oneOrMore(self.adjective),
                      anyOneOf(self.noun, self.count))
        return ap

    @grammarRule
    def adjective(self):
        "parse an adjective"
        a = anyOneOf(sequence(self.verbPhrase(), self.adjectiveFormingSuffix()),
                     self.adverb(),
                     self.possessive())
        return a

    @grammarRule
    def verbPhrase(self):
        "parse a verb phrase"
        vp = sequence(zeroOrMore(self.adverbial),
                      anyOneOf(self.verb, self.verbAndAuxiliary),
                      zeroOrMore(self.verbSuffix))
        return vp

    @grammarRule
    def adverbial(self):
        "parse an adverbial"
        av = anyOneOf(self.adverb, self.adverbialPhrase)
        return av

    @grammarRule
    def adverb(self):
        "parse an adverb"
        vp = anyOneOf(self.simpleAdverb(),
                      sequence(self.descriptiveVerb(), self.adverbFormingSuffix()))
        return vp

    @grammarRule
    def simpleAdverb(self):
        sa = self.lexer.next(r'.*:(MAG)')
        return sa

    @grammarRule
    def possessive(self):
        "parse a possessive phrase"
        pp = sequence(self.noun(), self.possessiveParticle())
        return pp

    @grammarRule
    def possessiveParticle(self):
        return self.lexer.next(r'.*:(JKG)')

    @grammarRule
    def descriptiveVerb(self):
        return self.lexer.next(r'.*:(VA|VCP|VCN|VAND.*)')

    @grammarRule
    def adverbFormingSuffix(self):
        return self.lexer.next(r'.*:(EC)')

    @grammarRule
    def verbAndAuxiliary(self):
        "parse a verb + auxiliary verb"
        vpa = sequence(self.verb(),
                       self.auxiliaryVerb())
        return vpa

    @grammarRule
    def auxiliaryVerb(self):
        "parse an auxiliary verb"
        av = anyOneOf(sequence(self.auxiliaryVerbConnector(), self.verb()),
                      self.auxiliaryVerbPattern)
        return av

    @grammarRule
    def auxiliaryVerbConnector(self):
        return self.lexer.next(r'.*:(EC|NEC.*)')

    @grammarRule
    def auxiliaryVerbPattern(self):
        return self.lexer.next(r'.*:(AUX.*)')

    @grammarRule
    def adjectiveFormingSuffix(self):
        return self.lexer.next(r'.*:(ETM)')

    @grammarRule
    def verbSuffix(self):
        return self.lexer.next(r'.*:(EP|PSX.*)')

    @grammarRule
    def simpleNoun(self):
        return self.lexer.next(r'.*:(NN.*|NR|SL|NP)')

    @grammarRule
    def nominalizedVerb(self):
        "parse a nominalized verb"
        nv = sequence(self.verb(), self.nominalizingSuffix())
        return nv

    @grammarRule
    def verb(self):
        "parse a verb"
        v = anyOneOf(self.simpleVerb, self.descriptiveVerb)
        return v

    @grammarRule
    def simpleVerb(self):
        return self.lexer.next(r'.*:(VV|VX|VND.*)')

    @grammarRule
    def nominalizingSuffix(self):
        return self.lexer.next(r'.*:(NOM.*)')

    @grammarRule
    def nounModifyingSuffix(self):
        return self.lexer.next(r'.*:(XSN)')

    @grammarRule
    def auxiliaryParticle(self):
        return self.lexer.next(r'.*:(JX|PRT.*)')

    @grammarRule
    def adverbialPhrase(self):
        "parse an adverbial phrase - I think this should be called a prepostional phrase!"
        ap = sequence(anyOneOf(self.noun, self.adjectivalPhrase),
                      self.adverbialPhraseConnector(),
                      optional(self.auxiliaryParticle))
        return ap

    @grammarRule
    def adverbialPhraseConnector(self):
        return self.lexer.next(r'.*:(EC|ADVEC.*)')

    @grammarRule
    def objectPhrase(self):
        "parse a noun-phrase with object-marker"
        return sequence(self.nounPhrase(),
                        self.lexer.next(r'.*:JKO'))

    @grammarRule
    def subjectPhrase(self):
        "parse a noun-phrase with subject-marker"
        return sequence(self.nounPhrase(),
                        self.lexer.next(r'.*:JKS'))

    @grammarRule
    def complementPhrase(self):
        "parse a complement-phrase with complement-marker"
        return sequence(self.nounPhrase(),
                        self.lexer.next(r'.*:JKC'))

    @grammarRule
    def topicPhrase(self):
        "parse a noun-phrase with topic-marker"
        return sequence(self.nounPhrase(),
                        self.lexer.next(r'.*:TOP.*'))
