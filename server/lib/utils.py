def uri_encode(s) -> str:
    from ubinascii import hexlify

    encoded = ""
    for char in s:
        ascii_code = ord(char)
        # Check if the character is alphanumeric or one of the unreserved characters
        if (
                (48 <= ascii_code <= 57) or  # 0-9
                (65 <= ascii_code <= 90) or  # A-Z
                (97 <= ascii_code <= 122) or  # a-z
                char in "-_.~"
        ):
            encoded += char
        else:
            encoded += "%" + hexlify(char.encode()).decode().upper()
    return encoded


def timestamp() -> int:
    import utime

    # The micropython time uses Jan 1, 2000 as the base, while the rest of the world uses the Unix Epoch
    return utime.time() + 946684800


def uuid() -> str:
    import urandom

    return "{:08x}-{:04x}-{:04x}-{:04x}-{:012x}".format(
        urandom.getrandbits(32),
        urandom.getrandbits(16),
        urandom.getrandbits(16),
        urandom.getrandbits(16),
        (urandom.getrandbits(32) << 16) | urandom.getrandbits(16),
    )
