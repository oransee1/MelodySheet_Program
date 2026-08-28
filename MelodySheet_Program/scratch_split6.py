import numpy as np

def _runs_from_mask(active, merge_gap):
    regions = []
    in_run = False
    start = 0
    last_active = -10**9
    for y, on in enumerate(active):
        if on:
            if not in_run:
                if regions and y - last_active <= merge_gap:
                    start = regions.pop()[0]
                else:
                    start = y
                in_run = True
            last_active = y
        elif in_run and (y - last_active) > merge_gap:
            regions.append((start, last_active + 1))
            in_run = False
    if in_run:
        regions.append((start, last_active + 1))
    return regions

def split_tall_regions_by_staves(regions, active, y_lo, dpi):
    max_sys_h = int(dpi * 2.4)
    final_regions = []
    for a, b in regions:
        if b - a > max_sys_h:
            local_active = active[a - y_lo : b - y_lo]
            
            # Use small merge gap to isolate staves
            local_runs = _runs_from_mask(local_active, int(dpi * 0.15))
            
            # Filter out noise/lyrics by minimum height of a staff
            min_staff_h = int(dpi * 0.16)
            staves = [r for r in local_runs if (r[1] - r[0]) >= min_staff_h]
            
            if len(staves) >= 2 and len(staves) % 2 == 0:
                # Group by pairs
                for i in range(0, len(staves), 2):
                    sys_a = a + staves[i][0]
                    sys_b = a + staves[i+1][1]
                    final_regions.append((sys_a, sys_b))
            else:
                # If we couldn't cleanly pair them, fallback to just keeping the original
                final_regions.append((a, b))
        else:
            final_regions.append((a, b))
    return final_regions

# Test data
active = np.zeros(2000, dtype=bool)
# Sys 1 Treble 100-160 (h=60), Bass 250-310 (h=60)
active[100:160] = True
active[250:310] = True

# Noise 380-400 (h=20)
active[380:400] = True

# Sys 2 Treble 450-510, Bass 600-660
active[450:510] = True
active[600:660] = True

dpi = 200 # min_staff_h = 32
y_lo = 0
merge_gap = int(dpi * 0.45) # 90
regions = _runs_from_mask(active, merge_gap)
print("Initial:", regions)

final = split_tall_regions_by_staves(regions, active, y_lo, dpi)
print("Final:", final)

