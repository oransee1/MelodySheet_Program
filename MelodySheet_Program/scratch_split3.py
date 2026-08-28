import numpy as np

def split_recursive(a, b, smooth, y_lo, min_h, max_sys_h):
    if b - a <= max_sys_h:
        return [(a, b)]
    local = smooth[a - y_lo : b - y_lo]
    mid0, mid1 = int(len(local) * 0.3), int(len(local) * 0.7)
    if mid1 > mid0:
        split = mid0 + int(np.argmin(local[mid0:mid1]))
        if split < min_h or (len(local) - split) < min_h:
            return [(a, b)]
        return split_recursive(a, a + split, smooth, y_lo, min_h, max_sys_h) + \
               split_recursive(a + split, b, smooth, y_lo, min_h, max_sys_h)
    return [(a, b)]

regions = [(100, 1900)]
smooth = np.ones(2000)
smooth[690:710] = 0.001
smooth[1290:1310] = 0.001

dpi = 200
y_lo = 0
min_h = int(dpi * 0.80)
max_sys_h = int(dpi * 2.4) # 480

print(split_recursive(100, 1900, smooth, y_lo, min_h, max_sys_h))

