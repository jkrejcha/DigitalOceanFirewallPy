import argparse
import sys
from typing import Any, MutableMapping

from pydo import Client

from digitaloceanfirewall.iplistgen import IpListGen, get_list_gen
from digitaloceanfirewall.types import AnyIpNetwork
from env.env import API_KEY

_Json = MutableMapping[str, Any]


def _check_valid_port(value: str) -> int:
	try:
		port: int = int(value)
	except ValueError as e:
		raise argparse.ArgumentTypeError(f"Value '{value}' is not an integer") from e
	if 1 < port > 65535:
		raise argparse.ArgumentTypeError(f"Value '{value}' is not a valid TCP port (valid 1-65535)")
	return port


parser: argparse.ArgumentParser = argparse.ArgumentParser(
	prog="digitaloceanfirewallpy",
	description="DigitalOceanFirewallPy: an application to manage DigitalOcean firewalls",
)

parser.add_argument(
	"name",
	help=(
		"Name of firewall to use"
	),
)

parser.add_argument(
	"whitelist_type",
	choices=['cloudflare', 'us'],
	help=(
		"IP ranges to whitelist"
	)
)

parser.add_argument(
	"tcp_port",
	type=_check_valid_port,
	help=(
		"TCP Port to whitelist (range: 1-65535)"
	)
)

parser.add_argument(
	"--key",
	help=(
		"Specify a custom API key to use"
	),
	default=API_KEY,
)

parser.add_argument(
	"--remove-existing-rules",
	help=(
		"Remove existing rules, if available (default false)"
	),
	type=bool,
	default=False,
)

parsed: argparse.Namespace = parser.parse_args()
listgen: IpListGen = get_list_gen(parsed.whitelist_type)
networks: list[AnyIpNetwork] = listgen.get_cidr_list()

def pinfo(text: str) -> None:
	print(f'[Info] {text}')

pinfo("Generated IP list, now uploading to API")

do: Client = Client(parsed.key)

firewalls: list[_Json] = do.firewalls.list()["firewalls"]
firewall_id: str | None = None
firewall_t: _Json | None = None
for firewall in firewalls:
	if parsed.name.lower() == firewall["name"].lower():
		firewall_id = firewall["id"]
		firewall_t = firewall
		pinfo(f"Found firewall with ID '{firewall_id}'")
		break
else:
	pinfo("Could not find firewall, exiting...")
	sys.exit(2) # File not found

assert firewall_id is not None
assert firewall_t is not None

if parsed.remove_existing_rules and firewall_t.get("inbound_rules"):
	do.firewalls.delete_rules(firewall_id, {
		"inbound_rules": firewall_t["inbound_rules"]
	})
do.firewalls.add_rules(firewall_id, {
	"inbound_rules": [
		{
			"protocol": "tcp",
			"ports": parsed.tcp_port,
			"sources": {
				"addresses": [str(network) for network in networks],
			},
		},
	]
})
