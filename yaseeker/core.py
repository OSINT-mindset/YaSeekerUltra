import json
import os
import sys
from http.cookiejar import MozillaCookieJar
import requests
from socid_extractor import extract

import asyncio
from typing import List, Any

from aiohttp import TCPConnector, ClientSession

from .executor import AsyncioProgressbarQueueExecutor, AsyncioSimpleExecutor

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
}

COOKIES_FILENAME = 'cookies.txt'


def load_cookies(filename):
    cookies = {}
    if os.path.exists(filename):
        cookies_obj = MozillaCookieJar(filename)
        cookies_obj.load(ignore_discard=False, ignore_expires=False)

        for domain in cookies_obj._cookies.values():
            for cookie_dict in list(domain.values()):
                for _, cookie in cookie_dict.items():
                    cookies[cookie.name] = cookie.value

    return cookies


class ObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class IdTypeInfoAggregator:
    acceptable_fields = ()

    def __init__(self, identifier: str, cookies: dict):
        self.identifier = identifier
        self.cookies = cookies
        self.info = {}
        self.sites_results = {}

    @classmethod
    def validate_id(cls, name, identifier):
        return name in cls.acceptable_fields

    def aggregate(self, info: dict):
        for k, v in info.items():
            if k in self.info:
                if isinstance(self.info[k], set):
                    self.info[k].add(v)
                else:
                    self.info[k] = {self.info[k], v}
            else:
                self.info[k] = v

    def simple_get_info_request(self, url: str, headers_updates: dict = None, orig_url: str = None) -> dict:
        headers = dict(HEADERS)
        headers.update(headers_updates if headers_updates else {})
        r = requests.get(url, headers=headers, cookies=self.cookies)

        if '/checkcaptcha?key=' in r.text:
            info = {'Error': 'Captcha detected'}
        else:
            try:
                info = extract(r.text)
            except Exception as e:
                print(f'Error for URL {url}: {e}\n')
                info = {}

            if info:
                info['URL'] = orig_url or url
                if orig_url and url and orig_url != url:
                    info['URL_secondary'] = url

        return info

    def collect(self):
        for f in self.__dir__():
            if f.startswith('get_'):
                info = getattr(self, f)()
                name = ' '.join(f.split('_')[1:-1])
                self.sites_results[name] = info
                self.aggregate(info)

    def print(self):
        for sitename, data in self.sites_results.items():
            print('[+] Yandex.' + sitename[0].upper() + sitename[1:])
            if not data:
                print('\tNot found.\n')
                continue

            if 'URL' in data:
                print(f'\tURL: {data.get("URL")}')
            for k, v in data.items():
                if k != 'URL':
                    print('\t' + k.capitalize() + ': ' + v)
            print()


class YaUsername(IdTypeInfoAggregator):
    acceptable_fields = ('username',)

    def get_collections_API_info(self) -> dict:
        return self.simple_get_info_request(
            url=f'https://yandex.ru/collections/api/users/{self.identifier}',
            orig_url=f'https://yandex.ru/collections/user/{self.identifier}/'
        )

    def get_music_info(self) -> dict:
        orig_url = f'https://music.yandex.ru/users/{self.identifier}/playlists'
        referer = {'referer': orig_url}
        return self.simple_get_info_request(
            url=f'https://music.yandex.ru/handlers/library.jsx?owner={self.identifier}',
            orig_url=orig_url,
            headers_updates=referer,
        )

    def get_bugbounty_info(self) -> dict:
        return self.simple_get_info_request(f'https://yandex.ru/bugbounty/researchers/{self.identifier}/')

    def get_messenger_search_info(self) -> dict:
        url = 'https://yandex.ru/messenger/api/registry/api/'
        data = {"method": "search",
                "params": {"query": self.identifier, "limit": 10, "entities": ["messages", "users_and_chats"]}}
        r = requests.post(url, headers=HEADERS, cookies=self.cookies, files={'request': (None, json.dumps(data))})
        info = extract(r.text)
        if info and info.get('yandex_messenger_guid'):
            info['URL'] = f'https://yandex.ru/chat#/user/{info["yandex_messenger_guid"]}'
        return info

    def get_music_API_info(self) -> dict:
        return self.simple_get_info_request(f'https://api.music.yandex.net/users/{self.identifier}')


class YaPublicUserId(IdTypeInfoAggregator):
    acceptable_fields = ('yandex_public_id', 'id',)

    @classmethod
    def validate_id(cls, name, identifier):
        # len(identifier) == 26 and
        # may be a non-standard
        return name in cls.acceptable_fields

    def get_collections_API_info(self) -> dict:
        return self.simple_get_info_request(
            url=f'https://yandex.ru/collections/api/users/{self.identifier}',
            orig_url=f'https://yandex.ru/collections/user/{self.identifier}/'
        )

    def get_reviews_info(self) -> dict:
        return self.simple_get_info_request(f'https://reviews.yandex.ru/user/{self.identifier}')

    def get_znatoki_info(self) -> dict:
        return self.simple_get_info_request(f'https://yandex.ru/q/profile/{self.identifier}/')

    def get_zen_info(self) -> dict:
        return self.simple_get_info_request(f'https://zen.yandex.ru/user/{self.identifier}')

    def get_market_info(self) -> dict:
        return self.simple_get_info_request(f'https://market.yandex.ru/user/{self.identifier}/reviews')

    def get_o_info(self) -> dict:
        return self.simple_get_info_request(f'http://o.yandex.ru/profile/{self.identifier}/')

    def get_kinopoisk_info(self) -> dict:
        return self.simple_get_info_request(f'https://www.kinopoisk.ru/user/{self.identifier}/')


class YaMessengerGuid(IdTypeInfoAggregator):
    acceptable_fields = ('yandex_messenger_guid',)

    @classmethod
    def validate_id(cls, name, identifier):
        return len(identifier) == 36 and '-' in identifier and name in cls.acceptable_fields

    def get_messenger_info(self) -> dict:
        url = 'https://yandex.ru/messenger/api/registry/api/'
        data = {"method": "get_users_data", "params": {"guids": [self.identifier]}}
        r = requests.post(url, headers=HEADERS, cookies=self.cookies, files={'request': (None, json.dumps(data))})
        info = extract(r.text)
        if info:
            info['URL'] = f'https://yandex.ru/chat#/user/{self.identifier}'
        return info


def crawl(user_data: dict, output: dict, cookies: dict = None, checked_values: list = None):
    # print(user_data)

    entities = (YaUsername, YaPublicUserId, YaMessengerGuid)
    if cookies is None:
        cookies = {}
    if checked_values is None:
        checked_values = []

    for k, v in user_data.items():
        values = list(v) if isinstance(v, set) else [v]
        for value in values:
            if value in checked_values:
                continue

            for e in entities:
                if not e.validate_id(k, value):
                    continue

                checked_values.append(value)

                # print(f'[*] Get info by {k} `{value}`...\n')
                entity_obj = e(value, cookies)
                entity_obj.collect()
                # entity_obj.print()

                output[entity_obj.identifier] = entity_obj.sites_results

                crawl(entity_obj.info, output, cookies, checked_values)

    return output


class InputData:
    def __init__(self, value: str):
        self.value = value.split('@')[0]
        self.identifier_type = 'username'

    def __str__(self):
        return f'{self.value} ({self.identifier_type})'

    def __repr__(self):
        return f'{self.value} ({self.identifier_type})'


class OutputData:
    def __init__(self, value, dict_data, error):
        self.value = value
        self.error = error
        self.__dict__.update(dict_data)
        print(self.__dict__)

    @property
    def fields(self):
        fields = list(self.__dict__.keys())
        fields.remove('error')

        return fields

    def __str__(self):
        error = ''
        if self.error:
            error = f' (error: {str(self.error)}'

        result = ''

        for field in self.fields:
            field_pretty_name = field.title().replace('_', ' ')
            value = self.__dict__.get(field)
            if value:
                result += f'{field_pretty_name}: {str(value)}\n'

        result += f'{error}'
        return result


class OutputDataList:
    def __init__(self, input_data: InputData, results: List[OutputData]):
        self.input_data = input_data
        self.results = results

    def __repr__(self):
        return f'Target {self.input_data}:\n' + '--------\n'.join(map(str, self.results))


class Processor:
    def __init__(self, *args, **kwargs):
        from aiohttp_socks import ProxyConnector

        # make http client session
        proxy = kwargs.get('proxy')
        self.proxy = proxy
        if proxy:
            connector = ProxyConnector.from_url(proxy, ssl=False)
        else:
            connector = TCPConnector(ssl=False)

        self.session = ClientSession(
            connector=connector, trust_env=True
        )
        if kwargs.get('no_progressbar'):
            self.executor = AsyncioSimpleExecutor()
        else:
            self.executor = AsyncioProgressbarQueueExecutor()

        # yandex setup
        self.cookies = load_cookies(COOKIES_FILENAME)
        if not self.cookies:
            print(f'Cookies not found, but are required for some sites. See README to learn how to use cookies.')

    async def close(self):
        await self.session.close()


    async def request(self, input_data: InputData) -> OutputDataList:
        data = []
        result = None
        error = None

        try:
            identifier = {input_data.identifier_type: input_data.value}
            output_data = crawl(identifier, {}, cookies=self.cookies)

            print('here')

            for ident, result in output_data.items():
                for platform, fields in result.items():
                    platform = platform.title().replace('_', ' ')
                    fields = fields or {}
                    fields.update({'platform': platform})

                    print('fields')
                    print(fields)
                    od = OutputData(ident, fields, error)
                    data.append(od)
                    print(od)

        except Exception as e:
            error = e

        results = OutputDataList(input_data, data)

        return results


    async def process(self, input_data: List[InputData]) -> List[OutputDataList]:
        tasks = [
            (
                self.request, # func
                [i],          # args
                {}            # kwargs
            )
            for i in input_data
        ]

        results = await self.executor.run(tasks)

        return results
