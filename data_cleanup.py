import re
import json
import time
import requests

from analyze import *


def normalize(card_name):
    card_name = card_name.lower().replace("-", " ")

    card_name = re.sub(r"[\!\'\"\(\)\&\,\.\/\:\?\_\®]", "", card_name)
    card_name = re.sub(r"[àáâ]", "a", card_name)
    card_name = re.sub(r"[é]", "e", card_name)
    card_name = re.sub(r"[í]", "i", card_name)
    card_name = re.sub(r"[ö]", "o", card_name)
    card_name = re.sub(r"[úû]", "u", card_name)

    return card_name


def lightweight_scryfall_dict():
    with open(SCRYFALL_CARD_DICTIONARY, "r") as f:
        data = json.loads(f.read())

    lightweight_dict = {}

    for card in data:
        cur_name = normalize(card)

        lightweight_dict[cur_name] = {}
        lightweight_dict[cur_name]["color_identity"] = data[card]["color_identity"]
        lightweight_dict[cur_name]["type_line"] = data[card]["type_line"]
        lightweight_dict[cur_name]["cmc"] = data[card]["cmc"]
        lightweight_dict[cur_name]["color_identity"] = data[card]["color_identity"]
        lightweight_dict[cur_name]["full_name"] = card

    with open("json_data/lite_scryfall_dict.json", "w") as f:
        json.dump(lightweight_dict, f)


def normalized_decklists():
    flat_database = flatten(load_database())

    normalized_decks = {}

    for deck in flat_database:
        normalized_decks[deck] = [normalize(card) for card in flat_database[deck]]

    with open("json_data/normalized_decklists.json", "w") as f:
        json.dump(normalized_decks, f)


if __name__ == "__main__":

    """
    dataset = load_database()
    all_cards, num_decks = summary(dataset)
    card_dictionary = {}

    # loop over all found cards on DDB and add their info to master json
    for card in all_cards.keys():
        print(f"Fetching card: {card}")
        response = requests.get(f"https://api.scryfall.com/cards/named?exact={card}")
        card_dictionary[card] = response.json()
        time.sleep(0.5)

    with open("json_data/card_dictionary.json", "w") as f:
        json.dump(card_dictionary, f)

    """

    lightweight_scryfall_dict()
    print("Lightweight scryfall DONE")

    normalized_decklists()
    print("Normalized decklists DONE")
