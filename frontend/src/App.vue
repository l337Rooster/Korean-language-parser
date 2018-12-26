<!-- main KoNLPy parser    -->

<template>
    <div id="app">
        <div class="k-flexcol">
            <div id="input-row" class="k-flexrow ">
                <div id="input-title" >Korean sentence parser</div>
                <div id="attribution">v0.3.1 - JBW - based on the <a href="https://github.com/kakao/khaiii">Kakao Hangul Analyzer III</a></div>
            </div>
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
                        <!-- label id="parser-select-label" for="parser-select">Select parser: </label>
                        <select id="parser-select" v-model="parserSelect" class="k-cell">
                            <option v-for="p in parsers" >{{p}}</option>
                        </select -->
                            <label for="debug">Debug output: </label>
                            <input class="" type="checkbox" id="debug" v-model="debugOutput">
                        </td>
                        <td>&nbsp;</td>
                    </tr>
                </table>
            </div>
            <div v-if="!parsing" id="output-row" class="k-flexrow k-table">
                <div v-if="error" class="error-msg">
                    {{ error }}
                </div>
                <template v-else>
                    <div id="pos-list">
                        <div v-for="phrase in phrases">
                            <template v-for="element, i in phrase">
                                <span v-if="element.type == 'word' && i > 0" class="phrase-plus"> + </span>
                                <span v-if="element.type == 'word'" class="leaf-word"
                                      v-on:mouseenter="mouseEnterWord(element, $event)">{{ element.word }}</span>
                                <span v-if="element.type == 'label'" class="leaf-tag">({{ element.word }})</span>
                            </template>
                        </div>
                    </div>
                    <svg id="parse-tree" class="tree-svg" :width="parseTreeWidth" :height="parseTreeHeight" style="background-color: rgba(0,0,0,0);">
                        <g v-for="node in nodes">
                            <line v-if="node.parent" :x1="node.xOffset + node.width / 2" :y1="node.yOffset - 15" class="link-line"
                                  :x2="node.parent.xOffset + node.parent.width / 2" :y2="node.parent.yOffset + 4"/>
                            <text :x="node.xOffset + node.width / 2" :y="node.yOffset" text-anchor="middle" alignment-baseline="hanging">
                                <template v-if="node.word">
                                    <tspan class="leaf-word" v-on:mouseenter="mouseEnterWord(node, $event)">{{ node.word }}</tspan>
                                    <tspan :x="node.xOffset + node.width / 2" dy="1.3em" class="leaf-tag">{{ tagDisplay(node.tag) }}</tspan>
                                </template>
                                <tspan v-else class="node-tag" >{{ node.tag }}</tspan>
                            </text>
                        </g>
                    </svg>
                    <svg id="parse-tree-2" class="tree-svg" :width="parseTreeWidth" :height="400" style="background-color: rgba(0,0,0,0);">
                        <g v-for="word in words">
=                            <text :x="word.x + word.width / 2" :y="word.y" text-anchor="middle" alignment-baseline="hanging">
                                <tspan class="word-word">{{ word.word }}</tspan>
                            </text>
                            <line :x1="word.lineX" :y1="word.y + 6" class="word-line"
                                  :x2="word.lineX + word.lineWidth" :y2="word.y + 6"/>
                        </g>
                        <g v-for="node in terminals">
=                            <text :x="node.x + node.width / 2" :y="node.y" text-anchor="middle" alignment-baseline="hanging">
                                <template v-if="node.word">
                                    <tspan class="leaf-word" v-on:mouseenter="mouseEnterWord(node, $event)">{{ node.word }}</tspan>
                                    <tspan :x="node.x + node.width / 2" dy="1.3em" class="leaf-tag">{{ tagDisplay(node.tag) }}</tspan>
                                </template>
                                <tspan v-else class="node-tag" >{{ node.tag }}</tspan>
                            </text>
                        </g>
                    </svg>
                </template>
            </div>
            <div v-if="!parsing && debugOutput && debugging" id="debug-row" class="k-flexrow k-table">
                <div class="k-row"><div class="k-cell">POS list</div><pre class="k-cell">{{debugging.posList}}</pre></div>
                <div class="k-row"><div class="k-cell">Mapped POS List</div><pre class="k-cell">{{debugging.mappedPosList}}</pre></div>
                <div class="k-row"><div class="k-cell">Phrases</div><pre class="k-cell">{{debugging.phrases}}</pre></div>
                <div class="k-row"><div class="k-cell">Parse tree</div><pre class="k-cell">{{debugging.parseTree}}</pre></div>
                <div class="k-row"><div class="k-cell">References</div><pre class="k-cell">{{debugging.references}}</pre></div>
            </div>
            <div v-if="wiktionaryUrl" class="k-row">
                <iframe :src="wiktionaryUrl"  class="wiktionary-iframe"></iframe>
            </div>
            <div id="definition" ref="defPopup" class="definition">
                <div class="k-table">
                    <div class="border-row k-row"><div v-if="POS" class="def-pos k-cell">{{POS.descr}}</div></div>
                    <div class="def-row k-row"><div v-if="POS && POS.notes" class="def-notes k-cell">{{POS.notes}}</div></div>
                </div>
                <div class="k-table">
                    <div v-for="(def, index) in definition" :class="{'border-row': index == definition.length-1}" class="k-row">
                        <div class="k-cell">{{def.partOfSpeech}}:</div>
                        <div class="k-cell"><ul><li v-for="w in def.text"><span>{{w}}</span></li></ul></div>
                    </div>
                    <div class="k-row refs-row">
                        <div class="k-cell">References:</div>
                        <div class="k-cell"><ul><li  v-for="ref in wordRefs"><a :href=ref.slug target="_blank">{{ref.name}}</a></li></ul></div>
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
		    parsing: false,
            mappedPosList: null,
		    parseTree: null,
		    posList: null,
		    phrases: null,
            debugging: null,
		    sentence: "나는 그것에 대해서 책을 쓸 거야",
		    error: "",
		    nodes: [],
		    answer: "Answer goes here",
		    wiktionaryUrl: null,
		    parseButtonText: "Parse",
            translators: [{"title": "Google translate", "slug": "https://translate.google.com/#view=home&op=translate&sl=ko&tl=en&text=${sentence}"},
                          {"title": "Naver Papago translator", "slug": "https://papago.naver.com/?sk=ko&tk=en&st=${sentence}"},
                          {"title": "PNU spell-checker", "slug": "http://speller.cs.pusan.ac.kr"}],
		    levelHeight: 50,
		    minNodeWidth: 50,
		    nodePadding: 20,
            hangulCharWidth: 12,
		    parseTreeWidth: 1200,
		    parseTreeHeight: 600,
            parsers: ["JHannanum", "Kkma", "KOMORAN", "MeCab-ko", "Open Korean Text"], // supported parsers
            defaultParser: "KOMORAN",
            debugOutput: false,
            parserSelect: "KOMORAN",
            definition: null,
            defPopup: null,
            mouseEnterX: null, mouseEnterY: null,
            definitionTimeout: null,
            references: null,
            wordRefs: null,
            POS: null,
            // second tree display layout test
            parseTree2: null,
            morphemeGroups: null,
            terminalGap: 20, lineGap: 20,
            treeMarginTop: 20, treeMarginLeft: 10,
            terminals: [],
            words: []
		};
	},

    ready: function () {
    },

	computed: {
	},

    // ---------- component methods ---------

	methods: {

	    requestParse: function() {
	        // send sentence to parser API
	        self = this;
	        self.parseButtonText = "Parsing...";
	        self.error = self.wiktionaryUrl = "";
	        self.parsing = true;
            $.ajax({
                method: "POST",
                url: 'http://localhost:9000/parse/', // '/parse/', // 'http://localhost:9000/parse/',
                crossDomain: true,
                cache: false,
                data: { sentence: this.sentence },
                success: function(response) {
                    self.parsing = false;
	                self.parseButtonText = "Parse";
	                if (response.result == 'OK') {
	                    self.mappedPosList = response.mappedPosList;
	                    self.morphemeGroups = response.morphemeGroups;
                        self.parseTree = response.parseTree;
                        self.posList = response.posList;
                        self.phrases = response.phrases;
                        self.references = response.references;
                        self.debugging = response.debugging;
                        //  console.log(JSON.stringify(self.debugging));
                        self.buildDisplay();
                        self.buildDisplay2();
                    }
                    else {
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    self.parsing = false;
	                self.parseButtonText = "Parse";
                    self.error = "Parsing failed - " + textStatus + ", " + errorThrown;
                }
            });
	    },

	    buildDisplay: function() {
	        // recurse parse-tree, build display tree layers
	        var idCounter = 0, maxY = 0;
	        var text = [], links = [];
	        var layers = [], nodes = [];
            // temp: take a deep copy of parsetree for display2 experiment
            self.parseTree2 = JSON.parse(JSON.stringify(self.parseTree));
            //
	        function subtree(t, level) {
	            if (layers.length < level+1)
	                layers[level] = { count:0, width: 0, level: level, entries: [] };  // add new layer level;
	            var width = 0;
	            if (t.type == 'tree') {
	                for (var i = 0; i < t.children.length; i++) {
	                    var child = t.children[i];
	                    child.parent = t;
	                    width += subtree(t.children[i], level + 1);
	                }
	            }
	            else
	                width = Math.max(self.minNodeWidth, self.nodePadding + t.word.length * self.hangulCharWidth);
	            //
	            t.id = nodes.length;
	            nodes.push(t);
	            t.yOffset = level * self.levelHeight + 20;
	            maxY = Math.max(maxY, t.yOffset);
	            t.width = width;
	            layers[level].entries.push(t)
	            return width;
	        }
	        //
	        subtree(self.parseTree, 0);

	        // compute layout coords
	        var maxX = 0;
	        for (var i = 0; i < layers.length; i++) {
	            var entries = layers[i].entries;
	            //console.log('layer ' + i);
	            var nodeOffset = 30;
	            for (var j = 0; j < entries.length; j++) {
                     var node = entries[j];
                     nodeOffset = Math.max(nodeOffset, node.parent && node.parent.xOffset || 0);
                     node.xOffset = nodeOffset;
                     nodeOffset += node.width;
                     maxX = Math.max(maxX, nodeOffset);
                     //console.log('  tag = ' + node.tag + ' width = ' + node.width + ', xy = ' + [node.xOffset, node.yOffset].toString());
	            }
	        }
	        //console.log(layers);

	        // trigger graph draw
	        self.parseTreeHeight = maxY + 20;
	        self.parseTreeWidth = maxX + 20;
	        self.nodes = nodes;
	    },

        buildDisplay2: function() {
	        // build display layout for 2nd test form
            var self = this;
            var terminals = [], layers = [], nodes = [];
            // descend parse-tree, figuring tree levels & collecting terminals
	        function subtree(t, level) {
	            if (layers.length < level + 1)
	                // add new layer level
	                layers[level] = { count:0, width: 0, level: level, entries: [] };
	            if (t.type == 'tree') {
	                // recurse down subtree
	                for (var i = 0; i < t.children.length; i++) {
	                    var child = t.children[i];
	                    child.parent = t;
	                    subtree(child, level + 1);
	                }
	            }
	            else {
	                // terminal node, gather
                    terminals.push(t);
                }
	        }
	        subtree(self.parseTree2, 0);

	        // lay out word line based on morphemeGroup word-groupings
            var x = self.treeMarginLeft, y = self.treeMarginTop;
            var words = [], height = 0, lastTag = '?';
            for (var i = 0; i < self.morphemeGroups.length; i++) {
                var g = self.morphemeGroups[i];
                var word = g[0], width = 0, lineWidth = 0;
                for (var j = 0; j < g[1].length; j++) {
                    // compute bounds of morpheme group
                    console.log(' ', j, g[1][j][0]);
                    lastTag = g[1][j][1];
                    var bbox1 = self.textBBox(g[1][j][0], "leaf-word"), bbox2 = self.textBBox(self.tagDisplay(g[1][j][1]), "leaf-tag");
                    width += Math.max(bbox1.width, bbox2.width) + (j < g[1].length-1 ? self.terminalGap : 0);
                    lineWidth += bbox1.width + (j < g[1].length-1 ? self.terminalGap : 0);
                    height = Math.max(height, bbox1.height, bbox2.height);
                }
                words.push({word: word, x: x, y: y, width: width, height: height, lineX: x + (width - lineWidth) / 2, lineWidth: lineWidth});
                console.log(word, x, width);
                // no terminal gap if we split prior terminal (tag == '')
                x += width + (lastTag != '' ? self.terminalGap : 0);
            }
            self.words = words;
            x = self.treeMarginLeft; y += height + self.lineGap;

        // [['나는', [('나', 'NP'), ('는', 'JX')]],
        //  ['그것에', [('그것', 'NP'), ('에', '')]],
        //  ['대해서', [(' 대하여서', 'PRP_11')]],
        //  ['책을', [('책', 'NNG'), ('을', 'JKO')]],
        //  ['쓸', [('쓰', 'VV'), ('ㄹ', '')]],
        //  ['거야.', [(' 거 이', 'PSX_13'), ('야', 'EF')]]]

        // [('나', 'NP'),
        //  ('는', 'JX'),
        //  ('그것', 'NP'),
        //  ('에 대하여서', 'PRP_11'),
        //  ('책', 'NNG'),
        //  ('을', 'JKO'),
        //  ('쓰', 'VV'),
        //  ('ㄹ 거 이', 'PSX_13'),
        //  ('야', 'EF'),
        //  ('.', 'SF')]

	        // lay out terminal line
            for (var i = 0; i < terminals.length; i++) {
                var t = terminals[i];
                var bbox1 = self.textBBox(t.word, "leaf-word"), bbox2 = self.textBBox(self.tagDisplay(t.tag), "leaf-tag");
                t.x = x; t.y = y;
                t.width = Math.max(bbox1.width, bbox2.width); t.height = Math.max(bbox1.height, bbox2.height);
                console.log(t.word, t.x, t.width);
                x += t.width + self.terminalGap;
            }
            //
            self.terminals = terminals;
        },

        textBBox: function(text, cls) {
            // return bounding box for text rendered in given class
            var t = $("#template ." + cls)[0];
            t.textContent = text;
            return t.getBBox();
        },

        // deprecated. now wiki link is in def popup
	    lookupWord: function(node) {
	        // lookup word in wiktionary, open in iframe
	        //  construct dictionary form of verb if needed
	        var word = node.tag[0] == 'V' && node.word[node.word.length-1] != '다' ? node.word + '다' : node.word;
	        this.wiktionaryUrl = "https://en.wiktionary.org/wiki/" + word;
	    },

        tagDisplay: function(tag) {
	        // return displayable
            return tag != '' ? this.references.posTable[tag].wikiPOS : '';
	        // return tag.split("_")[0];
        },

        showReferences: function(node, event) {
            // only show if mouse has hovered over node for 500ms
            //console.log(self.mouseEnterX, window.screenX, self.mouseEnterY, window.screenY);
            if (Math.abs(self.mouseEnterX - window.screenX) < 20 && Math.abs(self.mouseEnterY - window.screenY) < 20) {
                var word = self.references.wikiKeys[node.word];
                $.ajax({
                    method: "GET",
                    url: "http://localhost:9000/definition/" + word, // "/definition/" + word, // "http://localhost:9000/definition/" + word,
                    crossDomain: true,
                    cache: false,
                    success: function (response) {
                        // set POS description & any synth-tag notes
                        self.POS = self.references.posTable[node.tag];
                        // display any non-empty useful result
                        self.definition = response.length > 0 ? response : null;
                        // add reference links
                        self.wordRefs = self.references.references[node.word];
                        // show referece popup if anything to show
                        if (self.definition || self.wordRefs) {
                            var popup = self.$refs["defPopup"];
                            var x = event.clientX,
                                y = event.clientY;
                            popup.style.top = (y + 12) + 'px';
                            popup.style.left = (x + 12) + 'px';
                            popup.classList.add("show");
                        }
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        self.definition = self.wordRefs = null;
                    }
                });
            }
        },

        mouseEnterWord: function(node, event) {
            var self = this;
            if (self.definitionTimeout)
                clearTimeout(self.definitionTimeout);
	        // handle mouse enter, note entering mouse-pos & show refs if (roughly) still after 250ms
	        self.mouseEnterX = event.screenX; self.mouseEnterY = event.screenY;
	        self.definitionTimeout = setTimeout(self.showReferences, 250, node, event);
        },

        // deprecated, now def popup is sticky, dismissed with outside click
        mouseLeaveWord: function() {
            if (self.definitionTimeout)
                clearTimeout(self.definitionTimeout);
            this.definition = this.wordRefs = null;
            this.$refs["defPopup"].classList.remove("show");
            this.mouseEnterLoc = null;
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

    #debug-row {
        padding-top: 10px;
        font-size: 12px;
    }

    #debug-row .k-row > .k-cell {
        font-weight: bold;
        padding: 4px;
    }

    #output-row {
        width: 1200px;
        overflow: scroll;
    }

    #pos-list {
        padding-left: 50px;
    }

    .link-line {
        stroke: rgb(114, 194, 119);
        stroke-width: 0.8px;
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
        font-size: 11px;
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
        font-size: 12px;
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
        position: absolute;
        z-index: 1;
        max-width: 500px;
    }

    .definition .def-pos {
        width: 100%;
        padding-bottom: 5px;
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


function renderedTextSize(string, font, fontSize) {
  var paper = Raphael(0, 0, 0, 0);
  paper.canvas.style.visibility = 'hidden';

  var el = paper.text(0, 0, string);
  el.attr('font-family', font);
  el.attr('font-size', fontSize);

  var bBox = el.getBBox();
  paper.remove();

  return {
    width: bBox.width,
    height: bBox.height
  };
}
