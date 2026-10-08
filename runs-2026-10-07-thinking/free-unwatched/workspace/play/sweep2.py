# Board-size sweep: does the plateau / glider peak survive on larger tori?
import os, sys, subprocess, re, time
runs = [(64, 64, 16000, 1000), (128, 128, 2000, 125)]
for w, h, n, chunk in runs:
    for d in [0.05, 0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8]:
        t0 = time.time()
        f = f'/workspace/play/sweep_{w}x{h}_{d}.txt'
        out = open(f).read() if os.path.exists(f) and 'object census' in open(f).read() else subprocess.run([sys.executable, '/workspace/play/census2.py', str(n), '16'],
                             env={**os.environ, 'D': str(d), 'W': str(w), 'H': str(h), 'CHUNK': str(chunk), 'RING': str(16 * w)},
                             capture_output=True, text=True, cwd='/tmp').stdout
        open(f'/workspace/play/sweep_{w}x{h}_{d}.txt', 'w').write(out)
        per = re.search(r'periods: (.*)', out).group(1)
        st = re.search(r'median settle: (\d+).*longest: (\d+)', out)
        objs = re.findall(r'^\s+(\d+)\s+(\S.*)$', out.split('object census:')[1].split('unnamed objects')[0], re.M)
        total = sum(int(c) for c, _ in objs)
        ships = {nm: int(c) for c, nm in objs if nm in ('glider', 'LWSS', 'MWSS', 'HWSS')}
        print(f"{w}x{h} D={d:<4} settle med {st.group(1):>5} max {st.group(2):>5} | obj/soup {total/n:6.2f} | "
              f"obj per 1k cells {1000*total/n/(w*h):5.2f} | gliders/soup {ships.get('glider',0)/n:.3f} | "
              f"other ships {sum(ships.values())-ships.get('glider',0)} | unsettled {re.search(r'-1: (\d+)', per).group(1) if '-1:' in per else 0} | {time.time()-t0:.0f}s", flush=True)
