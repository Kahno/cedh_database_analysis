import argparse
import datetime
from scraper import *
import json
import requests
from enum import Enum
from datetime import datetime, date


base_url = "https://edhtop16.com/api/"
headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


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
        return '\n'.join(
            '{}:{}'.format(
                str(k), str(v) if not isinstance(v, JSONObject) else repr(v).replace('\n', '\n\t')
            )
            for k,v in self.__dict__.items()
        )

RATE = 120/60 #[s]

DEFAULT_QUERY = {
    'standing': {'$lte': 16},
    'colorID': 'WUBRG',
    'tourney_filter': {
        'size': {'$gte': 64}
    }
}

CMP = JSONObject(**{
    'LTE': '$lte',
    'GTE': '$gte',
    'EQ': '$eq',
})

def str2timestamp(s:str) -> int:
    '''
    Converts a string of the form DDMMYYYY to a unix timestamp
    '''
    return int(datetime.strptime(s, '%d%m%Y').timestamp())

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
    parser.add_argument('--size', dest='tsize', nargs='+', help='Size filter (optional: gte/lte followed by a number)')
    parser.add_argument('--date', dest='tdate', nargs='+', help='Date filter (optional: gte/lte followed by a date)')

    # Parse the command-line arguments
    args = parser.parse_args()

    dtypes = {
        'tsize': int,
        'tdate': str2timestamp,
        'standing': int,
    }
    for arg in vars(args):
        opt_args = getattr(args, arg)
        if opt_args is not None:
            option_parser = argparse.ArgumentParser(prefix_chars='+')
            dtype = dtypes[arg]

            option_parser.add_argument('+lte', type=dtype, help='Maximum tournament size')
            option_parser.add_argument('+gte', type=dtype, help='Minimum tournament size')
            opt_args = option_parser.parse_args(getattr(args, arg))

            setattr(args, arg, opt_args)




    # Use the filter values as needed
    # Perform further processing or actions based on the filters


    '''size.add_argument('--gte', type=int, help='Minimum tournament size')
    size.add_argument('--lte', type=int, help='Maximum tournament size')

    #max/min/eq date
    tdate = parser.add_argument_group('Tournament date')
    tdate.add_argument('--gte', type=str2timestamp, help='Minimum tournament date')
    tdate.add_argument('--lte', type=str2timestamp, help='Maximum tournament date')

    standing = parser.add_argument_group('Placement')
    standing.add_argument('--lte', type=int, help='Maximum placement')
    standing.add_argument('--gte', type=int, help='Minimum placement')'''


    # Parse the command-line arguments


    pass

