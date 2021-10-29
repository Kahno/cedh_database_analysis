import time
import re

from flask import Flask
from flask import json
from flask import request
from flask import Response

from analyze import recommend, generality_info, compare, create_core
from data_cleanup import normalize
from scraper import parse_decklist_platform


app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    content = open("index.html").read()
    return Response(content, mimetype="text/html")


@app.route("/fetch", methods=["POST"])
def fetch_decklist():
    data_json = json.loads(request.data)

    decklist = parse_decklist_platform(data_json["url"], wait_time=2)
    fetch_result = ""

    for card in decklist:
        fetch_result += f"1 {card}\n"

    fetch_result.strip("\n")

    return Response(
        json.dumps({
            "decklist": fetch_result,
            "generality": generality_info(decklist)
        }),
        status=200,
        mimetype="application/json"
    )


@app.route("/compare", methods=["POST"])
def compare_against_ddb():
    data_json = json.loads(request.data)
    decklist = data_json["decklist"]
    identity = data_json["identity"]
    clean_decklist = {}

    for card in decklist.split("\n"):
        if card:
            clean_card = " ".join(card.split()[1:])
            clean_decklist[normalize(clean_card)] = clean_card

    if not clean_decklist:
        fetch_result = ("No decklist provided! Fetch via decklist "
                        "URL or paste in above text box.")
    else:
        fetch_result = compare(clean_decklist, identity)

    time.sleep(1)

    return Response(fetch_result, status=200, mimetype="application/json")


@app.route("/recommend_lands", methods=["POST"])
def recommend_lands():
    data_json = json.loads(request.data)
    decklist = data_json["decklist"]
    excludelist = data_json["excludelist"]
    identity = data_json["identity"]
    clean_decklist = []
    clean_excludelist = []

    for card in decklist.split("\n"):
        if card:
            clean_card = " ".join(card.split()[1:])
            clean_decklist.append(normalize(clean_card))

    for card in excludelist.split("\n"):
        if card:
            clean_card = card.split("(")[0]
            clean_card = re.search(r"[0-9]*\.?\s*(.+)", clean_card).group(1)
            clean_excludelist.append(normalize(clean_card.strip()))

    if not clean_decklist:
        fetch_result = ("No decklist provided! Fetch via decklist "
                        "URL or paste in above text box.")
    else:
        fetch_result = recommend(
            clean_decklist,
            identity,
            clean_excludelist,
            land_mode=True
        )

    time.sleep(1)

    return Response(fetch_result, status=200, mimetype="application/json")


@app.route("/recommend", methods=["POST"])
def recommend_cards():
    data_json = json.loads(request.data)
    decklist = data_json["decklist"]
    excludelist = data_json["excludelist"]
    identity = data_json["identity"]
    clean_decklist = []
    clean_excludelist = []

    for card in decklist.split("\n"):
        if card:
            clean_card = " ".join(card.split()[1:])
            clean_decklist.append(normalize(clean_card))

    for card in excludelist.split("\n"):
        if card:
            clean_card = card.split("(")[0]
            clean_card = re.search(r"[0-9]*\.?\s*(.+)", clean_card).group(1)
            clean_excludelist.append(normalize(clean_card.strip()))

    if not clean_decklist:
        fetch_result = ("No decklist provided! Fetch via decklist "
                        "URL or paste in above text box.")
    else:
        fetch_result = recommend(clean_decklist, identity, clean_excludelist)

    time.sleep(1)

    return Response(fetch_result, status=200, mimetype="application/json")


@app.route("/generate_core", methods=["POST"])
def generate_core():
    data_json = json.loads(request.data)

    identity = data_json["identity"]
    raw_ratio = data_json["ratio"]

    if not raw_ratio:
        result = create_core(identity)
    else:
        try:
            result = create_core(identity, float(raw_ratio))
        except ValueError:
            result = "Invalid ratio value specified!"

    return Response(result, status=200, mimetype="application/json")


if __name__ == "__main__":
    app.run(host="localhost", port=5000)
