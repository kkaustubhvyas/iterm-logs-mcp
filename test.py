def add(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket

add(1)
print(add(2))

import copy
from itertools import count
grid = [[0, 0], [0, 0]]
shallow = copy.copy(grid)
deep = copy.deepcopy(grid)
grid[0][0] = 9
print(shallow[0][0])
print(deep[0][0]) 




logs = [
    "192.168.1.5 - BLOCKED",
    "10.0.0.2 - ALLOWED",
    "192.168.1.5 - BLOCKED",
    "10.0.0.9 - BLOCKED",
    "10.0.0.2 - BLOCKED",
    "192.168.1.5 - ALLOWED",
]
# print(top_ips(logs))
# [('192.168.1.5', 3), ('10.0.0.2', 2), ('10.0.0.9', 1)]


print(count(10))