import subprocess
import shutil
import os
import glob

#EXFOL = "/Users/nitto/NNLOJETrelease/examples"
EXFOL = "/home/gstagn/NNLOJETrelease/examples"
RUNFOL = "runcards"

if os.path.exists(RUNFOL):
    shutil.rmtree(RUNFOL, ignore_errors=True)
os.makedirs(RUNFOL, exist_ok=True)


### TODO: read it by running NNLOJET --listprocs
listprocs = ["Z","ZJ","WP","WPJ","WM","WMJ",
             "H","HJ","HTO2P","HTO2PJ","HTO2L1P","HTO2L1PJ",
             "HTO4E","HTO2E2MU","HTO2L2N","HTO4EJ","HTO2E2MUJ","HTO2L2NJ",
             "GJ","GG","JJ","eeJJ","eeJJJ","epLJ","epLJJ",
             "epNJ","epNJJ","epNbJ","epNbJJ"]

rcards = {}
for proc in listprocs:
    rcards[proc] = []
for ff in glob.glob(EXFOL+"/*/*.run"):
    sname = os.path.normpath(ff).split('/')
    Pname = sname[-2]
    Rname = sname[-1]
    print(Pname,Rname)
    rcards[Pname].append(Rname)
    shutil.copyfile(ff,f"{RUNFOL}/{Pname}_{Rname}")

with open("examples.html","w") as ef:
    ef.write("<h2>Examples</h2>")
    ef.write("<p>Here we present example runcards for different processes. The arXiv numbers refer either to NNLOJET publications or to experimental papers.</p>")
    ef.write("<ul>")
    for k,v in rcards.items():
        print(k,v)
        ef.write("<li>")
        ef.write(k)
        ef.write("</li>")
        ef.write("<ul>")
        for r in v:
            ef.write("<li>")
            ef.write(f'<a href="runcards/{k}_{r}">{r}</a>')
            ef.write("</li>")
        ef.write("</ul>")
        # <a href="#">ZJ_1901.11041.run</a> [<a href="https://inspirehep.net/literature/1717885" target="_blank">1901.11041</a>] - <a href="#">ZJ_1901.11041.tar.gz</a> </li>
