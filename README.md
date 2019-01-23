# Korean Sentence Parser
Based on the [Kakao Hangul Analyzer III](https://github.com/kakao/khaiii) (khaiii) and JBW's phrase parser.  The parser webapp is built using
the [Flask](http://flask.pocoo.org) Python app-server, [Vue JS](https://vuejs.org) for the front-end, and [Webpack](https://webpack.js.org) for 
build-management

The parser, currently accessible online in development form at [http://hangugeo.org/analyzer](http://hangugeo.org/analyzer), is meant to be
a learning tool for students of 
the Korean language. It is still a work-in-progress and so may not give correct or even any parsing for a particular sentence, and may be 
offline at times.

### Example UI

Below is screen-shot of the front-end UI and an example sentence-parsing output.  You enter one or more sentences in the text-box at the top 
and hit the ``Parse`` button.  The main output is a parse-tree showing the original words in the sentence in black at the top sitting over the 
lexical phonemes & phoneme-patterns that make up the sentence, in teal.  Under each phoneme is a descriptive part-of-speech and under the
nouns & verbs are English
translations from the Naver/Papago translator public API in orange.  In cases where a word has multiple meanings, the one picked by Naver as its 
favorite meaning for the word out-of-context is shown.

Descending from that is a putative phrase-structure tree, showing the construction of larger phrases and clauses and the final predicate from
smaller ones.  If you hover the mouse over one of the teal phonemes or phoneme patterns, a gray box pops up showing the definition and any 
information
about it found on [Wiktionary](https://en.wiktionary.org/wiki/Category:Korean_language), along with links to related sections in selected
online references.

![Parsing example](frontend/static/example-parse.png)

#### Parse-tree form
The current parse-tree form, its descriptive labels and other annotations, are a work-in-progress and are an attempt at an explication of Korean
grammar with a decided English bent, for English learners, and it's not clear if a more formal, Korean set of grammatical phrasings & annotations
would be pedagogically preferred.  This is one of the areas of active development and discussion.

Korean, of course, is a language of myriad special connective, conjugational, ending and other forms; Korean grammar books are mostly filled
not with syntax-rules as you'd find in an English grammar text, but with lists of these patterns, describing their form, the way the should be attached
or applied and the particular meaning or nuance they impart.  The hope is to have this parser detect and show these patterns in the parse-tree.  

The example above shows an instance of this in the predicate, where it has detected the common auxiliary-verb pattern for expressing to-want-to-do
the suffixed verb: **V-고 싶다**.  The parser has isolated that pattern and labeled it appropriately.  A good part of the code at the end of
``backend.tagmap.py``
is a start at a set of pattern-specs that allow the parser to detect these patterns and label them usefully.   The hope is that
this set will be filled out by open-source contributions, along with other improvements that open-sourcing should bring.  


#### *NOTE: this readme is not complete, the setup, build & driving instructions and implementation notes will be completed soon.*


## Build Setup

If needed, install node.js from [here](https://nodejs.org/) and Python 3.6 or greater either from [here](https://www.python.org/downloads/) or 
as part of the highly-recommended Anaconda Python distribution
 [here](https://www.anaconda.com/download/).  

Clone or download the [Korean sentence parser](https://github.com/johnw3d/Korean-language-parser) repo, ``cd`` into its top-level directory and 
run:
```
# install Python requirements
$ pip3 install -r requirements.txt
```
Download the *Kakao Hangul Analyzer III* from the [kakao/khaiii github page](https://github.com/kakao/khaiii) and 
prepare according to its [build and installation instructions](https://github.com/kakao/khaiii/wiki/빌드-및-설치). 

To install front-end and webpack dependencies, ``cd`` into the ``frontend`` subdirectory and run:
``` bash
# install front-end and webpack dependencies
$ npm install
```

## Running the development build

The dev build can be run in two modes:
1. With a statically-built production front-end and the Python-based API server running and listening on port 9000, serving both the main 
index.html and handling API requests from the front end.
2. WIth a hot-reloading front-end being served on port 8080 and the Python API server handling API calls alone on port 9000.

In both cases, start the API server in its own shell by ``cd``ing into the top-level directory for this repo and run:
```
# start the API dev server
$ python3 backend/api.py
```
You can launch the parser web-app by pointing a browser at [http://localhost:9000/analyzer](http://localhost:9000/analyzer).

Open a separate shell to build & optionally run the front-end.

To statically-build the front-end, ``cd`` into the ``frontend`` subdirectory and run:
```
# build for production with minification
$ npm run build
```
To run the hot-reloading development version of the front-end, in the same directory run:

```
# serve with hot reload at localhost:8080
$ npm run dev
```
In this case, point a browser at [http://localhost:8080/analyzer](http://localhost:9000/analyzer) to lauch the parser front end.

## Implementation notes

The main parsing operation is performed by the ``backend.api.parseInput()`` function, most-often called by the handler for 
the front-end's AJAX ``/parse/`` REST API call, also in the ``backend.api`` module.

The parsing process has 4 stages, explained in further detail below:
1. Pass the input string throught the Khaiii morhpeme analyzer to get a list of the individual parts-of-speech it contains
2. Apply a series of mappings to that morpheme list that distinguish and provide more detail about specific morphemes and morhpeme patterns
3. Pass the mapped morhpeme list through one of two available phrase parsers to get a nested parse-tree of phrase structures in the input
4. Apply an annotation pass to the parse-tree, adding descriptive detail, definitions, references, re-labelings, and so on for a more
useful display

This parse-tree and various reference tables are returned in JSON form by the /parse/ API call to the front-end JavaScript AJAX call
for processing and display by the Vue js template and methods in ``frontend/src/App.vue``.
 
#### Morpheme analysis

The input string is run through the ``khaiiiAPI.analyze()`` morpheme analyzer function.  This returns a sequence of ``KhaiiiWord`` objects,
one for each word & punctuation symbol in the input string, including sentence-end markers for each sentence it finds in the input string.
These word objects themselves contain a sequence of ``KhaiiiMorph`` morpheme objects, one for each distinct lexical morhpheme in the input word,
separating out things like verb-stems, honorific markers, particles and other basic lexical components making up the word.  The returned
word-sequence is broken into sentences and each sentence is further processed in the following steps.

As an example, consider the following sentence:

>#### 그 작은 소년은 빨리 달렸다.

The Khaiii analyzer returns the breakdown of words in the sentence into one or more lexical phonemes and assigns each a part-of-speech
(POS)
tag, as shown in the table below. Note how it separates transforming and topic particles from their stems and even 'decompresses' common 
conjugation shortenings as it does in the past-tense predicate of that sentence.

|Word   |  Morpheme | POS tag |     |
|:-----:|:---------:|:-------:|-----|
| 그     | 그   | MM |  Determiner  |
| 작은   | 작   | VA  |  Descriptive verb|
|       | 은   | ETM |  Adjective-forming particle |   
| 소년은  | 소년 |  NNG |  General noun |
|       | 은  | JX  |  Topic-marking particle |
| 빨리   | 빨리 | MAG |  Adverb |
| 달렸다  | 달리 | VV  |  Verb  |
|       |었   | EP  | Predicate suffix |
|       | 다  | EF  |  Predicate final |
| .     | .  | SF   |   Sentence final |

(The ``backend.tagmap.py`` module contains a fill list of the POS tags that can be emitted by the Khaiii analyzer)


 
 ['그:MM',
 '작:VA',
 '은:ETM',
 '소년:NNG',
 '은:JX',
 '빨리:MAG',
 '달리:VV',
 '었:EP',
 '다:EF',
 '.:SF']
 
 [('그', 'MM'),
 ('작', 'VA'),
 ('은', 'ETM'),
 ('소년', 'NNG'),
 ('은', 'TOP_4'),
 ('빨리', 'MAG'),
 ('달리', 'VV'),
 ('었', 'PSX_31'),
 ('다', 'EF'),
 ('.', 'SF')]

