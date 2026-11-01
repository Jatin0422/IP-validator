import ipaddress

import pytest

try:
    from .core import (address_formats, classify_ipv4, classify_ipv6, ip_range,
                       same_network, split_subnet, subnet_info,
                       validate_ipv4, validate_ipv6)
except ImportError:
    from core import (address_formats, classify_ipv4, classify_ipv6, ip_range,
                      same_network, split_subnet, subnet_info,
                      validate_ipv4, validate_ipv6)


@pytest.mark.parametrize("address", [
    "0.0.0.0", "1.2.3.4", "255.255.255.255", "192.168.1.1",
    "10.0.0.1", "172.16.0.1", "172.31.255.255", "127.0.0.1",
    "169.254.1.2", "224.0.0.1", "240.0.0.1", "8.8.8.8",
])
def test_ipv4_valid_and_crosscheck(address):
    assert validate_ipv4(address) == {"valid": True, "error": None}
    ipaddress.IPv4Address(address)


@pytest.mark.parametrize("address,error", [
    ("256.1.1.1", "octet 1 is 256, must be 0-255"), ("1.1.1", "expected 4 octets, got 3"),
    ("01.1.1.1", "octet 1 has a leading zero"), ("1..1.1", "octet 2 is empty"),
    ("1.a.1.1", "octet 2 must contain only digits"), (" 1.1.1.1", "whitespace is not allowed"),
    ("1.1.1.1.", "expected 4 octets, got 5"),
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
    ":::", "1:::2", "1::2:", ":1::2",
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
    ("100.64.0.1", ("A", "shared")), ("192.0.2.1", ("C", "documentation")),
    ("198.51.100.5", ("C", "documentation")), ("203.0.113.2", ("C", "documentation")),
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


@pytest.mark.parametrize("address,mask,expected_role", [
    ("192.168.1.128", "/26", "network address"),
    ("192.168.1.191", "/26", "broadcast address"),
    ("192.168.1.129", "/26", "usable host"),
    ("192.168.1.190", "/26", "usable host"),
    ("192.168.1.128", "255.255.255.192", "network address"),
    ("192.168.1.191", "255.255.255.192", "broadcast address"),
    ("192.168.1.129", "255.255.255.192", "usable host"),
    ("192.168.1.190", "255.255.255.192", "usable host"),
    ("192.168.1.0", "/24", "network address"),
    ("192.168.1.255", "/24", "broadcast address"),
    ("0.0.0.0", "/0", "network address"),
    ("255.255.255.255", "/0", "broadcast address"),
    ("192.0.2.0", "/31", "usable host (point-to-point /31)"),
    ("192.0.2.1", "/31", "usable host (point-to-point /31)"),
    ("192.0.2.1", "/32", "single host (/32)"),
])
def test_subnet_role_crosscheck(address, mask, expected_role):
    result = subnet_info(address, mask)
    network = ipaddress.IPv4Network((address, int(mask[1:]) if mask.startswith("/") else mask), strict=False)
    assert result["role"] == expected_role
    assert result["network"] == str(network.network_address)
    assert result["broadcast"] == str(network.broadcast_address)
    if mask not in ("/31", "/32"):
        if result["role"] == "network address":
            assert ipaddress.ip_address(address) == network.network_address
        elif result["role"] == "broadcast address":
            assert ipaddress.ip_address(address) == network.broadcast_address
        else:
            assert ipaddress.ip_address(address) not in (network.network_address, network.broadcast_address)


@pytest.mark.parametrize("ip,mask", [("300.1.1.1", "/24"), ("1.1.1.1", "255.0.255.0"), ("1.1.1.1", "/33"), ("1.1.1.1", "abc")])
def test_subnet_rejects_bad_input(ip, mask):
    with pytest.raises(ValueError):
        subnet_info(ip, mask)


@pytest.mark.parametrize("address,category", [
    ("::", "unspecified"), ("::1", "loopback"), ("fe80::1234", "link-local"),
    ("febf::1", "link-local"), ("fc00::1", "unique-local"),
    ("fd12::1", "unique-local"), ("ff02::1", "multicast"),
    ("2001:db8::1", "documentation"), ("::ffff:192.0.2.1", "ipv4-mapped"),
])
def test_classify_ipv6(address, category):
    assert classify_ipv6(address)["category"] == category
    ipaddress.IPv6Address(address)


def test_same_network_crosscheck():
    pairs = [("192.168.1.1", "192.168.1.200", "/24"), ("10.0.0.1", "10.0.1.1", "/24")]
    for first, second, prefix in pairs:
        expected = ipaddress.IPv4Network((first, int(prefix[1:])), strict=False) == ipaddress.IPv4Network((second, int(prefix[1:])), strict=False)
        assert same_network(first, second, prefix) is expected


def test_split_subnet_crosscheck():
    result = split_subnet("192.168.1.0/24", 4)
    expected = list(ipaddress.ip_network("192.168.1.0/24").subnets(prefixlen_diff=2))
    assert [row["cidr"] for row in result] == [str(net) for net in expected]


def test_ip_range_crosscheck_and_cap():
    result = ip_range("192.0.2.1", "192.0.2.4")
    assert result == [str(ipaddress.ip_address(int(ipaddress.ip_address("192.0.2.1")) + i)) for i in range(4)]
    with pytest.raises(ValueError):
        ip_range("0.0.0.0", "0.0.4.0")


@pytest.mark.parametrize("address", [
    "192.0.2.1", "2001:db8::1", "1:2:3:4:5:6:1.2.3.4",
    "ff:1:abcd:1:ff:0:1.2.3.4",
])
def test_address_formats_crosscheck(address):
    expected = int(ipaddress.ip_address(address))
    result = address_formats(address)
    assert result["integer"] == str(expected)
    assert int(result["hex"], 16) == expected
    assert int(result["binary"].replace(".", ""), 2) == expected


@pytest.mark.parametrize("address,category", [
    ("1:2:3:4:5:6:1.2.3.4", "global"),
    ("ff:1:abcd:1:ff:0:1.2.3.4", "global"),
])
def test_classify_ipv6_full_form_ipv4_tail(address, category):
    assert classify_ipv6(address)["category"] == category
    ipaddress.IPv6Address(address)


def test_split_subnet_rejects_more_than_1024():
    with pytest.raises(ValueError, match="cannot exceed 1024"):
        split_subnet("10.0.0.0/8", 2048)
