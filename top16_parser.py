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

data = JSONObject(**DEFAULT_QUERY)

assert 1672527600 == str2timestamp('01012023')
assert str2timestamp('02012023') - str2timestamp('01012023') == 24*60*60
assert data.json == DEFAULT_QUERY

entries = json.loads(requests.post(base_url + 'req', json=data.json, headers=headers).text)
sprint(entries)

if __name__ == '__main__':
    #parser
    parser = argparse.ArgumentParser(description='EDH Top 16 Parser')
    #max/min/eq tournament size
    size = parser.add_mutually_exclusive_group()

    # Add the operation argument
    size.add_argument('op', choices=['lte', 'gte', 'eq'], help='Tournament size operation')
    # Add the number argument
    size.add_argument('n', type=int, help='Number to compare')

    # Parse the command-line arguments
    args = parser.parse_args()

