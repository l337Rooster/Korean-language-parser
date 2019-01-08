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

    def __init__(self, type, label, startMark, endMark, notes=''):
        self.type = type
        self.label = label
        self.startMark, self.endMark = startMark, endMark
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
        startMark = self.lexer.mark()
        print('--- at ', self.lexer.posList[self.lexer.cursor], 'looking for ', rule.__name__)
        result = rule(self, *args, **kwargs)
        node = self.makeNode(rule.__name__, startMark, result)
        if not node:
            self.lexer.backTrackTo(startMark)
            print('    nope, backtracking to ', self.lexer.posList[self.lexer.cursor])
            return []
        else:
            print('    found', node)
            return [node]
    return backtrack_wrapper

# parser helper functions
def eval(rule):
    return rule() if callable(rule) else rule

def optional(rule):
    return eval(rule) or [ParseTree.nullNode]

def anyOneOf(*rules):
    # eval all rules, take the longest matching
    longest = None; length = 0
    for r in rules:
        node = eval(r)
        if node and node[0] != ParseTree.nullNode:
            l = sum(n.terminalSpan() for n in node)
            if not longest or l > length:
                longest, length = node, l
            # restart matching
            node[0].lexer.backTrack(node[0].startMark)
    #
    if longest:
        # seek to end of selected longes match
        longest[0].lexer.backTrack(longest[-1].endMark)
        return longest

def oneOrMore(rule):
    nodes = []
    while True:
        node = eval(rule)
        if node:
            nodes.extend(node)
        if not node or not callable(rule):
            break

    return nodes

def zeroOrMore(rule):
    return oneOrMore(rule) or [ParseTree.nullNode]

def sequence(*rules):
    nodes = []
    for r in rules:
        nodes.extend(eval(r))
    return nodes if all(nodes) and len(nodes) == len(rules) else []

# ---------------

class Parser(object):
    "performs ad-hoc recursive descent of a given sentence POS-list"

    def __init__(self, posList):
        self.posList = posList
        self.lexer = Lexer(posList)
        self.state = 'start'

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
        nn = ParseTree('node', label, startMark, self.lexer.mark())
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
        # mainClause ::= clause (ending with a SENTENCE_END construct)
        # subordinateClause ::= clase (ending with  SENTENCE_CONNECTOR construct)

        constituents = []
        # loop getting clauses until sentence end
        while True:
            c = self.clause()
            # add clause or current terminal if not recognized
            constituents.extend(c or [self.lexer.next()])
            if self.lexer.peek(r'(.*:SF)'):
                break
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

        return anyOneOf(self.nounPhrase,
                        self.objectPhrase,
                        self.subjectPhrase,
                        self.topicPhrase,
                        self.verbPhrase,
                        self.predicate)

    @grammarRule
    def nounPhrase(self):
        "parse a noun-phrase"
        return sequence(optional(self.determiner), optional(self.adjectives), self.noun())

    @grammarRule
    def objectPhrase(self):
        "parse a noun-phrase with object-marker"
        return sequence(self.nounPhrase(), self.lexer.next(r'.*:JKO)'))

    @grammarRule
    def subjectPhrase(self):
        "parse a noun-phrase with subject-marker"
        return sequence(self.nounPhrase(), self.lexer.next(r'.*:JKS)'))

    @grammarRule
    def topicPhrase(self):
        "parse a noun-phrase with topic-marker"
        return sequence(self.nounPhrase(), self.lexer.next(r'(ㄴ|은|는):JX'))

    @grammarRule
    def adjectives(self):
        "adjective sequence"
        return sequence(zeroOrMore(self.adjective), optional(self.possessive), zeroOrMore(self.adjective))

    @grammarRule
    def adjective(self):
        "adjective"
        return sequence(self.descriptiveVerb(), self.adjectivalParticle())

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
    def possessive(self):
        "possessive"
        return sequence(self.noun(), self.possessiveMarker())

    @grammarRule
    def noun(self):
        "noun"
        return self.lexer.next(r'.*:(N.*)')

    @grammarRule
    def marker(self):
        "noun marker"
        return self.lexer.next(r'.*:(JKS|JKO|JKC)')

    @grammarRule
    def possessiveMarker(self):
        "possessive marker"
        return self.lexer.next(r'.*:(JKG)')

    @grammarRule
    def verbPhrase(self):
        "verb phrase"
        return sequence(self.verb(), self.verbConnectingParticle())

    @grammarRule
    def predicate(self):
        "sentence-ending predicate"
        return sequence(self.verb(), self.predicateEndingSuffix())

    @grammarRule
    def verb(self):
        "verb"
        return self.lexer.next(r'.*:(V.*)')

    @grammarRule
    def verbConnectingParticle(self):
        "verb-connecting particle"
        return self.lexer.next(r'.*:(JC)')

    @grammarRule
    def predicateEndingSuffix(self):
        "sentence-ending suffix"
        return self.lexer.next(r'.*:(EF)')


if __name__ == "__main__":
    #
    posList = ['저:MM',
                 '작:VA',
                 '은:ETM',
                 '소년:NNG',
                 '의:JKG',
                 '남동생:NNG',
                 '밥:NNG',
                 '을:JKO',
                 '먹:VV',
                 '다:EF',
                 '.:SF']
    posList = ['저:MM', '작:VA', '은:ETM', '소년:NNG', '밥:NNG', '을:JKO', '먹:VV', '다:EF', '.:SF']
    posList = ['저:NP',
                 '의:JKG',
                 '친구:NNG',
                 '는:JX',
                 '아주:MAG',
                 '예쁘:VA',
                 'ㄴ:ETM',
                 '차:NNG',
                 '를:JKO',
                 '사:VV',
                 '았:EP',
                 '어요:EF',
                 '.:SF']

    p = Parser(posList)
    p.parse()














