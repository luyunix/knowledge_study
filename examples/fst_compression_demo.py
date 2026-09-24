"""Hand-built FST and lossless integer encodings; not a Lucene codec."""

from itertools import accumulate
import random


# The same four states and additive outputs shown in the diagram.
ARCS = {0: {"b": (1, 20), "c": (1, 10)},
        1: {"a": (2, 0)},
        2: {"r": (3, 0), "t": (3, 1)},
        3: {}}
FINALS = {3: 0}


def fst_lookup(word):
    state, output = 0, 0
    for char in word:
        if char not in ARCS[state]:
            return None
        state, arc_output = ARCS[state][char]
        output += arc_output
    return output + FINALS[state] if state in FINALS else None


def encode_vint(value):
    if not 0 <= value <= 0x7FFFFFFF:
        raise ValueError("This demo accepts nonnegative signed-32-bit values only")
    result = bytearray()
    while value >= 128:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value)
    return bytes(result)


def decode_vint(data, offset=0):
    value, shift = 0, 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            if value > 0x7FFFFFFF:
                raise ValueError("Overflow")
            return value, offset
        shift += 7
        if shift >= 35:
            raise ValueError("Too many bytes")
    raise ValueError("Truncated VInt")


def pack_bits(values, width):
    if width < 1 or any(v < 0 or v >= (1 << width) for v in values):
        raise ValueError("Values must fit the positive bit width")
    # MSB-first pedagogical format; pad only at the end.
    bits = ''.join(f'{v:0{width}b}' for v in values)
    bits += '0' * ((-len(bits)) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def unpack_bits(data, width, count):
    if width < 1 or count < 0 or width * count > len(data) * 8:
        raise ValueError("Invalid width, count, or insufficient data")
    bits = ''.join(f'{byte:08b}' for byte in data)
    return [int(bits[i * width:(i + 1) * width], 2) for i in range(count)]


def patch_restore(low, exceptions, width):
    restored = list(low)
    for index, high in exceptions.items():
        restored[index] += high << width
    return restored


def main():
    expected = {"bar": 20, "bat": 21, "car": 10, "cat": 11}
    assert {word: fst_lookup(word) for word in expected} == expected
    assert all(fst_lookup(word) is None for word in ["", "b", "ba", "ca", "cab", "cats"])
    print("FST: " + ', '.join(f'{w}={v}' for w, v in expected.items()))

    data = encode_vint(300)
    assert data == bytes.fromhex('ac 02')
    assert decode_vint(data) == (300, 2)
    print("VInt 300:", data.hex(' '), "->", decode_vint(data)[0])
    assert len(encode_vint(127)) == 1 and len(encode_vint(128)) == 2
    assert len(encode_vint(0x7FFFFFFF)) == 5

    gaps = [3, 7, 1, 9]
    packed = pack_bits(gaps, 4)
    assert packed == bytes.fromhex('37 19')
    assert unpack_bits(packed, 4, 4) == gaps
    doc_ids = list(accumulate(gaps))
    assert doc_ids == [3, 10, 11, 20]
    print("Packed", gaps, ':', packed.hex(' '), '->', unpack_bits(packed, 4, 4))
    print("Recovered docIDs:", doc_ids)

    values, width = [3, 7, 1, 129], 3
    low = [v & ((1 << width) - 1) for v in values]
    exceptions = {i: v >> width for i, v in enumerate(values) if v >> width}
    assert low == [3, 7, 1, 1] and exceptions == {3: 16}
    assert patch_restore(low, exceptions, width) == values
    print("Patched:", patch_restore(low, exceptions, width))

    rng = random.Random(2026)
    samples = [0, 1, 127, 128, 300, 16383, 16384, 0x7FFFFFFF]
    samples += [rng.randrange(0x80000000) for _ in range(1000)]
    stream = b''.join(encode_vint(v) for v in samples)
    offset = 0
    for expected_value in samples:
        decoded, offset = decode_vint(stream, offset)
        assert decoded == expected_value
    assert offset == len(stream)
    for width in range(1, 17):
        for count in [0, 1, 3, 4, 17, 128]:
            values = [rng.randrange(1 << width) for _ in range(count)]
            assert unpack_bits(pack_bits(values, width), width, count) == values
    for invalid in [b'', b'\x80', b'\x80' * 6]:
        try:
            decode_vint(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Malformed VInt accepted")
    print("FST、边界值、连续整数流及 96 组位打包往返检查通过。")


if __name__ == '__main__':
    main()
