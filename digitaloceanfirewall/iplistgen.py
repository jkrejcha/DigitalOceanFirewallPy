from __future__ import annotations

import json
from ipaddress import ip_network
from typing import Final

import requests

from digitaloceanfirewall.types import AnyIpNetwork


class IpListGen:
	__slots__ = ()

	def get_cidr_list(self) -> list[AnyIpNetwork]:
		raise NotImplementedError()

_CF_URL_IPV4: Final[str] = "https://www.cloudflare.com/ips-v4/"
_CF_URL_IPV6: Final[str] = "https://www.cloudflare.com/ips-v6/"

class CloudflareListGen(IpListGen):
	__slots__ = ()

	def get_cidr_list(self) -> list[AnyIpNetwork]:
		ipv4: Final[str] = requests.get(_CF_URL_IPV4).text
		ipv6: Final[str] = requests.get(_CF_URL_IPV6).text
		return [
			ip_network(network)
			for network
			in ipv4.split('\n') + ipv6.split('\n')
		]

_DATA_FILE: Final[str] = "data/countries.json"

class CountryListGen(IpListGen):
	__slots__ = ('country')

	def __init__(self, country: str) -> None:
		self.country: str = country

	def get_cidr_list(self) -> list[AnyIpNetwork]:
		with open(_DATA_FILE, 'rt', encoding='utf-8') as f:
			ip_json = json.load(f)
		ips: dict[str, list[AnyIpNetwork]] = {}
		ip_key: Final[str] = self.country

		ips[ip_key] = []
		for country_name in ip_json[ip_key]:
			ips[ip_key].extend(
				[
					ip_network(network)
					for network
					in ip_json[ip_key][country_name]
					if '.' in network # Lol IPv6
				]
			)
		return ips[ip_key]


def get_list_gen(type: str) -> IpListGen:
	if type == 'cloudflare':
		return CloudflareListGen()
	elif type == 'us':
		return CountryListGen('US')
	else:
		raise Exception("Invalid argument '" + type + "'")
