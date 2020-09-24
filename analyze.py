import json

import pandas as pd
import numpy as np


MASTER_JSON_FILE = "json_data/cedh_decklists.json"
NORM_MASTER_JSON_FILE = "json_data/normalized_decklists.json"

SCRYFALL_CARD_DICTIONARY = "json_data/scryfall_card_dictionary.json"
LITE_SCRYFALL_DICT = "json_data/lite_scryfall_dict.json"

BASIC_LANDS = [
    "Plains",
    "Island",
    "Swamp",
    "Mountain",
    "Forest",

    "Snow-Covered Plains",
    "Snow-Covered Island",
    "Snow-Covered Swamp",
    "Snow-Covered Mountain",
    "Snow-Covered Forest"
]

def load_database():
    """
    Loads ddb from json file
    """

    with open(MASTER_JSON_FILE, "r") as f:
        data = json.loads(f.read())

    return data


def load_normalized():
    with open(NORM_MASTER_JSON_FILE, "r") as f:
        data = json.loads(f.read())

    return data


def load_lite():
    with open(LITE_SCRYFALL_DICT, "r") as f:
        data = json.loads(f.read())

    return data


def load_scryfall():
    """
    Loads scryfall data from json file
    """

    with open(SCRYFALL_CARD_DICTIONARY, "r") as f:
        scryfall_card_dict = json.loads(f.read())

    return scryfall_card_dict


def flatten(data):
    """
    Flattens database master json file for easier access
    """

    flat_data = dict()

    for color in data:
        for deck_type in data[color]:
            for deck in data[color][deck_type]:
                flat_data[deck] = data[color][deck_type][deck]

    return flat_data


def find_decklist(dataset, target_name):
    """
    Finds desired decklist via direct name matching
    """

    for color in dataset:
        for deck_type in dataset[color]:
            for deck_name in dataset[color][deck_type]:
                if deck_name == target_name:
                    return dataset[color][deck_type][deck_name]
    print("Deck not found!")
    return []


def jaccard_similarity(a, b):
    """
    Computes the size ratio of intersection versus union
    """

    return len(a & b) / len(a | b)


def not_basic_land(card):
    """
    Checks if a given card is not one of the basic lands
    """

    return card not in BASIC_LANDS


def deck_similarity(dataset, deck_1, deck_2):
    """
    Computes similarity between two decks. Ignores basic lands
    """

    raw_decklist_1 = find_decklist(dataset, deck_1)
    raw_decklist_2 = find_decklist(dataset, deck_2)

    decklist_1 = set(list(filter(not_basic_land, raw_decklist_1)))
    decklist_2 = set(list(filter(not_basic_land, raw_decklist_2)))

    return jaccard_similarity(decklist_1, decklist_2)


def deck_rep_by_color(dataset):
    """
    Constructs frequency dictionary of decks on the ddb by color identity
    """

    color_rep = {}

    for color in dataset:
        cur_rep = 0

        for deck_type in dataset[color]:
            for deck in dataset[color][deck_type]:
                cur_rep += 1

        color_rep[color] = cur_rep

    return color_rep


def max_inclusion_value(card, ddb_color_rep, scryfall_card_dict):
    """
    Computes the total number of possible decks which are
    able to include a given card based on color identity
    """

    card_identity = scryfall_card_dict[card]["color_identity"]

    max_inclusion = 0
    is_colorless = not card_identity

    for color_combo in ddb_color_rep:
        if all(c in color_combo.upper() for c in card_identity) or is_colorless:
            max_inclusion += ddb_color_rep[color_combo]

    return max_inclusion


def deck_identity(decklist, scryfall_card_dict):
    """
    Computes color identity of a given deck
    """

    deck_colors = set()

    for card in decklist:
        for color in scryfall_card_dict[card]["color_identity"]:
            deck_colors.add(color)

    return list(deck_colors)


def ci_filter(ci, scryfall_card_dict):
    """
    Returns a function that filters a given card based on provided color identity
    """
    s = scryfall_card_dict

    return lambda x: (not s[x]["color_identity"]) or all(c in ci for c in s[x]["color_identity"])


def decklist_filter(decklist):
    """
    Returns boolean function that check if input card is found
    in a given decklist
    """

    return lambda x: x not in decklist


def summary(dataset, output=False):
    """
    Constructs:
        - frequency dictionary of all cards on ddb
        - number of decks on ddb

    and shows basic card summary
    """

    all_cards = {}
    num_decks = 0

    for color in dataset:
        for deck_type in dataset[color]:
            for deck in dataset[color][deck_type]:
                for card in dataset[color][deck_type][deck]:
                    if card not in all_cards:
                        all_cards[card] = 0
                    all_cards[card] += 1
                num_decks += 1

    for i in range(1, 11):
        cur_representation = 0
        for card in all_cards:
            if all_cards[card] == i:
                cur_representation += 1
        if output:
            print(f"{cur_representation} cards are featured {i} times.")

    return all_cards, num_decks


def dataset_summary(normalized_dataset):
    all_cards = {}
    num_decks = 0

    for deck in normalized_dataset:
        for card in normalized_dataset[deck]:
            if card not in all_cards:
                all_cards[card] = 0
            all_cards[card] += 1
        num_decks += 1

    return all_cards, num_decks


def max_inclusion_ratio(card, all_ddb_cards, ddb_color_rep, scryfall_card_dict):
    """
    Computes the database representation of a given card weighted
    by its maximum possible inclusion
    """

    max_inclusion = max_inclusion_value(card, ddb_color_rep, scryfall_card_dict)

    return all_ddb_cards[card] / max_inclusion


def old_recommend(decklist, deck_color_identity):
    dataset = load_database()
    scryfall_card_dict = load_scryfall()

    flat_dataset = flatten(dataset)
    all_cards, num_decks = summary(dataset)
    ddb_color_rep = deck_rep_by_color(dataset)

    mi_val = lambda x: max_inclusion_value(x, ddb_color_rep, scryfall_card_dict)
    mi_ratio = lambda x: max_inclusion_ratio(x, all_cards, ddb_color_rep, scryfall_card_dict)
    rep_ratio = lambda x: all_cards[x] / num_decks
    combo = lambda x: 0.5 * mi_ratio(x) + 0.5 * rep_ratio(x)

    # Color identity filter
    cif = ci_filter(deck_color_identity, scryfall_card_dict)

    # Card filter
    dif = decklist_filter(decklist)

    # Composite filter
    cf = lambda x: cif(x) and dif(x) and not_basic_land(x)

    output = ""

    output += f"Total number of decks on ddb: {num_decks}\n"
    output += "MI - ratio of decks with card versus all decks in legal color identity\n"
    output += "RP - ratio of decks with card versus all decks on the ddb\n\n"

    for i, card in enumerate(sorted(filter(cf, all_cards.keys()), key=combo, reverse=True)[:50]):
        numbering = f"{i+1}.".ljust(4, " ")
        card_name = f"{card}".ljust(50, " ")

        output += (
            f"{numbering}{card_name}({all_cards[card]}/{mi_val(card)}) "
            f"(MI: {mi_ratio(card):.3f}) "
            f"(RP: {rep_ratio(card):.3f})\n"
        )

    return output


def old_create_dataframe(dataset, all_cards):
    all_cards_x = list(filter(not_basic_land, all_cards.keys()))
    dataset_flat = {}

    for color in dataset:
        for deck_type in dataset[color]:
            for deck in dataset[color][deck_type]:
                dataset_flat[deck] = dataset[color][deck_type][deck]

    deck_names = list(sorted(dataset_flat.keys()))
    all_cards_dict = {card: i for i, card in enumerate(all_cards_x)}
    mat = []

    for i, deck in enumerate(deck_names):
        cur_line = [0] * len(all_cards_x)
        for card in dataset_flat[deck]:
            if not_basic_land(card):
                cur_line[all_cards_dict[card]] = 1
        mat.append(cur_line)

    return pd.DataFrame(
        data=np.array(mat),
        index=deck_names,
        columns=all_cards_x
    )


def create_dataframe(flat_dataset, all_cards):
    all_cards_x = list(filter(not_basic_land, all_cards))
    deck_names = list(sorted(flat_dataset))
    all_cards_dict = {card: i for i, card in enumerate(all_cards_x)}
    data = []

    for i, deck in enumerate(deck_names):
        cur_line = [0] * len(all_cards_x)
        for card in flat_dataset[deck]:
            if not_basic_land(card):
                cur_line[all_cards_dict[card]] = 1
        data.append(cur_line)

    return pd.DataFrame(data=np.array(data), index=deck_names, columns=all_cards_x)


def similarity(df, decklist_vec, b, output=False):
    v = df.loc[b].values

    result = sum(decklist_vec & v) / sum(decklist_vec | v)

    if output:
        print(f"Comparing deck to {b}")
        print(f"{sum(decklist_vec & v)} card(s) in common")
        print(f"Jaccard similarity: {result}")

    return result


def deck2vec(df, decklist):

    return pd.Series([1 if card in decklist else 0 for card in df.columns])


def cards_in_common_ratio(decklist_1, decklist_2):

    return len([a for a in decklist_1 if a in decklist_2]) / 100


def deck_similarities(decklist, deck_color_identity):
    dataset = load_database()
    scryfall_card_dict = load_scryfall()
    flat_dataset = flatten(dataset)
    all_cards, num_decks = summary(dataset)
    ddb_color_rep = deck_rep_by_color(dataset)
    df = create_dataframe(dataset, all_cards)
    decklist_vec = deck2vec(df, decklist)

    for deck in sorted(flat_dataset, key=lambda x: similarity(df, decklist_vec, x), reverse=True)[:50]:
        print(f"Value: {similarity(df, decklist_vec, deck):.3f}, "
              f"{cards_in_common(decklist, flat_dataset[deck])}, {deck}")


def recommend(decklist, deck_color_identity, excludelist):
    scryfall_card_dict = load_lite()
    flat_dataset = load_normalized()
    all_cards, num_decks = dataset_summary(flat_dataset)

    # TODO:
    # ADD DDB_COLOR_REP TO MASTER JSON SO LOADING DATASET IS NOT NEEDED
    dataset = load_database()
    ddb_color_rep = deck_rep_by_color(dataset)

    df = create_dataframe(flat_dataset, all_cards)
    decklist_vec = deck2vec(df, decklist)

    master_dict = {}

    for deck in flat_dataset:
        cur_filtered = filter(lambda x: x not in decklist, flat_dataset[deck])
        cur_score = similarity(df, decklist_vec, deck)

        for card in cur_filtered:
            if card not in master_dict:
                master_dict[card] = []

            master_dict[card].append(cur_score)

    measure = lambda x: np.power(np.prod(master_dict[x]), 1/len(master_dict[x]))

    mi_val = lambda x: max_inclusion_value(x, ddb_color_rep, scryfall_card_dict)
    mi_ratio = lambda x: max_inclusion_ratio(x, all_cards, ddb_color_rep, scryfall_card_dict)
    rep_ratio = lambda x: all_cards[x] / num_decks

    composite = lambda x: (0.5 * mi_ratio(x) + 0.5 * rep_ratio(x))

    cif = ci_filter(deck_color_identity, scryfall_card_dict)
    lf = lambda x: "Land" not in scryfall_card_dict[x]["type_line"]
    ef = lambda x: x not in excludelist
    cf = lambda x: cif(x) and lf(x) and ef(x)

    shortlist = sorted(filter(cf, master_dict), key=composite, reverse=True)[:20]
    output = ""

    for i, card in enumerate(sorted(shortlist, key=measure, reverse=True)):
        numbering = f"{i+1}.".ljust(4, " ")
        card_name = f"{scryfall_card_dict[card]['full_name']}".ljust(40, " ")

        output += (
            f"{numbering}{card_name}({all_cards[card]}/{mi_val(card)}) "
            f"(DS: {measure(card):.3f})\n"
        )

    return output


def arithmetic_generality(deck, all_cards, num_decks):
    if not deck:
        return 0

    a = [all_cards[card] / num_decks for card in filter(not_basic_land, deck)]
    return sum(a) / len(a)


def geometric_generality(deck, all_cards, num_decks):
    if not deck:
        return 0

    a = [all_cards[card] / num_decks for card in filter(not_basic_land, deck)]
    return np.power(np.prod(a), 1/len(a))


def decklist_generality_ranking(generality_measure):
    for deck in sorted(flat_dataset.keys(), key=generality_measure, reverse=True)[:10]:
        print(f"{generality_measure(deck):.3f}, {deck}")


def generality_info(deck):
    dataset = load_database()
    flat_dataset = flatten(dataset)
    all_cards, num_decks = summary(dataset)
    measure = lambda x: arithmetic_generality(x, all_cards, num_decks)
    generality_list = [
        [name, measure(flat_dataset[name]), "blue"] for name in flat_dataset
    ]
    generality_list.append(["Your Deck", measure(deck), "red"])

    return list(sorted(generality_list, key=lambda x: x[1]))


if __name__ == "__main__":

    # Json data pulled from deckbox used for testing
    test_deck = []
    with open("test_deck.json", "r") as f:
        data = json.loads(f.read())
        for i, x in enumerate(data):
            test_deck.append(data[x]["name"])

    #print(old_recommend(test_deck, deck_identity(test_deck, load_scryfall())))
    #deck_similarities(test_deck, ["W", "U", "B", "G"])
    #print(recommend(test_deck, ["W", "U", "B", "G"]))

    """
    ddb_filter = lambda x: not_basic_land(x) and (all_cards[x] / num_decks >= 0.1)

    dataset = load_database()
    all_cards, num_decks = summary(dataset)
    for i, card in enumerate(sorted(
        filter(ddb_filter, all_cards.keys()),
        key=lambda x: all_cards[x],
        reverse=True
    )):
        print(f"{i+1}. {card} ({all_cards[card]})")
    """

    dataset = load_database()
    flat_dataset = flatten(load_database())
    all_cards, num_decks = summary(dataset)

    measure = lambda x: arithmetic_generality(flat_dataset[x], all_cards, num_decks)
    decklist_generality_ranking(measure)

    print()

    measure_2 = lambda x: geometric_generality(flat_dataset[x], all_cards, num_decks)
    decklist_generality_ranking(measure_2)

    print()

    print(arithmetic_generality(["Mana Crypt"], all_cards, num_decks))
    print(geometric_generality(["Mana Crypt"], all_cards, num_decks))
