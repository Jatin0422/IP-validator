"""Pure IPv4/IPv6 validation and IPv4 subnet calculations."""


def validate_ipv4(s):
    if any(ch.isspace() for ch in s):
        return {"valid": False, "error": "whitespace is not allowed"}
    octets = s.split(".")
    if len(octets) != 4:
        return {"valid": False, "error": "wrong octet count"}
    for octet in octets:
        if not octet:
            return {"valid": False, "error": "empty octet"}
        if not all("0" <= ch <= "9" for ch in octet):
            return {"valid": False, "error": "non-digit octet"}
        if len(octet) > 1 and octet[0] == "0":
            return {"valid": False, "error": "leading zero"}
        if int(octet) > 255:
            return {"valid": False, "error": "octet >255"}
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
        groups = ([g for g in left.split(":") if g] +
                  [g for g in right.split(":") if g])
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
