import numpy as np

def split_regions(regions, smooth, y_lo, dpi):
    kept_regions = []
    max_sys_h = int(dpi * 2.4)
    for a, b in regions:
        h = b - a
        if h > max_sys_h:
            N = max(2, int(round(h / (dpi * 2.0))))
            local = smooth[a - y_lo : b - y_lo]
            split_points = [0]
            for i in range(1, N):
                expected = int(len(local) * i / N)
                search_radius = int(len(local) * 0.15)
                s0 = max(0, expected - search_radius)
                s1 = min(len(local), expected + search_radius)
                
                split_offset = s0 + int(np.argmin(local[s0:s1]))
                split_points.append(split_offset)
            split_points.append(len(local))
            
            for i in range(N):
                sub_a = a + split_points[i]
                sub_b = a + split_points[i+1]
                kept_regions.append((sub_a, sub_b))
        else:
            kept_regions.append((a, b))
    return kept_regions

# Test data
regions = [(100, 1900)] # A massive merged region of 1800 height (3 systems of 600 each)
dpi = 200 # 2.0 * 200 = 400. N = round(1800 / 400) = round(4.5) = 4 systems? 
# Wait, if 1800, N = 4. 1800 / 4 = 450. 
y_lo = 0
smooth = np.ones(2000)
# Create gaps at 700 and 1300
smooth[690:710] = 0.001
smooth[1290:1310] = 0.001

kept = split_regions(regions, smooth, y_lo, dpi)
print(kept)

