# Korean Sentence Parser
Based on the [Kakao Hangul Analyzer III](https://github.com/kakao/khaiii) (khaiii) and JBW's phrase parser.  The parser webapp is built using
the [Flask](http://flask.pocoo.org) Python app-server, [Vue JS](https://vuejs.org) for the front-end, and [Webpack](https://webpack.js.org) for build-management

#### *NOTE: this readme is not complete, will add setup, build & driving instructions soon.*


## Build Setup

If needed, install node.js from [here](https://nodejs.org/) and Python 3.6 or greater from [here](https://www.python.org/downloads/), or as part of the highly-recommended Anaconda Python distribution
 [here](https://www.anaconda.com/download/).  

Clone or download the [Korean sentence parser](https://github.com/johnw3d/Korean-language-parser) repo, ``cd`` into its top-level directory and run:
```
# install Python requirements
$ pip3 install -r requirements.txt
```
The *Kakao Hangul Analyzer III* needs to be downloaded from the [kakao/khaiii github page](https://github.com/kakao/khaiii) and 
prepared according to its [build and installation instructions](https://github.com/kakao/khaiii/wiki/빌드-및-설치). 

To install front-end and webpack dependencies, ``cd`` into the ``frontend`` subdirectory and run:
``` bash
# install front-end and webpack dependencies
$ npm install
```

## Running the development build

The dev build can be run in two modes:
1. With a statically-built production front-end and the Python-based API server running and listening on port 9000, serving both the main index.html and handling API requests from the front end.
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
