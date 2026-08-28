def _runs_from_mask(active, merge_gap: int, max_h: int = 1000000):
    regions = []
    in_run = False
    start = 0
    last_active = -10**9
    for y, on in enumerate(active):
        if on:
            if not in_run:
                if regions and y - last_active <= merge_gap and (y - regions[-1][0]) <= max_h:
                    start = regions.pop()[0]
                else:
                    start = y
                in_run = True
            last_active = y
            
            # 연속된 잉크가 비정상적으로 길면 강제로 끊어서 단 병합을 방지
            if in_run and (y - start) >= max_h:
                regions.append((start, y))
                in_run = False
                
        elif in_run and (y - last_active) > merge_gap:
            regions.append((start, last_active + 1))
            in_run = False
            
    if in_run:
        regions.append((start, last_active + 1))
    return regions

# Test
# Create a dummy active array
active = [False]*1000
# System 1: 100 to 200 (Treble), 250 to 350 (Bass)
for i in range(100, 201): active[i] = True
for i in range(250, 351): active[i] = True

# Noise between System 1 and System 2
for i in range(380, 420): active[i] = True

# System 2: 450 to 550 (Treble), 600 to 700 (Bass)
for i in range(450, 551): active[i] = True
for i in range(600, 701): active[i] = True

dpi = 200
merge_gap = int(dpi * 0.45) # 90
max_sys_h = int(dpi * 2.3)  # 460

regions1 = _runs_from_mask(active, merge_gap)
regions2 = _runs_from_mask(active, merge_gap, max_sys_h)

print("Without max_h:", regions1)
print("With max_h:", regions2)

