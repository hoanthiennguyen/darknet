def parse_offset_limit(offset, limit):
    if not limit:
        limit = 10
    else:
        limit = int(limit)
    if not offset:
        offset = 0
    else:
        offset = int(offset)

    if offset < 0:
        offset = 0
    if limit < 0:
        limit = 10
    return offset, limit
