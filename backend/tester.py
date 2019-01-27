#  backend/tester.py  - builds/runs automated testing of test sentences
#
#
__author__ = 'jwainwright'

import sys, pickle, json

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
    "비가 올 것이라고 걱정된다.",
    "사실이 아니라고 몇 번을 해명했지만 통하지 않았다.",
    "나는 비가 온 것을 보았다.",
    "한국어를 배우고 싶지 않아요.",
    "저는 숙제를 끝내고 나서 집으로 갈 거예요.",
    "나는 저녁으로 빵과 물과 밥을 먹었어요.",
    "나는 저녁으로 매운 김치와 국과 밥을 먹고 싶어요.",
    "khaiii의 빌드 및 설치에 관해서는 빌드 및 설치 문서를 참고하시기 바랍니다.",
    "내일 일요일인데, 뭐 할 거예요?",
    "창문 열어도 돼요?",
    "중국음식을 먹었다. ",
    "중국음식을 좋아하기 때문이에요.",
    "중국음식을 먹었다.",
    "왜냐하면 중국음식을 좋아하기 때문이에요.",
    "중국 음식을 좋아하기 때문에 중국 음식을 먹었어요.",
    "중국 음식을 좋아하기 때문에 중국 음식을 많이 먹을 거예요.",
    "중국 음식은 좋아하기 때문에 중국 음식을 먹었어요.",
    "저는 호주인입니다. 하지만 캘리포니아에 살아요.",
    "저는 호주인입니다, 하지만 캘리포니아에 살아요.",
    "제일 맛있는 것 추천해 주세요."
]

# "사실이 아니라고 몇 번을 해명했지만 통하지 않았다.",
# "나는 비가 온 것을 보았다.",
# "그 분은 한국말을 이해하시지?",
#

def buildRefTrees():
    "runs parser against each sentence, writing JSONed parse-tree to reference dictionary"

    refDict = {}

    for s in testSentences:
        # parse sentence, extract parseTree & add to ref dict
        parse = parseInput(s, getWordDefinitions=False)[0]
        refDict[s] = parse['parseTree']

    # write ref-tree dict to disk
    with open("parse-ref-tree-dict.json", "w") as outf:
        json.dump(refDict, outf, indent=2)

def test():
    "re-parse test-sentences & compare to ref-set on disk, complain about mismatches"

    with open("parse-ref-tree-dict.json") as inf:
        refDict = json.load(inf)
    fails = []; missing = []
    for s in testSentences:
        # parse sentence, extract parseTree & compare to ref dict
        parse = parseInput(s, getWordDefinitions=False)[0]
        ref = refDict.get(s)
        if not ref:
            missing.append(s)
        else:
            if not matchParse(ref['tree'], parse['parseTree']['tree']):
                fails.append(s)
    #
    return fails, missing

def matchParse(p1, p2):
    "match parse trees, allowing synthetic-tag ordinal mismatch"
    if p1['type'] != p2['type'] or p1['tag'] != p2['tag'] or len(p1['children']) != len(p2['children']):
        return False
    if p1['type'] == 'tree':
        for c1, c2 in zip(p1['children'], p2['children']):
            return matchParse(c1, c2)
    else:
        if p1['word'] != p2['word'] or p1['tag'].split('_')[0] != p1['tag'].split('_')[0]:   # ignore differing synth tag numbers
            return False
    return True

if __name__ == "__main__":
    #
    if len(sys.argv) == 2:
        if sys.argv[1] == 'build':
            buildRefTrees()
        elif sys.argv[1] == 'test':
            fails, missing = test()
            print("\n-------\nTests complete")
            for m in missing:
                print("Missing in refDict: ", m)
            for f in fails:
                print("Parse mismatch for sentence: ", f)
                #
            print(len(fails), "fails")
        else:
            print("Unrecognized command, must be build or test")
    else:
        print("Wrong number of arguments")

