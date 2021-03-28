def parse_offset_limit(offset, limit):
    if not limit:
        limit = 10
    else:
        limit = int(limit)
    if not offset:
        offset = 0
    else:
        offset = int(offset)
    return offset, limit
