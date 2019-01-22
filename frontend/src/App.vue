<!-- main Korean sentence parser UI -->

<template>
    <div id="app" v-on:mouseup="appMouseUp($event)">
        <div class="k-flexcol">
            <!-- header row -->
            <div id="input-row" class="k-flexrow ">
                <div id="input-title" >Korean sentence parser</div>
                <div id="attribution">v0.7.3 - <a href="mailto:johnw3d@gmail.com">JBW</a> - based on the <a href="https://github.com/kakao/khaiii">Kakao Hangul Analyzer III</a> and JBW's phrase parser</div>
            </div>
            <!-- input row -->
            <div class="k-flexrow">
                <table>
                    <tr id="text-row">
                        <td><textarea autofocus id="input-sentence" class="" placeholder="enter Korean sentence to parse" v-model="sentence"></textarea></td>
                        <td><button autofocus class="" id="parse-button" v-on:click="requestParse" :disabled="sentence == ''">{{ parseButtonText }}</button></td>
                    </tr>
                    <tr id="controls-row">
                        <td>
                            <template v-if="sentence != ''">
                                <span v-for="t in translators" class="">
                                    <a :href="t.slug.replace('${sentence}', sentence)" target="_blank">{{t.title}}</a> ~
                                </span>
                            </template>
                            <label for="show-all-levels">Show all levels: </label>
                            <input class="" type="checkbox" id="show-all-levels" v-model="showAllLevels"> ~
                            <label for="debug">Debug output: </label>
                            <input class="" type="checkbox" id="debug" v-model="debugOutput">
                        </td>
                        <td>&nbsp;</td>
                    </tr>
                </table>
            </div>
            <!-- Naver/Papago translation -->
            <div class="k-flexrow">
                <div id="naver-translation" v-if="naverTranslation"><span>Naver/Papago translation: </span>{{naverTranslation}}</div>
            </div>

            <div v-if="error" class="error-msg">
                {{ error }}
            </div>
            <!-- parse-tree display, primarily one large SVG element -->
            <div v-if="!parsing">
                <div v-for="s in sentences">
                    <template v-if="s.error">
                        <div class="k-flexrow parse-fail-msg"> {{ s.error }} </div>
                        <div class="k-flexrow parse-fail-unrec">Unreconized: {{ s.lastToken.split(':')[0] }}</div>
                        <div class="k-flexrow parse-fail-poslist">
                            Parts of speech:
                            <span v-for="pos in s.posList">
                                <span class="parse-fail-word">{{ pos.split(':')[0] }}:</span>
                                <span class="parse-fail-tag">{{ pos.split(':')[1] }}, </span>
                            </span>
                        </div>
                    </template>
                    <tenplate v-else>
                        <div class="output-row k-flexrow k-table">
                            <!-- div class="pos-list">
                                <div v-for="phrase in s.phrases">
                                    <template v-for="element, i in phrase">
                                        <span v-if="element.type == 'word' && i > 0" class="phrase-plus"> + </span>
                                        <span v-if="element.type == 'word'" class="leaf-word"
                                              v-on:mouseenter="mouseEnterNode(element, $event)"
                                              v-on:click="nodeClick(element, $event)">{{ element.word }}</span>
                                        <span v-if="element.type == 'tree'" class="leaf-tag">({{ element.tag }})</span>
                                    </template>
                                </div>
                            </div -->
                            <svg class="parse-tree tree-svg" :width="s.treeWidth" :height="s.treeHeight" style="background-color: rgba(0,0,0,0);">
                                <!-- input word list -->
                                <g v-for="word in s.words">
                                    <text :x="word.x + word.width / 2" :y="word.y" text-anchor="middle" alignment-baseline="hanging">
                                        <tspan class="word-word">{{ word.word }}</tspan>
                                    </text>
                                    <line :x1="word.x + 2" :y1="word.y + 7" class="word-line"
                                          :x2="word.x + word.width - 4" :y2="word.y + 7"/>
                                </g>
                                <!-- the terminal morphemes -->
                                <g v-for="node in s.terminals">
                                    <text :x="node.x + node.width / 2" :y="node.y" text-anchor="middle" alignment-baseline="hanging">
                                        <template v-if="node.word">
                                            <tspan class="leaf-word" v-on:mouseenter="mouseEnterNode(node, $event)"
                                                                     v-on:click="nodeClick(node, $event)">{{ node.word }}</tspan>
                                            <tspan :x="node.x + node.width / 2" :dy="terminalHeight - 4" class="leaf-tag">{{ node.tagLabel[0] }}</tspan>
                                            <tspan v-if="node.tagLabel.length > 1"
                                                   :x="node.x + node.width / 2" :dy="tagLabelHeight" :class="leafTagClass(node)">{{ node.tagLabel[1] }}</tspan>
                                        </template>
                                        <tspan v-else class="node-tag" >{{ node.tag }}</tspan>
                                    </text>
                                    <line :x1="node.x + node.width / 2" :y1="node.y + tagLabelHeight * node.tagLabel.length + 6" class="link-line"
                                          :x2="node.x + node.width / 2" :y2="node.parent.y - (endChild(node) ? 35 : 28)"/>
                                </g>
                                <!-- the phrase structure node-and-connector graph, drawn in layers -->
                                <g v-for="layer in s.layers">
                                    <g v-for="node in layer">
                                        <text :x="node.x" :y="node.y" text-anchor="middle" alignment-baseline="hanging">
                                            <tspan class="node-tag" v-on:mouseenter="mouseEnterNode(node, $event)"
                                                                    v-on:click="nodeClick(node, $event)">{{ node.tag }}</tspan>
                                        </text>
                                        <line v-if="node.parent" :x1="node.x" :y1="node.y + 8" class="link-line"
                                                                 :x2="node.x" :y2="node.parent.y - (endChild(node) ? 35 : 28)"/>
                                        <path :d="childrenConnector(node)" class="link-line"></path>
                                        <line :x1="node.x" :y1="node.y - 14" class="link-line"
                                              :x2="node.x" :y2="node.y - 28"/>
                                    </g>
                                </g>
                            </svg>
                        </div>
                        <div v-if="debugOutput && s.debugging" class="debug-row k-flexrow k-table">
                            <div class="k-row"><div class="k-cell">POS list</div><pre class="k-cell">{{s.debugging.posList}}</pre></div>
                            <div class="k-row"><div class="k-cell">Mapped POS List</div><pre class="k-cell">{{s.debugging.mappedPosList}}</pre></div>
                            <div class="k-row"><div class="k-cell">MorphemeGroups</div><pre class="k-cell">{{s.debugging.morphemeGroups}}</pre></div>
                            <div class="k-row"><div class="k-cell">Phrases</div><pre class="k-cell">{{s.debugging.phrases}}</pre></div>
                            <div class="k-row"><div class="k-cell">ParseTree</div><pre class="k-cell">{{s.debugging.parseTree}}</pre></div>
                            <div class="k-row"><div class="k-cell">References</div><pre class="k-cell">{{s.debugging.references}}</pre></div>
                        </div>
                    </tenplate>
                </div>
            </div>

            <div v-if="wiktionaryUrl" class="k-row">
                <iframe :src="wiktionaryUrl"  class="wiktionary-iframe"></iframe>
            </div>
            <div id="definition" ref="defPopup" class="definition">
                <div class="k-table">
                    <div class="border-row k-row"><div v-if="references.annotation" class="def-pos k-cell">{{references.annotation}}</div></div>
                    <div class="border-row k-row"><div v-if="references.POS" class="def-pos k-cell">{{references.POS.descr}}</div></div>
                    <div class="def-row k-row"><div v-if="references.POS && references.POS.notes" class="def-notes k-cell">{{references.POS.notes}}</div></div>
                </div>
                <div class="k-table">
                    <div v-for="(def, index) in references.definition" :class="{'border-row': index == references.definition.length-1}" class="k-row">
                        <div class="k-cell def-label">{{def.partOfSpeech}}:</div>
                        <div class="k-cell"><ul><li v-for="w in def.text"><span>{{w}}</span></li></ul></div>
                    </div>
                    <div v-if="references.wordRefs" class="k-row refs-row">
                        <div class="k-cell def-label">References:</div>
                        <div class="k-cell"><ul>
                            <li  v-for="ref in references.wordRefs">
                                <a v-if="ref.slug" :href=ref.slug target="_blank">{{ref.title}}</a>
                                <div v-else >{{ref.title}}: {{ref.page}}</div>
                            </li></ul></div>
                    </div>
                </div>
            </div>
        </div>
        <!-- following template text elements used for computing text display bounds before rendering trees -->
        <svg id="template" style="visibility: hidden;" width="500" height="32">
            <text class="leaf-word"></text>
            <text class="leaf-tag"></text>
            <text class="node-tag"></text>
            <text class="word-word"></text>
        </svg>
    </div>

</template>

<script>
export default {
    name: 'App',

    // ------------ component local data ------------
	data: function() {
		return {
		    APIHost: "http://localhost:9000", // "http://localhost:9000", // ""
		    parsing: false,
		    sentence: "", // "밥을 먹은 후에 손을 씻는다", // "khaiii의 빌드 및 설치에 관해서는 빌드 및 설치 문서를 참고하시기 바랍니다.", // "나는 저녁으로 매운 김치와 국과 밥을 먹고 싶어요.", // "나는 요리하는 것에 대해서 책을 썼어요.", // "저의 딸도 행복해요", // "저는 비싼 음식을 좋아해요", // "나는 요리하는 것에 대해서 책을 썼어요.", // "모두 와줘서 고마워요.", "중국 음식은 좋아하기 때문에 중국 음식을 먹었어요.", // "나는 요리하는 것에 대해서 책을 쓸 거예요.", // "나는 저녁으로 매운 김치와 국과 밥을 먹고 싶어요.", // null, // "나는 그것에 대해서 책을 쓸 거야",
		    error: "",
            naverTranslation: "",
            sentences: [],
		    wiktionaryUrl: null,
		    parseButtonText: "Parse",
            translators: [{"title": "Google translate", "slug": "https://translate.google.com/#view=home&op=translate&sl=ko&tl=en&text=${sentence}"},
                          {"title": "Naver Papago translator", "slug": "https://papago.naver.com/?sk=ko&tk=en&st=${sentence}"},
                          {"title": "PNU spell-checker", "slug": "http://speller.cs.pusan.ac.kr"}],
		    levelHeight: 50,
            terminalHeight: 0, tagLabelHeight: 0,
            treeWidth: 0, treeHeight: 0,
            debugOutput: false,
            showAllLevels: false,
            references: {},
            defPopup: null,
            nodeInDef: null,
            mouseEnterX: null, mouseEnterY: null,
            definitionTimeout: null,
            terminalGap: 20, lineGap: 8,
            treeMarginX: 20, treeMarginY: 20
		};
	},

    ready: function () {
    },

	computed: {
	},

    // ---------- component methods ---------

	methods: {

        requestParse: function () {
            // send sentence to parser API
            self = this;
            self.parseButtonText = "Parsing...";
            self.error = self.wiktionaryUrl = "";
            self.parsing = true;
            $.ajax({
                method: "POST",
                url: self.APIHost + '/parse/', // '/parse/', // 'http://localhost:9000/parse/',
                crossDomain: true,
                cache: false,
                data: { sentence: self.sentence, showAllLevels: self.showAllLevels },
                success: function (response) {
                    self.parsing = false;
                    self.parseButtonText = "Parse";
                    if (response.result == 'OK') {
                        self.sentences = response.sentences;
                        self.buildDisplay();
                    }
                    else {
                        self.parsing = false;
                        self.parseButtonText = "Parse";
                        self.error = "Sorry, unable to parse";
                        self.sentences = [];
                    }
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    self.parsing = false;
                    self.parseButtonText = "Parse";
                    self.error = "Parsing failed - " + textStatus + ", " + errorThrown;
                    self.sentences = [];
                }
            });
            // and request translation
            self.getNaverTranslation(self.sentence);
        },

        buildDisplay: function () {
            // build display layout for 2nd test form
            var self = this;

            for (var si = 0; si < self.sentences.length; si++) {
                // prepare each sentence separately
                var s = self.sentences[si];
                if (!s.error) {
                    // build layer node-id lookup tables
                    var nodes = {}

                    function addID(n) {
                        nodes[n.id] = n;
                        n.parent = nodes[n.parent];
                        n.sentence = s;
                        for (var i = 0; i < n.children.length; i++)
                            addID(n.children[i]);
                    }

                    addID(s.parseTree.tree)

                    // grab terminals list
                    var terminalIDs = s.parseTree.layers[0],
                        terminals = [];
                    for (var i = 0; i < terminalIDs.length; i++) {
                        var t = nodes[terminalIDs[i]];
                        terminals.push(t);
                    }

                    // add owning-sentence object to phrase elements
                    for (var pi = 0; pi < s.phrases.length; pi++)
                        for (var ei = 0; ei < s.phrases[pi].length; ei++)
                            s.phrases[pi][ei].sentence = s;

                    // lay out original-text word line based on morphemeGroup word-groupings
                    var x = self.treeMarginX, y = self.treeMarginY + 10;
                    var words = [], height = 0;
                    var wi = 0, wci = 0,  // word & word-char indexes
                        ti = 0, tci = 0;      // terminal & terminal-char indexes
                    var t = null, ttw, ttt, ts, tcsx, tcex;  // current terminal & its SVG laytout text elements for word & terminal char start & end x positions
                    // run over words in morpheme-groupings, tracking character positions in terminals, picking up coords as original words are traversed
                    for (wi = 0; wi < s.morphemeGroups.length; wi++) {
                        var g = s.morphemeGroups[wi];
                        var word = {word: g[0], y: y}, chars = g[1];
                        for (wci = 0; wci < chars.length;) {
                            // track chars in terminal
                            if (!t || tci >= t.word.length) {
                                // end of terminal, grab next & update terminal layout vars
                                t = terminals[ti];
                                ti += 1;
                                tci = 0;
                                ttw = self.getLayoutElement(t.word, "leaf-word");
                                ttt = self.getLayoutElement(self.longestLabel(t.tagLabel), "leaf-tag");
                                var wWidth = ttw.getComputedTextLength(), tWidth = ttt.getComputedTextLength(),
                                    width = Math.max(wWidth, tWidth);
                                var dw = (width - wWidth) / 2;  // word-start delta
                                ts = x + dw;  // record this terminal's start & bump along for next terminal's pos
                                x += width + self.terminalGap;  // bump along terminal x pos using prior terminals' width
                            }
                            // update current terminal chars pos
                            tcsx = ts + ttw.getStartPositionOfChar(tci).x;
                            tcex = ts + ttw.getEndPositionOfChar(tci).x;
                            if (wci == 0) // start of word
                                word.x = tcsx;
                            if (wci == chars.length - 1) { // end of word, figure width, track max height
                                word.width = tcex - word.x;
                                height = Math.max(height, self.textBBox(word.word, "word-word").height);
                            }
                            //
                            tci += 1;  // bump along terminal & word characters
                            wci += 1;
                        }
                        // collect layed-out words
                        words.push(word);
                    }

                    s.words = words;
                    x = self.treeMarginX;
                    y += height + self.lineGap;

                    // lay out terminals line
                    self.terminalHeight = self.tagLabelHeight = height = 0;
                    for (var i = 0; i < terminals.length; i++) {
                        var t = terminals[i];
                        t.x = x;
                        t.y = y;
                        var tew = self.getLayoutElement(t.word, "leaf-word"),
                            tet = self.getLayoutElement(self.longestLabel(t.tagLabel), "leaf-tag");
                        t.width = Math.max(tew.getComputedTextLength(), tet.getComputedTextLength());
                        self.terminalHeight = Math.max(self.terminalHeight, self.textBBox(t.word, "leaf-word").height)
                        self.tagLabelHeight = Math.max(self.tagLabelHeight, self.textBBox(t.tagLabel[0], "leaf-tag").height)
                        height = Math.max(height, self.terminalHeight + 4 + self.tagLabelHeight * (t.tagLabel.length + 1));
                        x += t.width + self.terminalGap;
                    }
                    //
                    s.terminals = terminals;

                    // compute tree layout coords
                    y += self.lineGap + height;
                    // draw an inverted tree from the terminal layer down; start at layer above terminals,
                    //   find parent & siblings & layout parent midway between siblings
                    var layerIDs = s.parseTree.layers,
                        layers = [];
                    for (var i = 1; i < layerIDs.length; i++) {
                        layers.push([]);
                        var entryIDs = layerIDs[i];
                        for (var j = 0; j < entryIDs.length; j++) {
                            var node = nodes[entryIDs[j]];
                            layers[i - 1].push(node);
                            node.y = y + (i - 1) * self.levelHeight;
                            // get children bounds & center me within that
                            var c0 = node.children[0], cn = node.children[node.children.length - 1],
                                x0, xn = 0;
                            if (node.children.length > 0) {
                                x0 = c0.level >= 0 ? c0.x : c0.x + c0.width / 2;
                                xn = cn.level >= 0 ? xn = cn.x : cn.x + cn.width / 2;
                            } else
                                x0 = c0.level >= 0 ? c0.x : c0.x + c0.width / 2;
                            node.x = (x0 + xn) / 2;
                            node.x0 = x0;
                            node.xn = xn;
                        }
                    }

                    // figure graph bounds
                    var lt = terminals[terminals.length - 1];
                    s.treeWidth = self.treeMarginX * 2 + lt.x + lt.width;
                    s.treeHeight = y + (layers.length - 1) * self.levelHeight + self.treeMarginY;
                    s.layers = layers;

                    //console.log(layers);
                }
            }
        },

        childrenConnector: function (node) {
            // return SVG path commands drawing connector spanning children nodes with rounded ends
            return "M " + node.x0 + " " + (node.y - 38) +
                " q 0 10 10 10" +
                " H " + (node.x0 + 10) + " " + (node.xn - 10) +
                " q 10 0 10 -10";
        },

        endChild: function (node) {
            // return true if node is first or last child of parent
            return node == node.parent.children[0] || node == node.parent.children[node.parent.children.length - 1];
        },

        getLayoutElement: function (text, cls) {
            // return SVG text element of given class containing given text
            var t = $("#template ." + cls)[0];
            t.textContent = text;
            return t;
        },

        longestLabel: function(tagLabel) {
            // tag labels are one or two lines, in an array of lines, return longest label line (for layout computations)
            return tagLabel.length == 1 || tagLabel[0].length > tagLabel[1].length ? tagLabel[0] : tagLabel[1];
        },

        textBBox: function (text, cls) {
            // return bounding box for text rendered in given class
            if (text == '')
                return {width: 0, height: 0}
            var t = this.getLayoutElement(text, cls);
            console.log('bbox', text, t.textContent, cls, t.getBBox().width);
            return t.getBBox();
        },

        leafTagClass: function(node) {
            // return class for 2nd line in terminal node tag-label, a word definition if noun or verb
            return node.tag[0] == 'N' || node.tag[0] == 'V' ? "leaf-tag-def" : "leaf-tag";
        },

        // deprecated. now wiki link is in def popup
        lookupWord: function (node) {
            // lookup word in wiktionary, open in iframe
            //  construct dictionary form of verb if needed
            var word = node.tag[0] == 'V' && node.word[node.word.length - 1] != '다' ? node.word + '다' : node.word;
            this.wiktionaryUrl = "https://en.wiktionary.org/wiki/" + word;
        },

        showReferences: function(node, event) {
            // construct and show word/node reference popup
            var self = this;
            var s = node.sentence;
            var references = s.references;
            var r = {};
            if (node.type == 'word') {
                // retrieve and pop word leaf word references
                var word = references.wikiKeys[node.word];
                $.ajax({
                    method: "GET",
                    url: self.APIHost + "/definition/" + word, // "/definition/" + word, // "http://localhost:9000/definition/" + word,
                    crossDomain: true,
                    cache: false,
                    success: function (response) {
                        // set POS description & any synth-tag notes
                        r.POS = references.posTable[node.tag];
                        // display any non-empty useful result
                        r.definition = response.length > 0 ? response : null;
                        // add reference links
                        r.wordRefs = references.references[node.word];
                        // show referece popup if anything to show
                        if (r.definition || r.wordRefs) {
                            self.popReferences(r, node, event);
                        }
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        self.references = {};
                    }
                });
            }
            else {  // parse-tree rule node, pop-up any rule annotation
                var annotation = references.ruleAnnotations[node.tag];
                if (annotation) {
                    r.annotation = annotation.descr;
                    r.wordRefs = annotation.refList;
                    self.popReferences(r, node, event);
                }
            }
        },

        getNaverTranslation: function(sentence) {
            // call for Naver/Papago NMT translation into English
            var self = this;
            self.naverTranslation = "";
            $.ajax({
                method: "POST",
                url: self.APIHost + "/translate/", // http://localhost:9000
                crossDomain: true,
                data: {source: "ko", target: "en", text: sentence},
                success: function (response) {
                    if (response.result == "OK")
                        self.naverTranslation = response.translatedText;
                }
            });
        },

        popReferences: function(r, node, event) {
            // display node reference popup
            this.references = r;
            this.nodeInDef = node;
            var popup = self.$refs["defPopup"];
            var x = event.clientX,
                y = event.clientY;
            popup.style.top = (y + 12) + 'px';
            popup.style.left = (x + 12) + 'px';
            popup.classList.add("show");
        },

        nodeClick: function(node, event) {
	        // handle click on node word, open reference popup if not already
            if (this.definitionTimeout)
                clearTimeout(self.definitionTimeout);
            var popup = $("#definition")[0];
            if (!popup.classList.contains("show") || this.nodeInDef != node) {
                this.showReferences(node, event);
            }
        },

        mouseEnterNode: function (node, event) {
            var self = this;
            if (self.definitionTimeout)
                clearTimeout(self.definitionTimeout);
	        // handle mouse enter, note entering mouse-pos & show refs if (roughly) still after 250ms
	        self.mouseEnterX = event.screenX; self.mouseEnterY = event.screenY;
	        self.definitionTimeout = setTimeout(function() {
                if (Math.abs(self.mouseEnterX - window.screenX) < 20 && Math.abs(self.mouseEnterY - window.screenY) < 20)
                    // only show if mouse has hovered over node for 500ms
	                self.showReferences(node, event);
            }, 250);
        },

        appMouseUp: function (event) {
            // this is for MobileSafari which doesn't send mouse events unless on explictly clickable elements
            var popup = $("#definition");
            if (popup.length > 0 &&
                !popup.is(event.target) // if the target of the click isn't the container...
                && popup.has(event.target).length === 0) // ... nor a descendant of the container
            {
                popup[0].classList.remove("show");
            }
        }
    }
}

//# register for mouse-move events
document.onmousemove = function(e) {
    var event = e || window.event;
    window.screenX = event.screenX;
    window.screenY = event.screenY;
    //console.log("* ", event.screenX, window.screenX, event.screenY, window.screenY);
}

// dismiss popup ref div if click is outside popup
document.onmouseup = function (e) {
    var popup = $("#definition");
    if (popup.length > 0 &&
        !popup.is(e.target) // if the target of the click isn't the container...
        && popup.has(e.target).length === 0) // ... nor a descendant of the container
    {
        popup[0].classList.remove("show");
    }
};

</script>

<style>

    #app {
        font-family: Helvetica, simsun, nanumgothic, '나눔고딕', dotum, sans-serif;
        font-size: 112%;
        -webkit-tap-highlight-color: transparent;
    }

    #input-row {
        justify-content: space-between;
    }

    #input-title {
        font-weight: bold;
    }

    #attribution {
        font-size: 70%;
        color: gray;
    }

    #input-sentence {
        width: 45em;
        margin: 20px 20px 5px 20px;
        padding: 10px 10px 0px 10px;
        font-size: 18px;
        vertical-align: top;
    }

    #parse-button {
        vertical-align: top;
        margin-top: 15px;
        /* padding: 5px; */
        font-size: 14px;
        width: 75px;
    }

    #controls-row {
        float: right;
        font-size: 11px;
    }

    #controls-row a {
        /* padding-right: 10px; */
        color:rgba(85, 117, 255, 1);
    }

    .controls-row label {
        padding-left: 10px;
    }

   .debug-row {
        padding-top: 10px;
        font-size: 12px;
    }

   .debug-row .k-row > .k-cell {
        font-weight: bold;
        padding: 4px;
    }

    .output-row {
        width: 1200px;
        overflow: scroll;
    }

    #naver-translation {
        padding-left: 50px;
        padding-bottom: 20px;
        padding-top: 8px;
        color: #ab5405;
        font-size: 14px;
    }

    #naver-translation span {
        color: #696863;
        font-size: 13px;
        padding-right: 6px;
    }

    .pos-list {
        padding-left: 50px;
    }

   .parse-tree {
        padding-left: 50px;
    }

    .link-line {
        stroke: rgb(114, 194, 119);
        stroke-width: 0.8px;
        fill: none;
    }

    .word-line {
        stroke: rgb(105, 105, 105);
        stroke-width: 0.5px;
    }

    .leaf-word {
        fill: #00a6de;
        color: #00a6de;
    }

    .leaf-tag {
        fill: #8d8c86;
        color: #8d8c86;
        font-size: 12px;
    }

    .leaf-tag-def {
        fill: #ab5405;
        color: #ab5405;
        font-size: 12px;
    }

    .leaf-word {
        fill: #00a6de;
        cursor: pointer;
    }

    .word-word {
        fill: black;
        color: black;
    }

    .phrase-plus {
        color: #8d8c86;
    }

    .node-tag {
        fill: #ad47de;
        font-size: 13px;
        cursor: pointer;
    }

    .wiktionary-iframe {
        margin-top: 20px;
        width: 100%;
        height: 900px;
        border-width: thin;
    }

    /* definition-popup styles  */
    .definition {
        visibility: hidden;
        background-color: rgba(200, 200, 200, .80);
        color: #111;
        font-size: 12px;
        border-radius: 6px;
        padding: 0px 5px 5px 5px;
        position: fixed;
        z-index: 1;
        max-width: 500px;
    }

    .definition .def-label {
        width: 10%;
    }

    .definition .def-pos {
        width: 100%;
        padding-bottom: 5px;
        padding-top: 4px;
        /* font-weight: bold; */
    }

    .definition .def-notes {
        width: 100%;
    }

    .definition .k-table {
        border-collapse: collapse;
        width: 100%;
    }

    .definition .border-row {
        border-bottom: 0.5px solid gray;
        padding-bottom: 5px;
    }

    .definition .refs-row {
        /* border-top: 0.5px solid gray; */
    }

    .definition .k-cell {
        padding-left: 4px;
        /* padding-top: 3px; */
        padding-bottom: 2px;
    }

    .definition ul {
        padding-left: 14px;
        margin-left: 5px;
        maring-top: 02px;
        margin-bottom: 0px;
        font-size: 50%;
    }

    .definition li span {
        font-size: 200%;
        vertical-align:middle;
    }

    .definition li a {
        font-size: 200%;
        vertical-align:middle;
    }
    .definition li div {
        font-size: 200%;
    }

    /* toggle this class - hide and show the popup */
    .show {
      visibility: visible;
      -webkit-animation: fadeIn 0.5s;
      animation: fadeIn 0.5s;
    }

    /* Add animation (fade in the popup) */
    @-webkit-keyframes fadeIn {
      from {opacity: 0;}
      to {opacity: 1;}
    }

    @keyframes fadeIn {
      from {opacity: 0;}
      to {opacity:1 ;}
    }
    
    .error-msg {
        color: red;
        font-style: italic;
        font-size: 14px;
        padding-left: 30px;
    }

    .parse-fail-msg {
        color: red;
        font-size: 18px;
        padding-left: 30px;
    }
    .parse-fail-unrec {
        font-size: 16px;
        padding-left: 30px;
        color: rgb(82, 82, 82);;
    }
    .parse-fail-poslist {
        color: rgb(82, 82, 82);;
        font-size: 16px;
        padding-left: 30px;
    }
    .parse-fail-word {
        color: #346f8d;;
        padding-left: 5px;
    }
    .parse-fail-tag {
        color: rgb(127, 140, 144);
        font-size:14px;
    }

    /* useful CSS3 layout classes */
    .k-flexrow {
        display: flex;
        flex-direction: row;
    }

    .k-flexcol {
        display: flex;
        flex-direction: column;
    }

    .k-down-shadow {
        box-shadow: 0px 4px 7px #d0d0d0;
        border-width: 0;
    }

    .k-table {
        display: table;
    }

    .k-row {
        display: table-row;
    }

    .k-cell {
        display: table-cell;
    }

</style>
