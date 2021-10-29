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
    Returns boolean function that checks if input card is found
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
        return cif(x) and ef(x) and (not lf(x)) #and (
            #"Creature" not in s[x]["type_line"] and s[x]["cmc"] <= 4
        #)

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

    for deck in sorted(dataset, key=measure, reverse=True)[:20]:
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


def generate_aggregate(any_base_cards):
    data = load_normalized()
    scry = load_lite()

    aggregated_deck = dict()
    num_decks = 0

    for deck in data:
        if any(c in data[deck] for c in any_base_cards):
            num_decks += 1
            for card in data[deck]:
                if card in BASIC_LANDS:
                    continue
                if card not in aggregated_deck:
                    aggregated_deck[card] = 0

                aggregated_deck[card] += 1

    for x in sorted([c for c in aggregated_deck], key=lambda x: aggregated_deck[x]):
        if scry[x]["type_line"] == "Land":
            continue
        print(f"{aggregated_deck[x]}/{num_decks}", x)


def synergy_increase(base_card):
    data = load_normalized()
    scry = load_lite() 
    all_cards, _ = dataset_summary(data)
    dcr = deck_rep_by_color(load_database())
    decks = data.values()

    def syn_inc(x):
        one = num_decks_with_card(x, decks)
        if not one: return 0

        two = max_inclusion_value(x, dcr, scry)
        three = num_decks_with_cards(x, base_card, decks)
        four = miv_dual(x, base_card, dcr, scry)

        return two * (three/four - one/two) / one

    for card in sorted(
        filter(
            lambda x: (all([
                "Land" not in scry[x]["type_line"],
                syn_inc(x) > 0,
                num_decks_with_card(x) > 1,  # Hack
            ])),
            all_cards
        ),
        key=syn_inc
    ):
        print(f"+{round(syn_inc(card), 3)}\t{card}")


def db_ci_info(data=None):
    if not data:
        data = load_database()
    deck_ci = dict()
    for color in data:
        for deck_type in data[color]:
            for deck in data[color][deck_type]:
                deck_ci[deck] = set([x.upper() for x in color])
    return deck_ci


def nonland_synergy(x):
    data = load_normalized()
    database = load_database()

    scry = load_lite() 
    all_cards, _ = dataset_summary(data)
    dcr = deck_rep_by_color(database)
    deck_ci = db_ci_info(database)

    decks_with_base_card = []
    for deck in data:
        if x in data[deck]:
            decks_with_base_card.append(deck)

    datavals = data.values()
    result = []
    for y in all_cards:
        if "Land" in scry[y]["type_line"]:
            continue
        yci = set(scry[y]["color_identity"])

        # decks with y
        a = num_decks_with_card(y, datavals)
        
        # decks with y ci
        b = max_inclusion_value(y, dcr, scry)

        # decks with base_card and y
        c = sum(y in data[deck] for deck in decks_with_base_card) 

        # decks with base_card and y ci
        d = sum(yci.issubset(deck_ci[deck]) for deck in decks_with_base_card)

        if c == 0:
            increase = 0
        else:
            increase = (c/d - a/b) / (a/b)

        #print(f"{a}/{b}\t{c}/{d}\t{round(increase, 4)}\t{y}")
        result.append([increase, y])

    for increase, card in sorted(result, key=lambda x: x[0], reverse=True):
        print(round(increase, 4), card)


def miv_dual(x, y, dcr, scry):
    ci = list(set(scry[x]["color_identity"]) | set(scry[y]["color_identity"]))
    colorless = not ci
    max_inclusion = 0

    for color_combo in dcr:
        if all(c in color_combo.upper() for c in ci) or colorless:
            max_inclusion += dcr[color_combo]

    return max_inclusion


def num_decks_with_card(x, decks=None):
    if not decks:
        decks = load_normalized().values()
    return sum(x in deck for deck in decks)


def num_decks_with_cards(x, y, decks=None):
    if not decks:
        decks = load_normalized().values()
    return sum((x in deck) and (y in deck) for deck in decks)


def create_core(colors, ratio=0.75):
    colors = [x.lower() for x in colors]
    color_code = "".join([x for x in "wubrg" if x in colors])
    data_complex = load_database()
    
    aggregate = dict()
    num_decks = 0

    for c in data_complex:
        if c == color_code:
            for d in data_complex[c]:
                for deck in data_complex[c][d]:
                    num_decks += 1
                    for card in data_complex[c][d][deck]:
                        if normalize(card) in BASIC_LANDS:
                            continue

                        if card not in aggregate:
                            aggregate[card] = 0

                        aggregate[card] += 1

    core = [c for c in aggregate if aggregate[c] >= ratio * num_decks]

    return "\n".join([f"1 {c}" for c in sorted(core, key=lambda x: aggregate[x], reverse=True)])


if __name__ == "__main__":

    data = load_normalized()
    all_cards, num_decks = dataset_summary(data)
    df = create_dataframe(data, all_cards)
    scry = load_lite()

    ##################################
    data_complex = load_database()
    ddb_color_rep = deck_rep_by_color(data_complex)
    ##################################

    cif = ci_filter(["B",], scry)

    def miv(x): return max_inclusion_value(x, ddb_color_rep, scry)

    """"""
    for card in sorted(
        filter(
            lambda x: (
                all([
                    "Land" not in scry[x]["type_line"],
                    "Artifact" not in scry[x]["type_line"],
                    cif(x),
                    #not_basic_land(x),
                    #len(scry[x]["color_identity"]) > 1,
                ])
            ),
            all_cards
        ),
        key=lambda x: all_cards[x]# / miv(x)
    ):

        #print(f"({all_cards[card]} / {num_decks}) {card}")

        #val = round(100 * all_cards[card] / miv(card), 2)
        #print(f"{val} %\t ({all_cards[card]} / {miv(card)}) {card}")
        print(f"({all_cards[card]} / {num_decks}) {card}")
    """"""
    ##############################################
    """
    Check for decks that don't play a specific card.
    """
    #print()
    #not_played_card = "mox diamond"
    #for deck in data:
    #    if not_played_card not in data[deck]:
    #        print(deck)
    ###############################################

    #generate_aggregate(["protean hulk", ])
    #generate_aggregate(["underworld breach", ])
    #generate_aggregate(["underworld breach", "brain freeze"])

    #print()
    #def measure(x): return arithmetic_generality(data[x], all_cards, num_decks)
    #decklist_generality_ranking(data, measure)

    #synergy_increase("pattern of rebirth")

    """
    x = "protean hulk"
    base_card = "pattern of rebirth"
    dcr = deck_rep_by_color(load_database())

    one = num_decks_with_card(x)
    two = max_inclusion_value(x, dcr, scry)
    three = num_decks_with_cards(x, base_card)
    four = miv_dual(x, base_card, dcr, scry)

    print(f"({one}/{two})\t({three}/{four})")
    """

    #nonland_synergy("underworld breach")

    print()
    #create_core(["R", "U", "g"])
    bla = create_core(["W", "U", "B", "R", "G"], ratio=0.8)
    #bla = create_core(["W", "U", "B", "R"], ratio=0.41)

    print(bla)