#  backend/api.py  - Konlpy Korean parser API
#
#
__author__ = 'jwainwright'

import logging, zipfile, gzip, pprint, os, tempfile, shutil, threading
from flask import (Flask, request, abort, render_template, Response, jsonify)
from flask_cors import CORS

import konlpy  # see  http://konlpy.org/en/latest/
import nltk

# instantiate Flask (global) app
konlpyApp = Flask('app',
               static_folder="./dist/static",
               template_folder="./dist")
CORS(konlpyApp)
#
konlpyApp.config.update(
    DEBUG=True,
    SECRET_KEY = "iu877hy3jnd8**yd98y334%$#Rjxhg6222",
    SESSION_COOKIE_HTTPONLY = False
)

def run_dev_server():
    "launch Flask dev server"
    konlpyApp.run(host = '0.0.0.0',
               port = 80,
               debug = True)

# -------- page request handlers --------

parser = None
nodeData = {}

@konlpyApp.route('/analyzer')
def analyzer():
    "Konlpy analyzer main page"
    return render_template("/index.html")

# -------- API handlers ----------------

@konlpyApp.route('/parse/', methods=['POST'])
def parse():
    "parse POSTed Korean sentence"
    # grab sentence to parse
    sentence = request.form.get('sentence')
    if not sentence:
        return jsonify(result="FAIL", msg="Missing sentence")

    # for now, just use the Kkma parser, todo: make this a parameter
    # extract tagged parts of speech
    words = konlpy.tag.Kkma().pos(sentence)
    #konlpy.utils.pprint(words)

    # Define a nltk chunk grammar, or chunking rules, then chunk; again just for Kkma for now
    # todo: needs building out, is parser-specific
    grammar = """
    np: {<N.*><J.*>?}   	# Noun phrase
    vp: {<V.*><E.*>?}       # Verb phrase
    ap: {<A.*>*}            # Adjective phrase
    """
    # gen chunk tree from POS under above chunking grammar
    parser = nltk.RegexpParser(grammar)
    chunkTree = parser.parse(words)
    # print(chunks.pprint())

    # dict-ify tree
    def asDict(chunk):
        if isinstance(chunk, nltk.Tree):
            return dict(type='tree', tag=chunk.label(), children=[asDict(t) for t in chunk])
        else:
            return dict(type='pos', word=chunk[0].strip(), tag=chunk[1])
    #
    import pprint
    pprint.pprint(asDict(chunkTree))

    return jsonify(result="OK", parseTree=asDict(chunkTree))

#
if __name__ == "__main__":
    #
    run_dev_server()
