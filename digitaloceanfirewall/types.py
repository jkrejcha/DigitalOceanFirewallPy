from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network

AnyIpAddress = IPv4Address | IPv6Address
AnyIpNetwork = IPv4Network | IPv6Network
