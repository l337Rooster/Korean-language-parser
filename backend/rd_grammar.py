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
                     anyOneOf(option(self.nounPhrase),
                              option(self.combinedNounPhrase),
                              option(self.objectPhrase),
                              option(self.subjectPhrase),
                              option(self.topicPhrase),
                              option(self.adverbialPhrase),
                              option(self.prepositionalPhrase),
                              option(self.complementPhrase)),
                     zeroOrMore(self.interjection),
                     zeroOrMore(self.punctuation))
        return p

    @grammarRule
    def punctuation(self):
        return self.lexer.next(r'.*:(SP|SS|SE|SO|SW|SWK)')

    @grammarRule
    def interjection(self):
        return self.lexer.next(r'.*:(IC)')

    @grammarRule
    def conjunction(self):
        "parse a conjunction of connected noun phrases"
        c = sequence(self.nounPhrase(), self.connector())
        return c

    @grammarRule
    def connector(self):
        return self.lexer.next(r'.*:(JC|CON.*)')

    @grammarRule
    def combinedNounPhrase(self):
        "parse a conjunction-combined noun-phrase"
        snp = sequence(zeroOrMore(self.conjunction), self.nounPhrase)
        return snp

    @grammarRule
    def nounPhrase(self):
        "parse a noun-phrase"
        np = sequence(optional(self.determiner),
                      anyOneOf(option(self.noun), option(self.count), option(self.adjectivalPhrase)),
                      zeroOrMore(self.noun),
                      zeroOrMore(self.nounModifyingSuffix),
                      zeroOrMore(self.adverbialParticle),
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
        n = anyOneOf(option(self.simpleNoun),
                     option(self.nominalizedVerb))
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
                      anyOneOf(option(self.noun), option(self.count)))
        return ap

    @grammarRule
    def adjective(self):
        "parse an adjective"
        a = anyOneOf(option(sequence(self.verbPhrase(), self.adjectiveFormingSuffix())),
                     option(self.adverb()),
                     option(self.possessive()))
        return a

    @grammarRule
    def verbPhrase(self):
        "parse a verb phrase"
        vp = sequence(zeroOrMore(self.adverbial),
                      anyOneOf(option(self.verb), option(self.verbAndAuxiliary)),
                      zeroOrMore(self.verbSuffix))
        return vp

    @grammarRule
    def adverbial(self):
        "parse an adverbial"
        av = anyOneOf(option(self.adverb), option(self.adverbialPhrase))
        return av

    @grammarRule
    def adverb(self):
        "parse an adverb"
        vp = anyOneOf(option(self.simpleAdverb),
                      option(sequence(self.descriptiveVerb(), self.adverbFormingSuffix())))
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
                       oneOrMore(self.auxiliaryVerb))
        return vpa

    @grammarRule
    def auxiliaryVerb(self):
        "parse an auxiliary verb"
        av = anyOneOf(option(sequence(self.auxiliaryVerbConnector(), self.verb())),
                      option(self.auxiliaryVerbPattern))
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
        v = anyOneOf(option(self.simpleVerb), option(self.descriptiveVerb))
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
    def adverbialParticle(self):
        return self.lexer.next(r'.*:(JKB)')

    @grammarRule
    def auxiliaryParticle(self):
        return self.lexer.next(r'.*:(JX|PRT.*)')

    @grammarRule
    def adverbialPhrase(self):
        "parse an adverbial phrase - I think this should be called a prepostional phrase!"
        ap = sequence(anyOneOf(option(self.noun), option(self.adjectivalPhrase)),
                      self.adverbialPhraseConnector(),
                      optional(self.auxiliaryParticle))
        return ap

    @grammarRule
    def adverbialPhraseConnector(self):
        return self.lexer.next(r'.*:(EC|ADVEC.*)')

    @grammarRule
    def prepositionalPhrase(self):
        "parse a prepositional phrase"
        pp = sequence(anyOneOf(option(self.nounPhrase), option(self.combinedNounPhrase)),
                      self.prepositionalSuffix())
        return pp

    @grammarRule
    def prepositionalSuffix(self):
        return self.lexer.next(r'.*:(PRP.*)')

    @grammarRule
    def objectPhrase(self):
        "parse a noun-phrase with object-marker"
        return sequence(zeroOrMore(self.conjunction),
                        self.nounPhrase(),
                        self.lexer.next(r'.*:JKO'))

    @grammarRule
    def subjectPhrase(self):
        "parse a noun-phrase with subject-marker"
        return sequence(zeroOrMore(self.conjunction),
                        self.nounPhrase(),
                        self.lexer.next(r'.*:JKS'))

    @grammarRule
    def complementPhrase(self):
        "parse a complement-phrase with complement-marker"
        return sequence(zeroOrMore(self.conjunction),
                        self.nounPhrase(),
                        self.lexer.next(r'.*:JKC'))

    @grammarRule
    def topicPhrase(self):
        "parse a noun-phrase with topic-marker"
        return sequence(zeroOrMore(self.conjunction),
                        self.nounPhrase(),
                        self.lexer.next(r'.*:TOP.*'))
