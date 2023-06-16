import argparse
import datetime

from pydantic import Json
from scraper import *
import json
import requests
from enum import Enum
from datetime import datetime, date
import urllib.parse

from scraper import parse_decklist_platform

from tqdm import tqdm

import atexit


base_url = "https://edhtop16.com/api/"
headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

MOXFIELD_RATE_LIMIT = 0 # [s]

DEFAULT_QUERY = {
    'standing': {'$lte': 16},
    'colorID': 'WUBRG',
    'tourney_filter': {
        'size': {'$gte': 64}
    }
}

PARSER_CACHE = {}

PARSER_CACHE_FILE = 'parser_cache.json'

try:
    with open(PARSER_CACHE_FILE, 'r') as f:
        PARSER_CACHE = json.load(f)
        print('Loaded {} decks from cache'.format(len(PARSER_CACHE)))
except:
    pass

atexit.register(lambda: json.dump(PARSER_CACHE, open(PARSER_CACHE_FILE, 'w')))

# Custom validation function for color combinations
def validate_color_combination(colors):
    valid_colors = ['W', 'U', 'B', 'R', 'G', 'C']
    if 'C' in colors and len(colors) > 1:
        raise argparse.ArgumentTypeError("Colorless (C) cannot be combined with other colors")

    for color in colors:
        if color not in valid_colors:
            raise argparse.ArgumentTypeError(f"Invalid color: {color}")
    return ''.join(colors)

class JSONObject:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, dict):
                value = JSONObject(**value)
            self.__dict__[key] = value

    @property
    def json(self):
        return {
            k:v if not isinstance(v, JSONObject) else v.json
            for k,v in self.__dict__.items()
        }

    @property
    def query_json(self):
        return json.loads(json.dumps(self.json).replace('gte', '$gte').replace('lte', '$lte'))

    def __repr__(self):
        '''return '\n'.join(
            '{}:{}'.format(
                str(k), str(v) if not isinstance(v, JSONObject) else repr(v).replace('\n', '\n\t')
            )
            for k,v in self.__dict__.items()
        )'''
        x = self.json
        return json.dumps(x, indent=4)

def str2timestamp(s:str) -> int:
    '''
    Converts a string of the form DDMMYYYY to a unix timestamp
    '''
    return int(datetime.strptime(s, '%d%m%Y').timestamp())

def generate_query(args):
    data = {}
    if args.tstanding is not None:
        data['standing'] = {}
        if args.tstanding.lte is not None:
            data['standing']['lte'] = args.tstanding.lte
        if args.tstanding.gte is not None:
            data['standing']['gte'] = args.tstanding.gte

    if args.tsize is not None or args.tdate is not None:
        data['tourney_filter'] = {}
        if args.tsize is not None:
            data['tourney_filter']['size'] = {}
            if args.tsize.lte is not None:
                data['tourney_filter']['size']['lte'] = args.tsize.lte
            if args.tsize.gte is not None:
                data['tourney_filter']['size']['gte'] = args.tsize.gte
        if args.tdate is not None:
            data['tourney_filter']['dateCreated'] = {}
            if args.tdate.lte is not None:
                data['tourney_filter']['dateCreated']['lte'] = args.tdate.lte
            if args.tdate.gte is not None:
                data['tourney_filter']['dateCreated']['gte'] = args.tdate.gte
    if args.tentries is not None:
        data['entries'] = {}
        if args.tentries.lte is not None:
            data['entries']['lte'] = args.tentries.lte
        if args.tentries.gte is not None:
            data['entries']['gte'] = args.tentries.gte
    if args.color is not None:
        data['colorID'] = args.color
    #else:
    #    data['colorID'] = 'null'
    return JSONObject(**data)

def get_entries(query):
    data = json.loads(requests.post(base_url + 'req', json=query.query_json, headers=headers).text)
    data = [entry for entry in data]
    entries = {}

    for entry in data:
        if entry['commander'] not in entries.keys():
            entries[entry['commander']] = {
                'entries': [],
                'decklists': set(),
                'color': entry['colorID'],
                'deck_type': entry['commander'],
            }

        entries[entry['commander']]['entries'].append(entry)
        entries[entry['commander']]['decklists'].add(entry['decklist'])


    if hasattr(data, 'entries'):
        del_keys = set()
        lte = hasattr(query.entries, 'lte')
        gte = hasattr(query.entries, 'gte')
        if lte or gte:
            for key, val in entries.items():
                if lte and len(val['entries']) > query.entries.lte:
                    del_keys.add(key)
                if gte and len(val['entries']) < query.entries.gte:
                    del_keys.add(key)
        for key in del_keys:
            del entries[key]

    for entry in entries:
        entries[entry]['decklists'] = list(entries[entry]['decklists'])

    return JSONObject(**entries)

def build_master_json(data):
    master_json = {}
    for commander, commander_data in data.__dict__.items():
        if commander_data.color not in master_json.keys():
            master_json[commander_data.color] = {}
        if commander not in master_json[commander_data.color].keys():
            master_json[commander_data.color][commander] = {}
        for entry in commander_data.entries:
            entry_name = '{}|{}'.format(entry['name'], entry['tournamentName'])
            master_json[commander_data.color][commander][entry_name] = entry['decklist']

    return master_json

def parse_decklists(master_json):
    pbar_1 = tqdm(master_json.items(), desc='Color', leave=False)
    for color, commanders in pbar_1:
        pbar_1.set_description('{}'.format(color))
        pbar_2 = tqdm(commanders.items(), desc='Commander', leave=False)
        for commander, entries in pbar_2:
            pbar_2.set_description('{}'.format(commander))
            pbar_3 = tqdm(entries.items(), desc='Entry', leave=False)
            for entry, url in pbar_3:
                pbar_3.set_description('{}'.format(entry))
                try:
                    decklist = None
                    if url in PARSER_CACHE.keys():
                        decklist = PARSER_CACHE[url]['decklist']
                    if decklist is None:
                        decklist = parse_decklist_platform(url, wait_time=1)
                        PARSER_CACHE[url] = {
                            'decklist': decklist,
                            'time': time.time()
                        }

                    master_json[color][commander][entry] = decklist
                except Exception as e:
                    #clear TQDM buffer
                    #print('\r{} parsing decklist: {}'.format(e, url), flush=True)
                    PARSER_CACHE[url] = {
                        'decklist': None,
                        'time': time.time()
                    }
    return master_json

def decode_url_query(url):
    '''
    Decodes a url query into a dict
    '''

    URL  = urllib.parse.unquote(url)

    query = {}
    for key, value in urllib.parse.parse_qs(URL.split("?")[1]).items():
        key = key.split("__")
        if len(key) == 1:
            try:
                query[key[0]] = int(value[0])
            except ValueError:
                query[key[0]] = value[0]
        elif len(key) == 2:
            if key[0] not in query:
                query[key[0]] = {}
            try:
                query[key[0]][key[1]] = int(value[0])
            except ValueError:
                query[key[0]][key[1]] = value[0]
        elif len(key) == 3:
            if key[0] not in query:
                query[key[0]] = {}
            if key[1] not in query[key[0]]:
                query[key[0]][key[1]] = {}
            #TODO: Correct types
            try:
                query[key[0]][key[1]][key[2]] = int(value[0])
            except ValueError:
                query[key[0]][key[1]][key[2]] = value[0]


    return JSONObject(**query)


'''
tourney_filter: {
    size:{[$lte | $gte | $eq] : <N>}
    dateCreated: {$lte | $gte | $eq]= <unix_timestamp>}
}
entries : {[$lte | $gte | $eq] : <N>}
standing = {[$lte | $gte | $eq] : <N>}
colorID = [(W | U | B | R | G) ^ C]
'''

#data = JSONObject(**DEFAULT_QUERY)

#assert 1672527600 == str2timestamp('01012023')
#assert str2timestamp('02012023') - str2timestamp('01012023') == 24*60*60
#assert data.json == DEFAULT_QUERY

#entries = json.loads(requests.post(base_url + 'req', json=data.json, headers=headers).text)
#print(entries)

if __name__ == '__main__':
    #parser
    parser = argparse.ArgumentParser(description='EDH Top 16 Parser')

    # Define the "size" and "date" argument pairs
    parser.add_argument('--size', dest='tsize', nargs='+', help='Size filter (optional: +gte/+lte followed by a number)')
    parser.add_argument('--date', dest='tdate', nargs='+', help='Date filter (optional: +gte/+lte followed by a date)')
    parser.add_argument('--standing', dest='tstanding', nargs='+', help='Standing filter (optional: +gte/+lte followed by a number)')
    parser.add_argument('--entries', dest='tentries', nargs='+', help='Entries filter (optional: +gte/+lte followed by a number)')
    # Define the '--color' argument with custom validation
    parser.add_argument('--color', type=validate_color_combination,
                        help='MTG color(s) (W - White, U - Blue, B - Black, R - Red, G - Green, C - Colorless)')

    parser.add_argument('--output', type=str, default='top16.json',
                        help='Output file name (default: top16.json)')



    # Parse the command-line arguments
    args = parser.parse_args()

    dtypes = {
        'tsize': int,
        'tdate': str2timestamp,
        'tstanding': int,
        'tentries': int,
    }
    for arg in vars(args):
        if arg in dtypes:
            opt_args = getattr(args, arg)
            if opt_args is not None:
                option_parser = argparse.ArgumentParser(prefix_chars='+')
                dtype = dtypes[arg]

                option_parser.add_argument('+lte', type=dtype, help='Maximum tournament size')
                option_parser.add_argument('+gte', type=dtype, help='Minimum tournament size')
                opt_args = option_parser.parse_args(getattr(args, arg))

                setattr(args, arg, opt_args)
    #url = "https://edhtop16.com/?tourney_filter__size__%24gte=64&tourney_filter__dateCreated__%24gte=1672527600&standing__%24lte=16&entries__%24gte=10"
    #query = decode_url_query(url)
    #entries = get_entries(query)
    #print(query)
    #print(entries)


    query = generate_query(args)
    data = get_entries(query)

    #print(query)
    #print(entries)
    master_json = build_master_json(data)
    parse_decklists(master_json)

    with open(args.output, 'w') as f:
        json.dump(master_json, f) #, indent=4 )
    pass

