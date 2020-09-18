import requests
import json
import time
import re

from bs4 import BeautifulSoup


HEADERS = {'user-agent': 'Mozilla/5.0'}


def clean(url):
    """
    Performs minor cleanup of url
    """

    url = url.split("?")[0]
    url = url.rstrip("/") + "/"

    return url


def parse(url):
    """
    Extract all decks from the database and determine their color and
    deck type. Save decklists accordingly.
    """

    master_json = {}

    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, features="html5lib")

    for i, p in enumerate(soup.select("#decks > li:not(.hidden)")):

        # Extract deck color
        color = parse_color(p)

        # Extract deck type
        deck_type = parse_deck_type(p)

        # Extract all decklists and add them to master json
        for deck_link in p.select(".ddb-decklists li a"):

            name = deck_link.text.strip()
            print(f"Parsing deck: {name}")
            decklist = parse_decklist_platform(clean(deck_link.get("href")))

            if color not in master_json:
                master_json[color] = {}

            if deck_type not in master_json[color]:
                master_json[color][deck_type] = {}

            master_json[color][deck_type][name] = decklist
            time.sleep(3)

    with open("cedh_decklists.json", "w") as f:
        json.dump(master_json, f)


def parse_color(element):
    """
    Extract commander color identity for given deck element.
    Possible values are a combination of the following:
        w - White
        u - Blue
        b - Black
        r - Red
        g - Green

    or 'Colorless' if no other colors are extracted.
    """

    color_string = ""

    for color in element.select(".ddb-colors > svg"):
        cur_color = color.get("class")[0][1:]
        if cur_color == "x":
            continue
        color_string += cur_color

    if not color_string:
        return "Colorless"
    return color_string


def parse_deck_type(element):
    """
    Extracts deck supertype from databse list element section
    """

    return element.get('data-title')


def parse_decklist_platform(url):
    """
    Determines decklist platform and chooses decklist parsing accordingly.
    """

    for platform_name in DECKLIST_PLATFORM_PARSERS:
        if platform_name in url:
            return DECKLIST_PLATFORM_PARSERS[platform_name](url)

    print("No matching platform found! Returning empty decklist")

    return []


def parse_moxfield(url):
    deck_id = re.search(r"moxfield\.com\/decks\/([\w\-]+)\/", url).group(1)
    api_string = f"https://api.moxfield.com/v1/decks/all/{deck_id}"
    response = requests.get(api_string, headers=HEADERS)
    result = response.json()

    output_decklist = []
    for card in result["mainboard"]:
        output_decklist += int(result["mainboard"][card]["quantity"]) * [card]

    # Also add commander(s)
    for commander in result["commanders"]:
        output_decklist.append(commander)

    return output_decklist


def parse_tappedout(url):
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, features="html5lib")
    result = []

    for card in soup.select(".boardlist .member"):

        # Skip sideboard cards
        if "boardcontainer-side" in card.get("id").lower():
            continue

        # Skip maybeboard cards
        if "boardcontainer-maybe" in card.get("id").lower():
            continue

        num = int(card.select(".qty.board")[0].get("data-qty"))
        name = card.select(".card-link")[0].get("data-name")
        result += num * [name]

    # Parse commander card names with additional GET requests
    for title in soup.select(".board-col h3"):
        if "commander" in title.text.lower():
            for commander_link in title.find_next_sibling().select("a"):
                response = requests.get(
                    f"https://tappedout.net{commander_link.get('href')}",
                    headers=HEADERS
                )
                commander_soup = BeautifulSoup(response.text, features="html5lib")
                result.append(commander_soup.select(".well-jumbotron h1")[0].text.strip())
                time.sleep(1)

    return result


def parse_archidekt(url):
    deck_id = re.search(r"archidekt\.com\/decks\/(\w+)\#", url).group(1)
    api_string = f"https://archidekt.com/api/decks/{deck_id}/small/"
    response = requests.get(api_string, headers=HEADERS)
    result = response.json()

    output_decklist = []
    for card in result["cards"]:
        if card["category"].lower() == "maybeboard":
            continue

        output_decklist += int(card["quantity"]) * [card["card"]["oracleCard"]["name"]]

    # NOTE: Commander is already present in decklist
    # so it does not have to be added separately

    return output_decklist


def parse_scryfall(url):
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, features="html5lib")
    result = []

    for i, card in enumerate(soup.select(".deck-list-section-entries .deck-list-entry")):
        num = int(card.select(".deck-list-entry-count")[0].text.strip())
        name = card.select(".deck-list-entry-name")[0].text.strip().split("\n")[0]
        result += num * [name]

    return result


def parse_deckbox(url):
    response = requests.get(url, headers=HEADERS)
    deck_json = re.search(r"Tcg\.MtgDeck\({.+?}, ({.+})\);", response.text).group(1)
    data = json.loads(deck_json)
    result = []

    for x in data:
        result.append(data[x]["name"])

    return result


URL = "https://cedh-decklist-database.com/"

DECKLIST_PLATFORM_PARSERS = {
    "moxfield": parse_moxfield,
    "tappedout": parse_tappedout,
    "archidekt": parse_archidekt,
    "scryfall": parse_scryfall
}


if __name__ == "__main__":
    parse(URL)
