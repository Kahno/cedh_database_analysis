import json
import time
import requests

from analyze import *


if __name__ == "__main__":

    dataset = load_database()

    all_cards, num_decks = summary(dataset)
    card_dictionary = {}

    # loop over all found cards on DDB
    for card in all_cards.keys():

        print(f"Fetching card: {card}")

        # perform scryfall api call
        response = requests.get(f"https://api.scryfall.com/cards/named?exact={card}")

        # save json data to master json
        card_dictionary[card] = response.json()

        # wait 0.5 seconds
        time.sleep(0.5)

    with open("card_dictionary.json", "w") as f:
        json.dump(card_dictionary, f)
