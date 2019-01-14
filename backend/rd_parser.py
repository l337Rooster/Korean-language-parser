#  backend/rd_parser.py  - ad-hoc recursive-descent syntactic parser for Korean sentences
#
#
__author__ = 'jwainwright'

import functools, re
from collections import defaultdict

#  This is an alternative to the nltk chunking approach, allowing more contextual control over parsing
#
# The high-level sentence structure will roughly be as follows:
#
#  sentence ::=  [subordinateClause]* mainClause
#  mainClause ::= clause SENTENCE_END
#  subordinateClause ::= clause CLAUSE_CONNECTOR
#  clause ::= [phrase]* verbPhrase
#

class Terminal(object):
    "wraps lexical terminal token"


class Lexer(object):
    "lexical analyzer wraps morhpheme:POS list from KHaiii analyzer, doing any needed lexixcal transformation & providing token-by-token access"

    def __init__(self, posList):   # in the form ['phoneme:POStag', ,...]
        self.posList = posList
        self.cursor = 0
        self.lexer = None

    # -------- parser API ---------

    def next(self, tokenPat=None):
        "yields and consumes next token (as a terminal node), or fails if tokenPat supplied and next token doesn't match"
        node = self.peek(tokenPat)
        if node:
            self.cursor += 1
        return node

    def peek(self, tokenPat=None):
        "yields but doesn't consume next token"
        token = self.posList[self.cursor]
        if tokenPat and not re.fullmatch(tokenPat, token):
            return None
        #
        return [ParseTree('terminal', token, self.cursor, self.cursor, self, None)]

    def last(self):
        "yields last token again"

    def mustBe(self, tokenPat):
        "yields & consumes next token if it matches give pattern, else doesn't consome & returns None"

    def backTrack(self, token):
        "backtracks over given token"

    def mark(self):
        "return marker for current lexical progress"
        # for now, just the phoneme:tag tuple cursor
        return self.cursor

    def backTrackTo(self, marker):
        "backracks lexer state to given marker"
        # for now, just restore cursor
        self.cursor = marker

class ParseTree(object):
    "nodes in the result of a parse"

    nullNode = None

    def __init__(self, type, label, startMark, endMark, lexer, notes=''):
        self.type = type
        self.label = label
        self.startMark, self.endMark = startMark, endMark
        self.lexer = lexer
        self.notes = notes
        #
        self.children = []

    def __repr__(self):
        return '{0}: {1} [{2}]'.format(self.type, self.label, ', '.join(c.label for c in self.children))

    def append(self, node):
        "adds child node"
        self.children.append(node)

    def insert(self, index, node):
        "inserts child node before given index"

    def delete(self, index):
        "deletes indexed child"

    def count(self):
        "return count of child nodes"
        return len(self.children)

    def terminalSpan(self):
        "return number of terminal symbols this node & it's sub-tree covers"
        return self.endMark - self.startMark

    def phrase(cls, type, label, *constituents):
        "appends constituents as a phrase subtree"

    def isLeaf(self):
        return self.type == 'terminal'

    def isEmpty(self):
        return len(self.children) == 0

    def pprint(self, level=0, closer=''):
        indent = '  ' * level
        if self.isEmpty():
            print(indent + self.label + closer)
        else:
            print(indent + self.label + ' (')
            for c in self.children:
                c.pprint(level + 1, closer + (')' if c == self.children[-1] else ''))

ParseTree.nullNode = ParseTree('null', 'null', 0, 0, None)

# --------------

# define decorator for grammar-rule methods on Parser
#   will automatically handle backtracking if rule returns False result
def grammarRule(rule):
    @functools.wraps(rule)
    def backtrack_wrapper(self, *args, **kwargs):
        indent = '  ' * len(self.recursionState)
        startMark = self.lexer.mark()
        print(indent, '--- at ', self.lexer.posList[self.lexer.cursor], 'looking for ', rule.__name__)
        # if rule in self.fails[startMark]:
        #     print(indent, '    nope, failed this before')
        #     return []
        if (rule, startMark) in self.recursionState:
            print(indent, '    recursion on same token encountered, failing')
            return []
        #
        self.recursionState.append((rule, startMark))
        #
        result = rule(self, *args, **kwargs)
        #
        self.recursionState.pop(-1)
        #
        node = self.makeNode(rule.__name__, startMark, result)
        if not node:
            self.fails[startMark].add(rule) # note we failed this production at this point to break later recursive attempts at same thing
            self.lexer.backTrackTo(startMark)
            print(indent, '    nope, backtracking to ', self.lexer.posList[self.lexer.cursor])
            return []
        else:
            traceBack = " -> ".join(r.__name__ for r, m in reversed(self.recursionState))
            print(indent, '**** found', node, traceBack)
            return [node]
    return backtrack_wrapper

# parser helper functions
def eval(rule):
    return rule() if callable(rule) else rule

def optional(rule):
    return eval(rule) or [ParseTree.nullNode]

def anyOneOf(*rules):
    # eager match: eval all rules, take the longest matching
    longest = None; length = 0
    for i, r in enumerate(rules):
        node = eval(r)
        if node and node[0] != ParseTree.nullNode:
            l = sum(n.terminalSpan() for n in node)
            if not longest or l > length:
                longest, length = node, l
            # restart matching
            node[0].lexer.backTrackTo(node[0].startMark)
    #
    if longest:
        # seek to end of selected longes match
        longest[0].lexer.backTrackTo(longest[-1].endMark)
        return longest

def oneOrMore(rule):
    nodes = []
    while True:
        node = eval(rule)
        if node and node[0] != ParseTree.nullNode:
            nodes.extend(node)
        if not node or not callable(rule):
            break

    return nodes

def zeroOrMore(rule):
    return rule and oneOrMore(rule) or [ParseTree.nullNode]

def sequence(*rules):
    nodes = []
    for r in rules:
        node = eval(r)
        if node:
            nodes.extend(node)
        else:
            # any miss fails whole seq
            return []
    return nodes

# ---------------

class Parser(object):
    "performs ad-hoc recursive descent of a given sentence POS-list"

    def __init__(self, posList):
        self.posList = posList
        self.lexer = Lexer(posList)
        self.fails = defaultdict(set)  # tracks history of failed profuctions at each cursor position to break recursions
        self.recursionState = []  # tracks recursion state to break recursive rules

    def mark(self):
        "return marker for current parsing state"
        # for now, just lexer state
        return self.lexer.mark()

    def backTrackTo(self, marker):
        "backtrack parsing to state indicate by given marker"
        # for now, just back-tracks lexer
        self.lexer.backTrackTo(marker)

    def parse(self):
        "begin parse, return ParseTree root node"

        s = self.sentence()[0]
        s.pprint()

        return s

    def makeNode(self, label, startMark, constituents):
        "makes a node with given label & constituents as children"
        label = label[0].capitalize() + label[1:]
        nn = ParseTree('node', label, startMark, self.lexer.mark(), self.lexer)
        constituents = constituents if type(constituents) == list else [constituents]
        for c in constituents:
            if c and c != ParseTree.nullNode:
                nn.append(c)
        return None if nn.isEmpty() else nn


    # -----------  grammar rules ---------

    @grammarRule
    def sentence(self):
        "parses top-level sentence"
        # sentence ::=  [subordinateClause]* mainClause
        # subordinateClause ::= [phrase]* verbPhrase CONNECTING_SUFFIX
        # mainClause ::= [phrase]* predicate
        # predicate ::= verbPhrase ENDING_SUFFIX

        s = sequence(zeroOrMore(self.subordinateClause), self.mainClause)
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
        c = sequence(self.simpleNoun,
                     self.number,
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
        a = anyOneOf(sequence(self.verbPhrase, self.adjectiveFormingSuffix),
                     self.adverb(),
                     self.possessive())
        return a

    @grammarRule
    def verbPhrase(self):
        "parse a verb phrase"
        vp = sequence(zeroOrMore(anyOneOf(self.adverb, self.adverbialPhrase)),
                      anyOneOf(self.verb, self.verbAndAuxiliary),
                      optional(self.verbSuffix))
        return vp

    @grammarRule
    def adverb(self):
        "parse an adverb"
        vp = anyOneOf(self.simpleAdverb(),
                      sequence(self.descriptiveVerb, self.adverbFormingSuffix))
        return vp

    @grammarRule
    def simpleAdverb(self):
        return self.lexer.next(r'.*:(MAG)')

    @grammarRule
    def possessive(self):
        "parse a possessive phrase"
        pp = sequence(self.noun, self.possessiveParticle)
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
        vpa = sequence(self.verb,
                       self.auxiliaryVerb)
        return vpa

    @grammarRule
    def auxiliaryVerb(self):
        "parse an auxiliary verb"
        av = anyOneOf(sequence(self.auxiliaryVerbConnector, self.verb),
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
        nv = sequence(self.verb, self.nominalizingSuffix)
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
                      self.adverbialPhraseConnector,
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

if __name__ == "__main__":
    #
    posList = [('저', 'MM'),
             ('작', 'VA'),
             ('은', 'ETM'),
             ('소년', 'NNG'),
             ('의', 'JKG'),
             ('남동생', 'NNG'),
             ('은', 'TOP_6'),
             ('밥', 'NNG'),
             ('을', 'JKO'),
             ('먹', 'VV'),
             ('다', 'EF'),
             ('.', 'SF')]

    p = Parser([":".join(p) for p in posList])
    p.parse()














