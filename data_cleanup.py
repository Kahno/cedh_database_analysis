import json
import os
import requests

from analyze import (
    normalize, flatten, load_database, load_scryfall, load_lite, summary
)
from tqdm import tqdm

def load_scry_data():
    fpath = 'json_data/scryfall_data.json'
    if not os.path.exists(fpath):
        #download bulk data from scryfall
        #get url for download through scryfall api

        data = requests.get('https://api.scryfall.com/bulk-data').json()
        url = None
        for dataset in data['data']:
            if dataset['type'] == 'oracle_cards':
                url = dataset['download_uri']
                break
        if url is None:
            raise Exception('Could not find oracle_cards dataset')
        #download json file from link and save it to
        response = requests.get(url, stream=True)
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024 #1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        with open(fpath, 'wb') as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            print("ERROR, something went wrong")

    with open(fpath, "r") as f:
        data = json.loads(f.read())

    data_dict = {
        c['name']: c
        for c
        in tqdm(data)
    }

    return data_dict


def lightweight_scryfall_dict():
    with open("json_data/scryfall_card_dictionary.json", "r") as f:
        data = json.loads(f.read())

    lw_dict = {}

    for card in data:
        cur_name = normalize(card)

        lw_dict[cur_name] = {}
        lw_dict[cur_name]["color_identity"] = data[card]["color_identity"]
        lw_dict[cur_name]["type_line"] = data[card]["type_line"]
        lw_dict[cur_name]["cmc"] = data[card]["cmc"]
        lw_dict[cur_name]["color_identity"] = data[card]["color_identity"]
        lw_dict[cur_name]["full_name"] = card

    with open("json_data/lite_scryfall_dict.json", "w") as f:
        json.dump(lw_dict, f)


def normalized_decklists():
    db = flatten(load_database())

    normalized_decks = {}

    for deck in db:
        if isinstance(db[deck], list):
            normalized_decks[deck] = [normalize(card) for card in db[deck]]

    with open("json_data/normalized_decklists.json", "w") as f:
        json.dump(normalized_decks, f)


def fix_land_color_identity():
    scry = load_scryfall(filename="json_data/scryfall_card_dictionary.json")
    scry_lite = load_lite(filename="json_data/lite_scryfall_dict.json")

    patch_data = {
        "Marsh Flats": ["W", "B"],
        "Verdant Catacombs": ["B", "G"],
        "Misty Rainforest": ["U", "G"],
        "Scalding Tarn": ["U", "R"],
        "Arid Mesa": ["R", "W"],
        "Wooded Foothills": ["R", "G"],
        "Windswept Heath": ["G", "W"],
        "Flooded Strand": ["W", "U"],
        "Polluted Delta": ["U", "B"],
        "Bloodstained Mire": ["B", "R"],
        "Urborg, Tomb of Yawgmoth": ["B"]
    }

    for card in patch_data:
        print(card)
        print("Before fix:")
        print(scry_lite[normalize(card)])
        print(scry[card]["color_identity"])

        scry[card]["color_identity"] = patch_data[card]
        scry_lite[normalize(card)]["color_identity"] = patch_data[card]

        print("After fix:")
        print(scry_lite[normalize(card)])
        print(scry[card]["color_identity"])

        print()

    with open("json_data/scryfall_card_dictionary.json", "w") as f:
        json.dump(scry, f)
    print("Scryfall dict UPDATED")

    with open("json_data/lite_scryfall_dict.json", "w") as f:
        json.dump(scry_lite, f)
    print("Scryfall lite dict UPDATED")


if __name__ == "__main__":

    dataset = load_database()
    all_cards, num_decks = summary(dataset)
    #card_dictionary = {}

    # loop over all found cards on DDB and add their info to master json

    card_dictionary = load_scry_data()
    card_dictionary = {k:card_dictionary[k] for k in all_cards.keys()}

    with open("json_data/scryfall_card_dictionary.json", "w") as f:
        json.dump(card_dictionary, f)

    import requests
    import time

    print(f"Number of all cards: {len(all_cards)}\n")

    '''try:
        for i, card in enumerate(all_cards.keys()):
            print(f"{i+1} Fetching card: {card}")

            response = None

            for _ in range(3):
                try:
                    response = requests.get(
                        f"https://api.scryfall.com/cards/named?exact={card}",
                        timeout=1
                    )
                    break
                except requests.ReadTimeout:
                    pass

            if not response:
                raise Exception("Failed after 3 retries. :(")

            card_dictionary[card] = response.json()
            time.sleep(0.3)
    except Exception:
        with open("json_data/card_dictionary.json", "w") as f:
            json.dump(card_dictionary, f)'''

    lightweight_scryfall_dict()
    print("Lightweight scryfall DONE")

    normalized_decklists()
    print("Normalized decklists DONE")

    fix_land_color_identity()


    #######################################################################

    '''
    dataset = load_database()
    all_cards, num_decks = summary(dataset)

    with open("json_data/card_dictionary.json", "r") as f:
        data = json.loads(f.read())

    all_new_cards = set(all_cards)
    all_old_cards = set([x for x in data])

    import requests
    import time

    print(len(data.keys()))

    saved = False

    """"""
    try:
        for i, card in enumerate(all_new_cards - all_old_cards):
            print(f"{i+1} Fetching card: {card}")

            response = None

            for _ in range(3):
                try:
                    response = requests.get(
                        f"https://api.scryfall.com/cards/named?exact={card}",
                        timeout=1
                    )
                    break
                except requests.ReadTimeout:
                    pass

            if not response:
                raise Exception("Failed after 3 retries. :(")

            data[card] = response.json()
            time.sleep(0.3)

    except Exception:
        with open("json_data/card_dictionary.json", "w") as f:
            json.dump(data, f)
            saved = True
    """"""

    if not saved:
        with open("json_data/card_dictionary.json", "w") as f:
            json.dump(data, f)
    '''
