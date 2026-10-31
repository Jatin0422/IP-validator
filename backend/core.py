"""Pure IPv4/IPv6 validation and IPv4 subnet calculations."""


def validate_ipv4(s):
    if any(ch.isspace() for ch in s):
        return {"valid": False, "error": "whitespace is not allowed"}
    octets = s.split(".")
    if len(octets) != 4:
        return {"valid": False, "error": f"expected 4 octets, got {len(octets)}"}
    for index, octet in enumerate(octets, 1):
        if not octet:
            return {"valid": False, "error": f"octet {index} is empty"}
        if not all("0" <= ch <= "9" for ch in octet):
            return {"valid": False, "error": f"octet {index} must contain only digits"}
        if len(octet) > 1 and octet[0] == "0":
            return {"valid": False, "error": f"octet {index} has a leading zero"}
        if int(octet) > 255:
            return {"valid": False, "error": f"octet {index} is {octet}, must be 0-255"}
    return {"valid": True, "error": None}


def validate_ipv6(s):
    if not s:
        return {"valid": False, "error": "empty address"}
    if any(ch.isspace() for ch in s):
        return {"valid": False, "error": "whitespace is not allowed"}
    if s.count("::") > 1:
        return {"valid": False, "error": "compression may appear only once"}
    compressed = "::" in s
    if not compressed and (s.startswith(":") or s.endswith(":")):
        return {"valid": False, "error": "single leading or trailing colon"}
    ipv4_words = 0
    if "." in s:
        tail = s.rsplit(":", 1)[-1]
        v4 = validate_ipv4(tail)
        if not v4["valid"]:
            return {"valid": False, "error": "invalid IPv4-mapped tail: " + v4["error"]}
        ipv4_words = 2
        prefix_text = s[: -(len(tail))]
        s = prefix_text if prefix_text.endswith("::") else prefix_text[:-1]
    groups = s.split(":") if s else []
    if compressed:
        left, right = s.split("::")
        left_groups = left.split(":") if left else []
        right_groups = right.split(":") if right else []
        if any(not group for group in left_groups + right_groups):
            return {"valid": False, "error": "empty group outside compression"}
        groups = left_groups + right_groups
        if len(groups) + ipv4_words >= 8:
            return {"valid": False, "error": "compression must omit at least one group"}
    elif len(groups) + ipv4_words != 8:
        return {"valid": False, "error": "wrong group count"}
    for group in groups:
        if not 1 <= len(group) <= 4 or any(ch not in "0123456789abcdefABCDEF" for ch in group):
            return {"valid": False, "error": "invalid hexadecimal group"}
    return {"valid": True, "error": None}


def _ipv4_int(s):
    parsed = validate_ipv4(s)
    if not parsed["valid"]:
        raise ValueError(parsed["error"])
    value = 0
    for part in s.split("."):
        value = (value << 8) | int(part)
    return value


def _dotted(value):
    return ".".join(str((value >> shift) & 255) for shift in (24, 16, 8, 0))


def _binary(value):
    return ".".join(f"{(value >> shift) & 255:08b}" for shift in (24, 16, 8, 0))


def classify_ipv4(s):
    value = _ipv4_int(s)
    first = (value >> 24) & 255
    if first < 128:
        klass = "A"
    elif first < 192:
        klass = "B"
    elif first < 224:
        klass = "C"
    elif first < 240:
        klass = "D"
    else:
        klass = "E"
    if (value >> 24) == 10 or (value >> 20) == 0xAC1 or (value >> 16) == 0xC0A8:
        category = "private"
    elif (value >> 22) == 0x191:  # 100.64.0.0/10
        category = "shared"
    elif ((value >> 8) == 0xC00002 or (value >> 8) == 0xC63364 or
          (value >> 8) == 0xCB0071):
        category = "documentation"
    elif (value >> 24) == 127:
        category = "loopback"
    elif (value >> 16) == 0xA9FE:
        category = "link-local"
    elif first >= 224 and first <= 239:
        category = "multicast"
    elif first >= 240 or first == 0:
        category = "reserved"
    else:
        category = "public"
    return {"class": klass, "category": category}


def _ipv6_int(s):
    result = validate_ipv6(s)
    if not result["valid"]:
        raise ValueError(result["error"])
    if "." in s:
        tail = s.rsplit(":", 1)[-1]
        v4 = _ipv4_int(tail)
        s = s[: -(len(tail))]
        s = s if s.endswith("::") else s[:-1]
        if "::" in s:
            left_text, right_text = s.split("::")
            left = left_text.split(":") if left_text else []
            right = right_text.split(":") if right_text else []
            words = [int(g, 16) for g in left] + [0] * (6 - len(left) - len(right)) + [int(g, 16) for g in right]
        else:
            words = [int(group, 16) for group in s.split(":")]
        words += [(v4 >> 16) & 0xFFFF, v4 & 0xFFFF]
    else:
        if "::" in s:
            left, right = s.split("::")
            a = left.split(":") if left else []
            b = right.split(":") if right else []
            words = [int(g, 16) for g in a] + [0] * (8 - len(a) - len(b)) + [int(g, 16) for g in b]
        else:
            words = [int(g, 16) for g in s.split(":")]
    value = 0
    for word in words:
        value = (value << 16) | word
    return value


def classify_ipv6(s):
    value = _ipv6_int(s)
    if value >> 32 == 0xFFFF:
        category = "ipv4-mapped"
    elif value >> 96 == 0x20010DB8:
        category = "documentation"
    elif value == 1:
        category = "loopback"
    elif value == 0:
        category = "unspecified"
    elif value >> 118 == 0x3FA:  # fe80::/10
        category = "link-local"
    elif value >> 121 == 0x7E:  # fc00::/7
        category = "unique-local"
    elif value >> 120 == 0xFF:
        category = "multicast"
    else:
        category = "global"
    return {"category": category}


def address_formats(s):
    if ":" in s:
        value, width = _ipv6_int(s), 128
        return {"binary": f"{value:0{width}b}", "hex": f"{value:0{width // 4}x}", "integer": value}
    value, width = _ipv4_int(s), 32
    return {"binary": _binary(value), "hex": f"{value:0{width // 4}x}", "integer": value}


def subnet_info(ip, prefix_or_mask):
    address = _ipv4_int(ip)
    if not isinstance(prefix_or_mask, str):
        prefix_or_mask = str(prefix_or_mask)
    if prefix_or_mask.startswith("/"):
        raw = prefix_or_mask[1:]
        if not raw or not raw.isdigit() or int(raw) > 32:
            raise ValueError("prefix must be between /0 and /32")
        prefix = int(raw)
        mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF if prefix else 0
    elif prefix_or_mask.isdigit():
        prefix = int(prefix_or_mask)
        if prefix > 32:
            raise ValueError("prefix must be between /0 and /32")
        mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF if prefix else 0
    else:
        mask = _ipv4_int(prefix_or_mask)
        inverse = (~mask) & 0xFFFFFFFF
        if inverse & (inverse + 1):
            raise ValueError("subnet mask must be contiguous")
        prefix = mask.bit_count()
    wildcard = (~mask) & 0xFFFFFFFF
    network = address & mask
    broadcast = network | wildcard
    total = 1 << (32 - prefix)
    if prefix == 32:
        first_host = last_host = address
        usable = 1
    elif prefix == 31:
        first_host, last_host, usable = network, broadcast, 2
    else:
        first_host, last_host, usable = network + 1, broadcast - 1, max(total - 2, 0)
    return {
        "ip": ip, "prefix": prefix, "subnet_mask": _dotted(mask),
        "wildcard": _dotted(wildcard), "network": _dotted(network),
        "broadcast": _dotted(broadcast), "first_host": _dotted(first_host),
        "last_host": _dotted(last_host), "total_addresses": total,
        "usable_hosts": usable, "ip_binary": _binary(address),
        "mask_binary": _binary(mask), "network_binary": _binary(network),
    }


def same_network(ip1, ip2, mask):
    first = subnet_info(ip1, mask)
    second = subnet_info(ip2, mask)
    return first["network"] == second["network"]


def split_subnet(network, n):
    if not isinstance(n, int) or isinstance(n, bool) or n < 1 or n & (n - 1):
        raise ValueError("n must be a positive power of 2")
    if n > 1024:
        raise ValueError("n cannot exceed 1024 subnets")
    if "/" not in network:
        raise ValueError("network must include a prefix, for example 192.168.1.0/24")
    address, prefix_text = network.rsplit("/", 1)
    info = subnet_info(address, "/" + prefix_text)
    new_prefix = info["prefix"] + (n.bit_length() - 1)
    if new_prefix > 32:
        raise ValueError("requested subnet count exceeds the address space")
    base = _ipv4_int(info["network"])
    block = 1 << (32 - new_prefix)
    return [{"network": _dotted(base + i * block), "prefix": new_prefix,
             "cidr": f"{_dotted(base + i * block)}/{new_prefix}"} for i in range(n)]


def validate_bulk(addresses):
    if not isinstance(addresses, list):
        raise ValueError("addresses must be a list")
    results = []
    for address in addresses:
        result = validate_ipv6(address) if isinstance(address, str) and ":" in address else validate_ipv4(address) if isinstance(address, str) else {"valid": False, "error": "address must be a string"}
        results.append({"ip": address, **result})
    valid_count = sum(item["valid"] for item in results)
    return {"valid_count": valid_count, "invalid_count": len(results) - valid_count, "results": results}


def ip_range(start, end):
    first, last = _ipv4_int(start), _ipv4_int(end)
    if last < first:
        raise ValueError("end address must be greater than or equal to start address")
    count = last - first + 1
    if count > 1024:
        raise ValueError("range cannot exceed 1024 addresses")
    return [_dotted(value) for value in range(first, last + 1)]
