#  backend/tester.py  - builds/runs automated testing of test sentences
#
#
__author__ = 'jwainwright'

import pickle, json

from api import parseInput

testSentences = [
    "저 작은 소년 밥을 먹다.",
    "저 작은 소년의 남동생은 밥을 먹다.",
    "제 친구는 아주 예쁜 차를 샀어요.",
    "제 친구는 아주 빠른 차를 샀어요.",
    "그분은 선생님이 아닙니다.",
    "이것이 제 책이예요.",
    "여기는 서울역이예요.",
    "빵 하나를 주세요.",
    "빵 네 개를 주세요.",
    "맥주 다섯 병를 주세요.",
    "그 큰 빵 네 개를 주세요.",
    "맥주 5병이요.",
    "맥주 다섯 병를 주세요.",
    "책 두세 권 있어요.",
    "어머니께서 아이에게 밥을 먹이셨습니다.",
    "저는 학교에 안 갔어요.",
    "날이 추워서 집에만 있는다.",
    "아기가 있어서 강아지는 안 키워요.",
    "참기름을 넣어서 더 맛있게 만들었다.",
    "탐은 공부하기를 싫어한다.",
    "기차가 떠나가 버렸어요.",
    "인삼은 한국에서만 잘 자랍니다.",
    "비가 오는 것을 봤어요.",
    "비가 올까 봐 걱정이다.",
    "나는 이미 여기서 많은 시간을 기다렸다.",
]

def buildRefTrees():
    "runs parser against each sentence, writing JSONed parse-tree to reference dictionary"

    refDict = {}

    for s in testSentences:
        # parse sentence, extract parseTree & add to ref dict
        parse = parseInput(s)[0]
        refDict[s] = parse['parseTree']

    # write ref-tree dict to disk
    with open("parse-ref-tree-dict.json", "w") as outf:
        json.dump(refDict, outf, indent=2)

def test():
    "re-parse test-sentences & compare to ref-set on disk, complain about mismatches"

    with open("parse-ref-tree-dict.json") as inf:
        refDict = json.load(inf)
    fails = []
    for s in testSentences:
        # parse sentence, extract parseTree & compare to ref dict
        parse = parseInput(s)[0]
        if json.dumps(refDict[s]) != json.dumps(parse['parseTree']):
            fails.append(s)
    #
    return fails

if __name__ == "__main__":
    #

    #buildRefTrees()

    #
    fails = test()
    print("\n-------\nTests complete")
    for f in fails:
        print("Parse mismatch for sentence: ", f)
        #
    print(len(fails), "fails")

