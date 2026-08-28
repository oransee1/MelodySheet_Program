import numpy as np

def split_regions(regions, smooth, y_lo, dpi):
    kept_regions = []
    max_sys_h = int(dpi * 2.8) # increased to prevent splitting a single tall system
    for a, b in regions:
        h = b - a
        if h > max_sys_h:
            N = max(2, int(round(h / (dpi * 2.0))))
            local = smooth[a - y_lo : b - y_lo]
            split_points = [0]
            for i in range(1, N):
                expected = int(len(local) * i / N)
                # Search range: +/- 12% to find the gap
                search_radius = int(len(local) * 0.12)
                s0 = max(0, expected - search_radius)
                s1 = min(len(local), expected + search_radius)
                
                # We need the global minimum in this range.
                if s1 > s0:
                    split_offset = s0 + int(np.argmin(local[s0:s1]))
                else:
                    split_offset = expected
                split_points.append(split_offset)
            split_points.append(len(local))
            
            for i in range(N):
                sub_a = a + split_points[i]
                sub_b = a + split_points[i+1]
                kept_regions.append((sub_a, sub_b))
        else:
            kept_regions.append((a, b))
    return kept_regions

regions = [(100, 1900)]
smooth = np.ones(2000)
smooth[690:710] = 0.001
smooth[1290:1310] = 0.001
y_lo = 0
dpi = 200

print(split_regions(regions, smooth, y_lo, dpi))

