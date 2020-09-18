import json
import time
import requests

from analyze import *


if __name__ == "__main__":

    dataset = load_database()

    all_cards, num_decks = summary(dataset)
    card_dictionary = {}

    # loop over all found cards on DDB and add their info to master json
    for card in all_cards.keys():
        print(f"Fetching card: {card}")
        response = requests.get(f"https://api.scryfall.com/cards/named?exact={card}")
        card_dictionary[card] = response.json()
        time.sleep(0.5)

    with open("card_dictionary.json", "w") as f:
        json.dump(card_dictionary, f)
