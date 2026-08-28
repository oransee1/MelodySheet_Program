import cv2
import numpy as np

def _runs_from_mask(mask, merge_gap=0):
    runs = []
    start = None
    for i, val in enumerate(mask):
        if val and start is None:
            start = i
        elif not val and start is not None:
            if not runs:
                runs.append((start, i))
            else:
                prev_start, prev_end = runs[-1]
                if start - prev_end <= merge_gap:
                    runs[-1] = (prev_start, i)
                else:
                    runs.append((start, i))
            start = None
    if start is not None:
        if not runs:
            runs.append((start, len(mask)))
        else:
            prev_start, prev_end = runs[-1]
            if start - prev_end <= merge_gap:
                runs[-1] = (prev_start, len(mask))
            else:
                runs.append((start, len(mask)))
    return runs

def split_large_regions(regions, smooth, dpi, min_h):
    # A single piano system is usually around 1.5 ~ 2.0 dpi.
    # If a region is > 2.6 dpi, it likely contains 2 or more systems.
    max_sys_h = int(dpi * 2.6)
    result = []
    for (a, b) in regions:
        if b - a > max_sys_h:
            # We need to split this region.
            # Find the largest gap(s) inside this region.
            # Actually, we can just use a smaller merge_gap to find sub-regions,
            # and then group them by the largest gaps!
            local_active = smooth[a:b] > 0.018 # some threshold
            # ...
            pass
        else:
            result.append((a, b))
    return result

