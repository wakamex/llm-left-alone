# Density sweep: final population, settle time, period mix, and top objects per density.
import os, sys, subprocess, re
for d in [0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    out = subprocess.run([sys.executable, '/workspace/play/census2.py', '20000', '16'],
                         env={**os.environ, 'D': str(d)}, capture_output=True, text=True, cwd='/tmp').stdout
    open(f'/workspace/play/sweep_{d}.txt', 'w').write(out)
    per = re.search(r'periods: (.*)', out).group(1)
    st = re.search(r'median settle: (\d+).*longest: (\d+)', out)
    objs = re.findall(r'^\s+(\d+)\s+(\S.*)$', out.split('object census:')[1].split('unnamed objects')[0], re.M)
    total = sum(int(c) for c, _ in objs)
    print(f"D={d:<4} median settle {st.group(1):>4}  longest {st.group(2):>5}  objects/soup {total/20000:5.2f}  periods {per}")
    print("        top:", ", ".join(f"{n} {int(c)/total:.0%}" for c, n in objs[:5]), "| ships:",
          ", ".join(f"{n} {c}" for c, n in objs if n in ('glider','LWSS','MWSS','HWSS')) or "none")
