import json


MASTER_JSON_FILE = "cedh_decklists.json"

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
    with open(MASTER_JSON_FILE, "r") as f:
        data = json.loads(f.read())

    return data


def find_decklist(dataset, target_name):
    for color in dataset:
        for deck_type in dataset[color]:
            for deck_name in dataset[color][deck_type]:
                if deck_name == target_name:
                    return dataset[color][deck_type][deck_name]


def jaccard_similarity(a, b):
    """
    Computes the size ratio of intersection versus union
    """

    return len(a & b) / len(a | b)


def not_basic_land(card):
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


def summary(dataset):
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

    for card in sorted(filter(not_basic_land, all_cards.keys()), key=lambda x: all_cards[x]):
        print(f"{all_cards[card] / num_decks:.4f} ({all_cards[card]}/{num_decks}) {card}")

    print(f"\nTotal number of unique cards on database is {len(all_cards.keys())}\n")

    for i in range(1, 11):
        cur_representation = 0
        for card in all_cards:
            if all_cards[card] == i:
                cur_representation += 1
        print(f"{cur_representation} cards are featured {i} times.")

    return all_cards, num_decks


if __name__ == "__main__":
    dataset = load_database()

    summary(dataset)
