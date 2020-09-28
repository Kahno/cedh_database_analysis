import re
import json

import pandas as pd
import numpy as np

from sklearn.cluster import DBSCAN


MASTER_JSON_FILE = "json_data/cedh_decklists.json"
NORM_MASTER_JSON_FILE = "json_data/normalized_decklists.json"

SCRYFALL_DICTIONARY = "json_data/scryfall_card_dictionary.json"
LITE_SCRYFALL_DICT = "json_data/lite_scryfall_dict.json"

BASIC_LANDS = [
    "plains",
    "island",
    "swamp",
    "mountain",
    "forest",

    "snow covered plains",
    "snow covered island",
    "snow covered swamp",
    "snow covered mountain",
    "snow covered forest"
]


def load_database():
    """
    Loads ddb from json file
    """

    with open(MASTER_JSON_FILE, "r") as f:
        data = json.loads(f.read())

    return data


def load_normalized():
    """
    Loads flat ddb with normalized names from json file
    """

    with open(NORM_MASTER_JSON_FILE, "r") as f:
        data = json.loads(f.read())

    return data


def load_lite(filename=LITE_SCRYFALL_DICT):
    """
    Loads lightweight scryfall data from json file
    """

    with open(filename, "r") as f:
        data = json.loads(f.read())

    return data


def load_scryfall(filename=SCRYFALL_DICTIONARY):
    """
    Loads scryfall data from json file
    """

    with open(filename, "r") as f:
        scryfall_dict = json.loads(f.read())

    return scryfall_dict


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


def normalize(card_name):
    """
    Transforms card name into lower case without special characters
    """

    card_name = card_name.lower().replace("-", " ")

    card_name = re.sub(r"[\!\'\"\(\)\&\,\.\/\:\?\_\®]", "", card_name)
    card_name = re.sub(r"[àáâ]", "a", card_name)
    card_name = re.sub(r"[é]", "e", card_name)
    card_name = re.sub(r"[í]", "i", card_name)
    card_name = re.sub(r"[ö]", "o", card_name)
    card_name = re.sub(r"[úû]", "u", card_name)

    return card_name


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

    return normalize(card) not in BASIC_LANDS


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


def max_inclusion_value(card, ddb_color_rep, scryfall_dict):
    """
    Computes the total number of possible decks which are
    able to include a given card based on color identity
    """

    card_identity = scryfall_dict[card]["color_identity"]

    max_inclusion = 0
    colorless = not card_identity

    for color_combo in ddb_color_rep:
        if all(c in color_combo.upper() for c in card_identity) or colorless:
            max_inclusion += ddb_color_rep[color_combo]

    return max_inclusion


def deck_identity(decklist, scryfall_dict):
    """
    Computes color identity of a given deck
    """

    deck_colors = set()

    for card in decklist:
        for color in scryfall_dict[card]["color_identity"]:
            deck_colors.add(color)

    return list(deck_colors)


def ci_filter(ci, scryfall_dict):
    """
    Returns a function that filters a given card based on
    provided color identity
    """

    def sc(x): return scryfall_dict[x]["color_identity"]

    return lambda x: not sc(x) or all(c in ci for c in sc(x))


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
    """
    Constructs:
        - frequency dictionary of all cards on ddb
        - number of decks on ddb
    """

    all_cards = {}
    num_decks = 0

    for deck in normalized_dataset:
        for card in normalized_dataset[deck]:
            if card not in all_cards:
                all_cards[card] = 0
            all_cards[card] += 1
        num_decks += 1

    return all_cards, num_decks


def max_inc_ratio(card, ddb_cards, ddb_color_rep, scryfall_dict):
    """
    Computes the database representation of a given card weighted
    by its maximum possible inclusion
    """

    max_inclusion = max_inclusion_value(card, ddb_color_rep, scryfall_dict)

    return ddb_cards[card] / max_inclusion


def old_recommend(decklist, deck_color_identity):
    """
    Recommends cards for a given decklist based on ddb data - DEPRECATED
    """

    dataset = load_database()
    s = load_scryfall()
    all_cards, num_decks = summary(dataset)
    ddb_color_rep = deck_rep_by_color(dataset)

    def mi_val(x): return max_inclusion_value(x, ddb_color_rep, s)
    def mi_ratio(x): return max_inc_ratio(x, all_cards, ddb_color_rep, s)
    def rep_ratio(x): return all_cards[x] / num_decks
    def combo(x): return 0.5 * mi_ratio(x) + 0.5 * rep_ratio(x)

    # Color identity filter
    cif = ci_filter(deck_color_identity, s)

    # Card filter
    dif = decklist_filter(decklist)

    # Composite filter
    def cf(x): return cif(x) and dif(x) and not_basic_land(x)

    output = ""

    output += f"Total number of decks on ddb: {num_decks}\n"
    output += ("MI - ratio of decks with card versus "
               "all decks in legal color identity\n")
    output += ("RP - ratio of decks with card versus "
               "all decks on the ddb\n\n")

    for i, card in enumerate(sorted(
        filter(cf, all_cards.keys()),
        key=combo,
        reverse=True
    )[:50]):
        numbering = f"{i+1}.".ljust(4, " ")
        card_name = f"{card}".ljust(50, " ")

        output += (
            f"{numbering}{card_name}({all_cards[card]}/{mi_val(card)}) "
            f"(MI: {mi_ratio(card):.3f}) "
            f"(RP: {rep_ratio(card):.3f})\n"
        )

    return output


def old_create_dataframe(dataset, all_cards):
    """
    Creates dataframe snapshot of ddb - DEPRECATED
    """

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
    """
    Creates dataframe snapshot of ddb
    """

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

    return pd.DataFrame(
        data=np.array(data),
        index=deck_names,
        columns=all_cards_x
    )


def df_similarity(df, a, b):
    v = df.loc[a].values
    w = df.loc[b].values

    return sum(v & w) / sum(v | w)


def similarity(df, decklist_vec, b, output=False):
    """
    Computes similarity between given decklist and given ddb deck
    """

    v = df.loc[b].values

    result = sum(decklist_vec & v) / sum(decklist_vec | v)

    if output:
        print(f"Comparing deck to {b}")
        print(f"{sum(decklist_vec & v)} card(s) in common")
        print(f"Jaccard similarity: {result}")

    return result


def deck2vec(df, decklist):
    """
    Transforms given decklist to vector form based on ddb
    """

    return pd.Series([1 if card in decklist else 0 for card in df.columns])


def cards_in_common_ratio(decklist_1, decklist_2):
    """
    Returns the size of the intersection of two given decklists
    """

    return len([a for a in decklist_1 if a in decklist_2]) / 100


def deck_similarities(decklist, deck_color_identity):
    """
    Displays top 50 ddb decks based on similarity to given decklist
    """

    dataset = load_database()
    flat_dataset = flatten(dataset)
    all_cards, num_decks = summary(dataset)
    df = create_dataframe(dataset, all_cards)
    decklist_vec = deck2vec(df, decklist)

    for deck in sorted(
        dataset,
        key=lambda x: similarity(df, decklist_vec, x),
        reverse=True
    )[:50]:
        print(f"Value: {similarity(df, decklist_vec, deck):.3f}, "
              f"{cards_in_common_ratio(decklist, flat_dataset[deck])}, {deck}")


def recommend(decklist, deck_color_identity, excludelist, land_mode=False):
    """
    Recommends cards for a given decklist based on ddb data
    """

    s = load_lite()
    flat_dataset = load_normalized()
    all_cards, num_decks = dataset_summary(flat_dataset)

    # TODO:
    # ADD DDB_COLOR_REP TO MASTER JSON SO LOADING DATASET IS NOT NEEDED
    dataset = load_database()
    ddb_color_rep = deck_rep_by_color(dataset)

    df = create_dataframe(flat_dataset, all_cards)
    decklist_vec = deck2vec(df, decklist)

    master = {}
    for deck in flat_dataset:
        cur_filtered = filter(lambda x: x not in decklist, flat_dataset[deck])
        cur_score = similarity(df, decklist_vec, deck)

        for card in cur_filtered:
            if card not in master:
                master[card] = []

            master[card].append(cur_score)

    def measure(x): return np.power(np.prod(master[x]), 1 / len(master[x]))
    def mi_val(x): return max_inclusion_value(x, ddb_color_rep, s)
    def mi_ratio(x): return max_inc_ratio(x, all_cards, ddb_color_rep, s)
    def rep_ratio(x): return all_cards[x] / num_decks
    def composite(x): return (0.5 * mi_ratio(x) + 0.5 * rep_ratio(x))

    cif = ci_filter(deck_color_identity, s)
    def lf(x): return "Land" in s[x]["type_line"]
    def ef(x): return x not in excludelist

    def cf(x):
        if land_mode:
            return cif(x) and ef(x) and lf(x) and not_basic_land(x)
        return cif(x) and ef(x) and (not lf(x))

    shortlist = sorted(filter(cf, master), key=composite, reverse=True)[:20]
    output = ""

    for i, card in enumerate(sorted(shortlist, key=measure, reverse=True)):
        numbering = f"{i+1}.".ljust(4, " ")
        card_name = f"{s[card]['full_name']}".ljust(40, " ")

        output += (
            f"{numbering}{card_name}({all_cards[card]}/{mi_val(card)}) "
            f"(DS: {measure(card):.3f})\n"
        )

    return output


def compare(decklist, deck_color_identity):
    flat_dataset = load_normalized()
    all_cards, num_decks = dataset_summary(flat_dataset)
    df = create_dataframe(flat_dataset, all_cards)
    decklist_vec = deck2vec(df, decklist)

    master = {}
    for deck in flat_dataset:
        cur_filtered = filter(lambda x: x in decklist, flat_dataset[deck])
        cur_score = similarity(df, decklist_vec, deck)

        for card in cur_filtered:
            if card not in master:
                master[card] = []

            master[card].append(cur_score)

    def measure(x):
        if x not in master:
            return 0
        return np.power(np.prod(master[x]), 1 / len(master[x]))

    output = ""

    for i, card in enumerate(sorted(decklist, key=measure)):
        numbering = f"{i+1}.".ljust(4, " ")
        card_name = f"{decklist[card]}".ljust(40, " ")

        output += (
            f"{numbering}{card_name} "
            f"(DS: {measure(card):.3f})\n"
        )

    return output


def arithmetic_generality(deck, all_cards, num_decks):
    """
    Computes generality score by calculating arithmetic average of scores
    """

    if not deck:
        return 0

    def ddb_num(card):
        if card not in all_cards:
            return 0
        return all_cards[card] / num_decks

    a = [ddb_num(card) for card in filter(not_basic_land, deck)]
    return sum(a) / len(a)


def geometric_generality(deck, all_cards, num_decks):
    """
    Computes generality score by calculating geometric average of scores
    """

    if not deck:
        return 0

    def ddb_num(card):
        if card not in all_cards:
            return 0
        return all_cards[card] / num_decks

    a = [ddb_num(card) for card in filter(not_basic_land, deck)]
    return np.power(np.prod(a), 1/len(a))


def decklist_generality_ranking(dataset, measure):
    """
    Displays top 10 ddb decks based on generality
    """

    for deck in sorted(dataset, key=measure, reverse=True)[:10]:
        print(f"{measure(deck):.3f}, {deck}")


def generality_info(deck):
    """
    Computes generality scores of all ddb decks and given decklist
    """

    dataset = load_database()
    flat_dataset = flatten(dataset)
    all_cards, num_decks = summary(dataset)
    def measure(x): return arithmetic_generality(x, all_cards, num_decks)
    generality_list = [
        [name, measure(flat_dataset[name]), "blue"] for name in flat_dataset
    ]
    generality_list.append(["Your Deck", measure(deck), "red"])

    return list(sorted(generality_list, key=lambda x: x[1]))


if __name__ == "__main__":

    """
    data = load_normalized()
    all_cards, num_decks = dataset_summary(data)
    df = create_dataframe(data, all_cards)

    def jdist(a, b): return 1 - sum(a & b) / sum(a | b)

    result = []

    for deck1 in df.index:
        cur_dists = []
        for deck2 in df.index:
            cur_dists.append(jdist(df.loc[deck1], df.loc[deck2]))
        result.append(cur_dists)

    print(result)

    clustering = DBSCAN(eps=0.5, min_samples=3, metric="precomputed").fit(
        np.array(result))
    cluster_results = {}

    for i, label in enumerate(clustering.labels_):
        if str(label) not in cluster_results:
            cluster_results[str(label)] = []

        cluster_results[str(label)].append(df.index[i])

    for label in cluster_results:
        print(label)

        for deck in cluster_results[label]:
            print(f"\t{deck}")
    """

    data = load_normalized()
    all_cards, num_decks = dataset_summary(data)
    df = create_dataframe(data, all_cards)
    scry = load_lite()

    cif = ci_filter(["U", "R"], scry)

    for card in sorted(
        filter(
            lambda x: (
                cif(x) and
                not_basic_land(x) and
                "Land" in scry[x]["type_line"]
            ),
            all_cards
        ),
        key=lambda x: all_cards[x]
    ):
        print(card, all_cards[card])
