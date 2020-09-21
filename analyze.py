import json


MASTER_JSON_FILE = "cedh_decklists.json"
SCRYFALL_CARD_DICTIONARY = "scryfall_card_dictionary.json"

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


def max_inclusion_ratio(card, all_ddb_cards, ddb_color_rep, scryfall_card_dict):
    """
    Computes the database representation of a given card weighted
    by its maximum possible inclusion
    """

    max_inclusion = max_inclusion_value(card, ddb_color_rep, scryfall_card_dict)

    return all_ddb_cards[card] / max_inclusion


def recommend(decklist, deck_color_identity):
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


if __name__ == "__main__":

    # Json data pulled from deckbox used for testing
    test_deck = []
    with open("test_deck.json", "r") as f:
        data = json.loads(f.read())
        for i, x in enumerate(data):
            test_deck.append(data[x]["name"])

    print(recommend(test_deck, deck_identity(test_deck, load_scryfall())))
