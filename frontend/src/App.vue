<!-- main KoNLPy parser    -->

<template>
    <div id="app">
        <div class="k-flexcol">
            <div id="input-row" class="k-flexrow ">
                <div id="input-title" >Korean sentence parser</div>
                <div id="attribution">v0.3.0 - JBW - based on the <a href="https://github.com/kakao/khaiii">Kakao Hangul Analyzer III</a></div>
            </div>
            <div class="k-flexrow k-table">
                <div class="k-row">
                    <textarea id="input-sentence" class="k-cell" placeholder="enter Korean sentence to parse" v-model="sentence"></textarea>
                    <button autofocus class="k-cell" id="parse-button" v-on:click="requestParse" :disabled="sentence == ''">{{ parseButtonText }}</button>
                </div>
                <div class="k-row controls-row">
                    <label for="debug">Debug output: </label>
                    <input type="checkbox" id="debug" v-model="debugOutput">
                    <!-- label id="parser-select-label" for="parser-select">Select parser: </label>
                    <select id="parser-select" v-model="parserSelect" class="k-cell">
                        <option v-for="p in parsers" >{{p}}</option>
                    </select -->
                </div>
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
                                <span v-if="element.type == 'word'" class="leaf-word" v-on:click="lookupWord(element)"
                                      v-on:mouseenter="mouseEnterWord(element, $event)" v-on:mouseleave="mouseLeaveWord()">{{ element.word }}</span>
                                <span v-if="element.type == 'label'" class="leaf-tag">({{ element.word }})</span>
                            </template>
                        </div>
                        <!--div v-for="parse in parseList">
                            <span v-for="word in parse[0]" class="leaf-word" v-on:click="lookupWord(word)">{{ word }} </span>:
                            <span class="leaf-tag">{{ parse[1] }}</span>
                        </div>
                        <br><br>
                        <div v-for="pos in posList">
                            <span class="leaf-word">{{pos[0]}}:</span> <span class="leaf-tag">{{pos[1]}}</span>
                        </div-->
                    </div>
                    <svg id="parse-tree" class="tree-svg" :width="parseTreeWidth" :height="parseTreeHeight" style="background-color: rgba(0,0,0,0);">
                        <g v-for="node in nodes">
                            <line v-if="node.parent" :x1="node.xOffset + node.width / 2" :y1="node.yOffset - 15" class="link-line"
                                  :x2="node.parent.xOffset + node.parent.width / 2" :y2="node.parent.yOffset + 4"/>
                            <text :x="node.xOffset + node.width / 2" :y="node.yOffset" text-anchor="middle" alignment-baseline="hanging">
                                <template v-if="node.word">
                                    <tspan class="leaf-word" v-on:click="lookupWord(node)" v-on:mouseenter="mouseEnterWord(node, $event)"
                                           v-on:mouseleave="mouseLeaveWord()">{{ node.word }}</tspan>
                                    <tspan :x="node.xOffset + node.width / 2" dy="1.3em" class="leaf-tag">{{ node.tag }}</tspan>
                                </template>
                                <tspan v-else class="node-tag">{{ node.tag }}</tspan>
                            </text>
                        </g>
                    </svg>
                </template>
            </div>
            <div v-if="!parsing && debugOutput && debugging" id="debug-row" class="k-flexrow k-table">
                <div class="k-row"><div class="k-cell">POS list</div><pre class="k-cell">{{debugging.posList}}</pre></div>
                <div class="k-row"><div class="k-cell">Mapped POS List</div><pre class="k-cell">{{debugging.mappedPosList}}</pre></div>
                <div class="k-row"><div class="k-cell">Parse list</div><pre class="k-cell">{{debugging.parseList}}</pre></div>
                <div class="k-row"><div class="k-cell">Phrases</div><pre class="k-cell">{{debugging.phrases}}</pre></div>
                <div class="k-row"><div class="k-cell">Parse tree</div><pre class="k-cell">{{debugging.parseTree}}</pre></div>
            </div>
            <div v-if="wiktionaryUrl" class="k-row">
                <iframe :src="wiktionaryUrl"  class="wiktionary-iframe"></iframe>
            </div>
            <div id="definition" ref="defPopup" class="definition k-table">
                <div v-for="def in definition" class="k-row">
                    <div class="k-cell">{{def.partOfSpeech}}:</div>
                    <div class="k-cell"><ul><li v-for="w in def.text"><span>{{w}}</span></li></ul></div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

export default {
    name: 'App',

	data: function() {
		return {
		    parsing: false,
            mappedPosList: null,
		    parseTree: null,
		    posList: null,
		    parseList: null,
		    phrases: null,
            debugging: null,
		    sentence: "",
		    error: "",
		    nodes: [],
		    answer: "Answer goes here",
		    wiktionaryUrl: null,
		    parseButtonText: "Parse",
		    levelHeight: 50,
		    nodeWidth: 60,
		    nodePadding: 10,
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
		};
	},

    ready: function () {
    },

	computed: {
	},

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
                        self.parseTree = response.parseTree;
                        self.posList = response.posList;
                        self.parseList = response.parseList;
                        self.phrases = response.phrases;
                        self.debugging = response.debugging;
                        //  console.log(JSON.stringify(self.debugging));
                        self.buildDisplay();
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
	        function subtree(t, level) {
	            if (layers.length < level+1)
	                layers[level] = { count:0, width: 0, level: level, entries: [] };  // add new layer level;
	            var count = 0;
	            if (t.type == 'tree') {
	                for (var i = 0; i < t.children.length; i++) {
	                    var child = t.children[i];
	                    child.parent = t;
	                    count += subtree(t.children[i], level + 1);
	                }
	            }
	            else
	                count = 1;
	            //
	            layers[level].count += count;
	            t.id = nodes.length;
	            nodes.push(t);
	            t.yOffset = level * self.levelHeight + 20;
	            maxY = Math.max(maxY, t.yOffset);
	            t.width = count * self.nodeWidth;
	            layers[level].entries.push(t)
	            return count;
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

	    lookupWord: function(node) {
	        // lookup word in wiktionary, open in iframe
	        //  construct dictionary form of verb if needed
	        var word = node.tag[0] == 'V' && node.word[node.word.length-1] != '다' ? node.word + '다' : node.word;
	        this.wiktionaryUrl = "https://en.wiktionary.org/wiki/" + word;
	    },

        mouseEnterWord: function(node, event) {
            var self = this;
            if (self.definitionTimeout)
                clearTimeout(self.definitionTimeout);
	        var showDef = function() {
	            // only show if mouse has hovered over node for 500ms
                //console.log(self.mouseEnterX, window.screenX, self.mouseEnterY, window.screenY);
	            if (Math.abs(self.mouseEnterX - window.screenX) < 15 && Math.abs(self.mouseEnterY - window.screenY) < 15) {
                    var word = node.tag[0] == 'V' && node.word[node.word.length - 1] != '다' ? node.word + '다' : node.word;
                    $.ajax({
                        method: "GET",
                        url: "http://localhost:9000/definition/" + word, // "/definition/" + word, // "http://localhost:9000/definition/" + word,
                        crossDomain: true,
                        cache: false,
                        success: function (response) {
                            // display any non-empty useful result
                            if (response.length > 0) {
                                self.definition = response;
                                var popup = self.$refs["defPopup"];
                                var x = event.clientX,
                                    y = event.clientY;
                                popup.style.top = (y + 12) + 'px';
                                popup.style.left = (x + 12) + 'px';
                                popup.classList.add("show");
                            }
                        },
                        error: function (jqXHR, textStatus, errorThrown) {
                            self.definition = null;
                        }
                    });
                }
            };
	        // handle mouse enter, start a timer & see if mouse still after 500ms
	        self.mouseEnterX = event.screenX; self.mouseEnterY = event.screenY;
	        self.definitionTimeout = setTimeout(showDef, 250);
        },

        mouseLeaveWord: function() {
            if (self.definitionTimeout)
                clearTimeout(self.definitionTimeout);
            this.definition = [];
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
        margin: 20px;
        padding: 10px;
        font-size: 18px;
    }

    #parse-button {
        vertical-align: top;
        margin-top: 35px;
        padding: 5px;
        font-size: 14px;
        width: 75px;
    }

    .controls-row {
        text-align: right;
        font-size: 12px;
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
        stroke-width: 0.8;
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
å
    .definition .k-cell {
        padding-left: 4px;
        padding-top: 5px;
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
