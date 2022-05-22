from flask import Flask, render_template, request, escape
from random_word import RandomWords
import requests
import jsonpath_ng
import json
import urllib.parse
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

from backend.util.db import engine, Base

flask_app = Flask(__name__)
app = FastAPI()
Base.metadata.create_all(bind=engine)


# flask routes
@flask_app.route('/login')
def login():  # put flask_application's code here
    read_login()
    return render_template("login.html")


@app.get('/login')
def read_login():
    return "HELLO WORLD"


@flask_app.route('/register')
def register():
    return render_template("register.html")


@flask_app.route('/')
def index():
    return render_template("base.html")


@flask_app.route('/', methods=['POST'])
def word_search_post():
    user_text = request.form['user_text']
    if user_text != "":
        return word_definition(user_text)
    else:
        return render_template("base.html")


app.mount("/v1", WSGIMiddleware(flask_app))


def word_definition(word):
    url = "https://api.dictionaryapi.dev/api/v2/entries/en/"

    # Parse and clean the user's word so that it is appropriate for the API call
    clean_url = url + urllib.parse.quote(word)

    # Check that the url does not contain any whitespaces, i.e., that the user only entered 1 word
    if "%20" in clean_url:
        return render_template("word_not_found.html"), 404

    response = requests.get(clean_url)
    entries = response.json()

    try:
        # Parse the JSON response to find the word, pronunciation and audio
        query_word = jsonpath_ng.parse('[0].word[*]')
        for match in query_word.find(entries):
            word = (json.dumps(match.value)).strip('"')

        query_pronunciation = jsonpath_ng.parse('[0].phonetics[*].text[*]')
        for match in query_pronunciation.find(entries):
            pronunciation = json.loads(json.dumps(match.value))

        query_audio = jsonpath_ng.parse('[0].phonetics[*].audio[*]')
        for match in query_audio.find(entries):
            audio_link = (json.dumps(match.value)).strip('"')

        part_of_speech = []
        definitions = []
        examples = []
        synonyms = []
        antonyms = []

        # Find the required information from the JSON response
        for entry in entries:
            for meaning in entry["meanings"]:
                for synonym in meaning["synonyms"]:
                    synonyms.append(synonym)
                for antonym in meaning["antonyms"]:
                    antonyms.append(antonym)

                for definition in meaning["definitions"]:
                    part_of_speech.append(meaning["partOfSpeech"])
                    definitions.append(definition["definition"])

                    for synonym in definition["synonyms"]:
                        synonyms.append(synonym)
                    for antonym in definition["antonyms"]:
                        antonyms.append(antonym)

                    if "example" in definition:
                        examples.append(definition["example"])
                    else:
                        examples.append("!")

        word_results = zip(part_of_speech, definitions, examples)

        # Show the play audio button only when a word is present
        audio_button = True
    except KeyError:
        # Render word_not_found.html if API doesn't return any definitions
        return render_template("word_not_found.html"), 404

    return render_template("word.html", word=word, pronunciation=pronunciation, audio=audio_link,
                           word_results=word_results,
                           audio_button=audio_button, synonyms=synonyms, antonyms=antonyms)


def word_of_the_day():
    r = RandomWords()
    r.word_of_the_day()


if __name__ == '__main__':
    flask_app.run()
