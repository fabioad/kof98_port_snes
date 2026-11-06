"""Repack long, linear IT songs for SNESMOD's 64-entry pattern table.

Keep source assets intact. Join pairs of patterns into <=128-row patterns;
expand IT mask reuse so the new boundaries never inherit stale mask caches.
Instrument/sample offsets and payloads stay byte-for-byte in place.
"""
import struct

MAX_PATTERNS = 64


def layout(data):
    if data[:4] != b'IMPM':
        raise ValueError('not an Impulse Tracker module')
    orders, instruments, samples, patterns = struct.unpack_from('<4H', data, 32)
    offset = 192 + orders + 4 * (instruments + samples)
    pointers = struct.unpack_from(f'<{patterns}I', data, offset)
    return orders, instruments, samples, pointers


def decode_pattern(data, pointer):
    if not pointer:
        return [[] for _ in range(64)]
    length, count = struct.unpack_from('<HH', data, pointer)
    packed = data[pointer+8:pointer+8+length]
    masks, previous = [0]*64, [[0, 0, 0, (0, 0)] for _ in range(64)]
    rows, events, offset = [], [], 0
    while offset < len(packed):
        channel = packed[offset]; offset += 1
        if channel == 0:
            rows.append(events); events = []
            continue
        index = (channel-1) & 63
        if channel & 128:
            masks[index] = packed[offset]; offset += 1
        mask = masks[index]
        values = [None]*4
        for field in range(4):
            if mask & (1 << field):
                size = 2 if field == 3 else 1
                value = tuple(packed[offset:offset+2]) if size == 2 else packed[offset]
                offset += size
                previous[index][field] = value
                values[field] = value
            elif mask & (16 << field):
                values[field] = previous[index][field]
        events.append((index, tuple(values)))
    if events or len(rows) != count:
        raise ValueError('invalid IT pattern row count')
    return rows


def encode_pattern(rows):
    packed = bytearray()
    masks = [None]*64
    previous = [[0, 0, 0, (0, 0)] for _ in range(64)]
    for events in rows:
        for channel, values in events:
            mask = 0
            payload = bytearray()
            for field, value in enumerate(values):
                if value is not None:
                    if value == previous[channel][field]:
                        mask |= 16 << field
                    else:
                        mask |= 1 << field
                        payload.extend(value if field == 3 else (value,))
                        previous[channel][field] = value
            if mask != masks[channel]:
                packed.extend((128 | (channel+1), mask))
                masks[channel] = mask
            else:
                packed.append(channel+1)
            packed.extend(payload)
        packed.append(0)
    return struct.pack('<HHI', len(packed), len(rows), 0) + packed


def fit_snesmod(data):
    orders, instruments, samples, pointers = layout(data)
    if len(pointers) <= MAX_PATTERNS:
        return data
    sequence = list(data[192:192+orders])
    if sequence != list(range(len(pointers))) + [255]:
        raise ValueError('long IT song must have a linear order list')
    decoded = [decode_pattern(data, pointer) for pointer in pointers]
    for rows in decoded:
        for events in rows:
            for _channel, values in events:
                effect = values[3]
                if effect and (effect[0] in (2, 3) or
                               effect[0] == 19 and effect[1] >> 4 == 11):
                    raise ValueError('pattern flow commands require explicit remapping')
    joined = []
    for index in range(0, len(decoded), 2):
        rows = sum(decoded[index:index+2], [])
        if len(rows) > 128:
            raise ValueError('joined pattern exceeds SNESMOD row limit')
        joined.append(rows)
    if len(joined) > MAX_PATTERNS:
        raise ValueError('song still exceeds SNESMOD pattern limit')
    result = bytearray(data)
    new_orders = bytes(range(len(joined))) + b'\xff'
    struct.pack_into('<H', result, 32, len(new_orders))
    struct.pack_into('<H', result, 38, len(joined))
    sample_tables = data[192+orders:192+orders+4*(instruments+samples)]
    table = 192 + len(new_orders) + len(sample_tables)
    result[192:table] = new_orders + sample_tables
    for index, rows in enumerate(joined):
        pointer = len(result)
        result.extend(encode_pattern(rows))
        struct.pack_into('<I', result, table+4*index, pointer)
    return bytes(result)
