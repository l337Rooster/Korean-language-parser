#  backend/rd_parser.py  - ad-hoc recursive-descent syntactic parser for Korean sentences
#
#
__author__ = 'jwainwright'

import functools, re

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
        return ParseTree('terminal', token, None)

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

    @classmethod
    def makeNode(cls, label, marker, constituents):
        "makes a node with given label & constituents as children"
        nn = cls('node', label, None)
        constituents = constituents if type(constituents) == list else [constituents]
        for c in constituents:
            if c and c != ParseTree.nullNode:
                nn.append(c)
        return None if nn.isEmpty() else nn

    def __init__(self, type, label, parent, notes=''):
        self.type = type
        self.label = label
        self.parent = parent
        self.notes = notes
        #
        self.children = []
        self.state = 'start'

    def append(self, node):
        "adds child node"

    def insert(self, index, node):
        "inserts child node before given index"

    def delete(self, index):
        "deletes indexed child"

    def children(self):
        "return iterable over children"

    def count(self):
        "return count of child nodes"

    def phrase(cls, type, label, *constituents):
        "appends constituents as a phrase subtree"

    @property
    def isLeaf(self):
        return self.type == 'leaf'

    @property
    def isEmpty(self):
        return len(self.children) == 0

    # not sure if we need state to be a stack yet
    # def pushState(self, state):
    #     "pushes new state"
    #
    # def popState(self):
    #     "pops and return top of state-stack"
    #
    # @property
    # def state(self):
    #     "pop & return last state"
    #     return self.popState()

ParseTree.nullNode = ParseTree('null', 'null', None)

# --------------

# define decorator for grammar-rule methods on Parser
#   will automatically handle backtracking if rule returns False result
def grammarRule(rule):
    @functools.wraps(rule)
    def backtrack_wrapper(self, *args, **kwargs):
        marker = self.lexer.mark()
        result = rule(self, *args, **kwargs)
        node = ParseTree.makeNode(rule.__name__.capitalize(), marker, result)
        if not node:
            self.lexer.backTrackTo(marker)
            return []
        else:
            return [node]
    return backtrack_wrapper

# parser helper functions
def optional(rule):
    return rule() or [ParseTree.nullNode]

def anyOneOf(*rules):
    return any(r() for r in rules)

def oneOrMore(rule):
    nodes = []
    while True:
        node = rule()
        if node:
            nodes.extend(node)
        else:
            break
    return nodes

def zeroOrMore(rule):
    return oneOrMore(rule) or [ParseTree.nullNode]

def sequence(*rules):
    nodes = []
    for r in rules:
        nodes.extend(r())
    return nodes if all(nodes) else []


# ---------------

class Parser(object):
    "performs ad-hoc recursive descent of a given sentence POS-list"

    def __init__(self, posList):
        self.posList = posList
        self.lexer = Lexer(posList)

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

        return self.sentence()

    @grammarRule
    def sentence(self):
        "parses top-level sentence"
        # sentence ::=  [subordinateClause]* mainClause
        # mainClause ::= clause (ending with a SENTENCE_END construct)
        # subordinateClause ::= clase (ending with  SENTENCE_CONNECTOR construct)

        constituents = []
        # loop getting clauses until ending main clause
        while self.state != 'end':
            constituents.extend(self.clause())
        #
        return constituents

    @grammarRule
    def clause(self):
        "parse clause"
        # clause ::= [phrase]* verbPhrase (CLAUSE_CONNECTOR | SENTENCE_END)
        # sets 'end' or 'connect' state depending on clause was ended with a sentence final or clause connecting particle

        p = self.phrase()
        return p

    @grammarRule
    def phrase(self):
        "parse a phrase"

        return anyOneOf(self.nounPhrase, self.verbPhrase, self.predicate)

    @grammarRule
    def nounPhrase(self):
        "parse a noun-phrase"
        #
        return sequence(optional(self.determiner), zeroOrMore(self.adjective), oneOrMore(self.noun), optional(self.marker))

    @grammarRule
    def adjective(self):
        "adjective"
        return sequence(self.descriptiveVerb, self.adjectivalParticle)

    @grammarRule
    def descriptiveVerb(self):
        "descriptive verb"
        return self.lexer.next(r'.*:(VA|VCP|VCN)')

    @grammarRule
    def adjectivalParticle(self):
        "adjective-forming particle"
        return self.lexer.next(r'.*:(ETM)')

    @grammarRule
    def determiner(self):
        "noun-phrase determiner"
        return self.lexer.next(r'.*:(MM)')

    @grammarRule
    def noun(self):
        "noun"
        return self.lexer.next(r'.*:(N.*)')

    @grammarRule
    def marker(self):
        "noun marker"
        return self.lexer.next(r'.*:(JKS|JKO|JKC)')

    @grammarRule
    def verbPhrase(self):
        "verb phrase"
        nodes = sequence(self.verb, self.verbConnectingParticle)
        if nodes:
            self.state = 'connecting'
        return nodes

    @grammarRule
    def predicate(self):
        "sentence-ending predicate"
        nodes = sequence(self.verb, self.predicateEndingSuffix)
        if nodes:
            self.state = 'end'
        return nodes

    @grammarRule
    def verbConnectingParticle(self):
        "verb-connecting particle"
        return self.lexer.next(r'.*:(JC)')

    @grammarRule
    def predicateEndingSuffix(self):
        "sentence-ending suffix"
        return self.lexer.next(r'.*:(EF)')

# ['저:MM', '작:VA', '은:ETM', '소년:NNG', '밥:NNG', '을:JKO', '먹:VV', '다:EF', '.:SF']











