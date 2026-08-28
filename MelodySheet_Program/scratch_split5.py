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

def split_tall_regions(regions, active, y_lo, dpi):
    max_sys_h = int(dpi * 2.5)
    final_regions = []
    for a, b in regions:
        if b - a > max_sys_h:
            local_active = active[a - y_lo : b - y_lo]
            local_runs = _runs_from_mask(local_active, int(dpi * 0.15))
            if len(local_runs) >= 2:
                local_gaps = []
                for i in range(len(local_runs) - 1):
                    gap_size = local_runs[i+1][0] - local_runs[i][1]
                    local_gaps.append((gap_size, i))
                
                N = max(2, int(round((b - a) / (dpi * 2.0))))
                num_splits = min(N - 1, len(local_gaps))
                
                local_gaps.sort(reverse=True, key=lambda x: x[0])
                split_indices = [g[1] for g in local_gaps[:num_splits]]
                split_indices.sort()
                
                sub_regions = []
                start_run_idx = 0
                for split_idx in split_indices:
                    sys_a = a + local_runs[start_run_idx][0]
                    sys_b = a + local_runs[split_idx][1]
                    sub_regions.append((sys_a, sys_b))
                    start_run_idx = split_idx + 1
                    
                sys_a = a + local_runs[start_run_idx][0]
                sys_b = a + local_runs[-1][1]
                sub_regions.append((sys_a, sys_b))
                
                final_regions.extend(sub_regions)
            else:
                final_regions.append((a, b))
        else:
            final_regions.append((a, b))
    return final_regions

# Test data
active = np.zeros(2000, dtype=bool)
# Sys 1 Treble 100-200, Bass 250-350
active[100:200] = True
active[250:350] = True
# Sys 2 Treble 430-530, Bass 580-680 (gap Sys1-Sys2 = 80)
active[430:530] = True
active[580:680] = True
# Sys 3 Treble 750-850, Bass 900-1000 (gap Sys2-Sys3 = 70)
active[750:850] = True
active[900:1000] = True

dpi = 200
y_lo = 0
merge_gap = int(dpi * 0.45) # 90
regions = _runs_from_mask(active, merge_gap)
print("Initial:", regions)

final = split_tall_regions(regions, active, y_lo, dpi)
print("Final:", final)

