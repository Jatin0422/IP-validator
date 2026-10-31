import ipaddress

import pytest

try:
    from .core import classify_ipv4, subnet_info, validate_ipv4, validate_ipv6
except ImportError:
    from core import classify_ipv4, subnet_info, validate_ipv4, validate_ipv6


@pytest.mark.parametrize("address", [
    "0.0.0.0", "1.2.3.4", "255.255.255.255", "192.168.1.1",
    "10.0.0.1", "172.16.0.1", "172.31.255.255", "127.0.0.1",
    "169.254.1.2", "224.0.0.1", "240.0.0.1", "8.8.8.8",
])
def test_ipv4_valid_and_crosscheck(address):
    assert validate_ipv4(address) == {"valid": True, "error": None}
    ipaddress.IPv4Address(address)


@pytest.mark.parametrize("address,error", [
    ("256.1.1.1", "octet >255"), ("1.1.1", "wrong octet count"),
    ("01.1.1.1", "leading zero"), ("1..1.1", "empty octet"),
    ("1.a.1.1", "non-digit octet"), (" 1.1.1.1", "whitespace is not allowed"),
    ("1.1.1.1.", "wrong octet count"),
])
def test_ipv4_invalid(address, error):
    assert validate_ipv4(address) == {"valid": False, "error": error}
    with pytest.raises(ipaddress.AddressValueError):
        ipaddress.IPv4Address(address)


@pytest.mark.parametrize("address", [
    "::", "::1", "2001:db8::1", "2001:db8:0:0:0:0:0:1",
    "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff", "::ffff:192.0.2.1",
    "2001:db8::192.0.2.1", "1:2:3:4:5:6:192.0.2.1",
])
def test_ipv6_valid_and_crosscheck(address):
    assert validate_ipv6(address)["valid"]
    ipaddress.IPv6Address(address)


@pytest.mark.parametrize("address", [
    "1::2::3", "1:2:3", "1:2:3:4:5:6:7:8:9", "12345::1",
    "gggg::1", ":1:2:3:4:5:6:7:8", "1:2:3:4:5:6:7:",
    "::ffff:256.0.0.1", "1:2:3:4:5:192.0.2.1",
])
def test_ipv6_invalid(address):
    assert not validate_ipv6(address)["valid"]
    with pytest.raises(ipaddress.AddressValueError):
        ipaddress.IPv6Address(address)


@pytest.mark.parametrize("address,expected", [
    ("10.1.2.3", ("A", "private")), ("172.16.0.1", ("B", "private")),
    ("192.168.0.1", ("C", "private")), ("127.0.0.1", ("A", "loopback")),
    ("169.254.0.1", ("B", "link-local")), ("224.0.0.1", ("D", "multicast")),
    ("240.0.0.1", ("E", "reserved")), ("0.1.2.3", ("A", "reserved")),
    ("8.8.8.8", ("A", "public")),
])
def test_classification(address, expected):
    result = classify_ipv4(address)
    assert (result["class"], result["category"]) == expected


@pytest.mark.parametrize("address,mask", [
    ("192.168.1.129", "/26"), ("0.1.2.3", "/0"),
    ("10.0.0.0", "/31"), ("10.0.0.1", "/32"),
    ("192.168.1.129", "255.255.255.192"),
])
def test_subnet_crosscheck(address, mask):
    result = subnet_info(address, mask)
    network = ipaddress.IPv4Network((address, int(mask[1:])), strict=False) if mask.startswith("/") else ipaddress.IPv4Network((address, mask), strict=False)
    assert result["network"] == str(network.network_address)
    assert result["broadcast"] == str(network.broadcast_address)
    assert result["subnet_mask"] == str(network.netmask)
    assert result["wildcard"] == str(network.hostmask)
    assert result["total_addresses"] == network.num_addresses
    assert result["ip_binary"] == ".".join(f"{int(x):08b}" for x in address.split("."))


def test_subnet_host_edge_cases():
    assert subnet_info("192.0.2.1", "/31")["usable_hosts"] == 2
    assert subnet_info("192.0.2.1", "/32")["first_host"] == "192.0.2.1"
    assert subnet_info("192.0.2.1", "/32")["usable_hosts"] == 1


@pytest.mark.parametrize("ip,mask", [("300.1.1.1", "/24"), ("1.1.1.1", "255.0.255.0"), ("1.1.1.1", "/33"), ("1.1.1.1", "abc")])
def test_subnet_rejects_bad_input(ip, mask):
    with pytest.raises(ValueError):
        subnet_info(ip, mask)
