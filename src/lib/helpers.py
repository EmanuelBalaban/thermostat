def hmac_sha256(key: bytes, message: bytes):
    import uhashlib

    block_size = 64  # Block size for SHA256
    if len(key) > block_size:
        key = uhashlib.sha256(key).digest()
    if len(key) < block_size:
        key += b'\x00' * (block_size - len(key))

    o_key_pad = bytes([k ^ 0x5C for k in key])
    i_key_pad = bytes([k ^ 0x36 for k in key])

    inner = uhashlib.sha256(i_key_pad + message).digest()
    return uhashlib.sha256(o_key_pad + inner).digest()


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


def create_sas_token(resource_uri: str, key: str, expiry=3600) -> str:
    import ubinascii, utime

    encoded_resource_uri = uri_encode(resource_uri)

    # The micropython time uses Jan 1, 2000 as the base, while the rest of the world uses the Unix Epoch
    timestamp = utime.time() + 946684800

    # Create signature
    ttl = int(timestamp + expiry)
    signature_content = f"{encoded_resource_uri}\n{ttl}".encode()
    key_bytes = ubinascii.a2b_base64(key)
    signature = hmac_sha256(key_bytes, signature_content)
    encoded_signature = uri_encode(ubinascii.b2a_base64(signature).strip().decode())

    return ("SharedAccessSignature "
            f"sr={encoded_resource_uri}"
            f"&sig={encoded_signature}"
            f"&se={ttl}")


def uuid() -> str:
    import urandom

    return "{:08x}-{:04x}-{:04x}-{:04x}-{:012x}".format(
        urandom.getrandbits(32),
        urandom.getrandbits(16),
        urandom.getrandbits(16),
        urandom.getrandbits(16),
        (urandom.getrandbits(32) << 16) | urandom.getrandbits(16),
    )
