import argparse
import datetime

from pydantic import Json
from scraper import *
import json
import requests
from enum import Enum
from datetime import datetime, date
import urllib.parse


base_url = "https://edhtop16.com/api/"
headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

# Custom validation function for color combinations
def validate_color_combination(colors):
    valid_colors = ['W', 'U', 'B', 'R', 'G', 'C']
    if 'C' in colors and len(colors) > 1:
        raise argparse.ArgumentTypeError("Colorless (C) cannot be combined with other colors")

    for color in colors:
        if color not in valid_colors:
            raise argparse.ArgumentTypeError(f"Invalid color: {color}")
    return list("".join(colors))

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

    def __repr__(self):
        '''return '\n'.join(
            '{}:{}'.format(
                str(k), str(v) if not isinstance(v, JSONObject) else repr(v).replace('\n', '\n\t')
            )
            for k,v in self.__dict__.items()
        )'''
        return json.dumps(self.json, indent=4)

RATE = 120/60 #[s]

DEFAULT_QUERY = {
    'standing': {'$lte': 16},
    'colorID': 'WUBRG',
    'tourney_filter': {
        'size': {'$gte': 64}
    }
}

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
            data['standing']['$lte'] = args.tstanding.lte
        if args.tstanding.gte is not None:
            data['standing']['$gte'] = args.tstanding.gte

    if args.tsize is not None or args.tdate is not None:
        data['tourney_filter'] = {}
        if args.tsize is not None:
            data['tourney_filter']['size'] = {}
            if args.tsize.lte is not None:
                data['tourney_filter']['size']['$lte'] = args.tsize.lte
            if args.tsize.gte is not None:
                data['tourney_filter']['size']['$gte'] = args.tsize.gte
        if args.tdate is not None:
            data['tourney_filter']['dateCreated'] = {}
            if args.tdate.lte is not None:
                data['tourney_filter']['dateCreated']['$lte'] = args.tdate.lte
            if args.tdate.gte is not None:
                data['tourney_filter']['dateCreated']['$gte'] = args.tdate.gte
    if args.tentries is not None:
        data['entries'] = {}
        if args.tentries.lte is not None:
            data['entries']['$lte'] = args.tentries.lte
        if args.tentries.gte is not None:
            data['entries']['$gte'] = args.tentries.gte
    if args.color is not None:
        data['colorID'] = args.color
    return JSONObject(**data)

def get_entries(query):
    data = json.loads(requests.post(base_url + 'req', json=query.json, headers=headers).text)
    entries = [JSONObject(**entry) for entry in data]
    unique_commanders = set(x.commander for x in entries)

    return entries




def decode_url_query(url):
    '''
    Decodes a url query into a dict
    '''

    URL  = urllib.parse.unquote(url)

    query = {}
    for key, value in urllib.parse.parse_qs(URL.split("?")[1]).items():
        key = key.split("__")
        if len(key) == 1:
            query[key[0]] = value[0]
        elif len(key) == 2:
            if key[0] not in query:
                query[key[0]] = {}
            query[key[0]][key[1]] = value[0]
        elif len(key) == 3:
            if key[0] not in query:
                query[key[0]] = {}
            if key[1] not in query[key[0]]:
                query[key[0]][key[1]] = {}
            #TODO: Correct types
            query[key[0]][key[1]][key[2]] = int(value[0]) if value[0].isdigit() else value[0]


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
    url = "https://edhtop16.com/?tourney_filter__size__%24gte=64&tourney_filter__dateCreated__%24gte=1672527600&standing__%24lte=16&entries__%24gte=20&colorID=null"
    org_query = decode_url_query(url)
    #print(org_query)
    query = generate_query(args)
    print(query)
    entries = get_entries(org_query)

    #print(entries)
    pass

