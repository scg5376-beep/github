import json, sys, glob, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
u = sorted("/" + f.replace(os.sep, "/").replace("index.html", "") for f in glob.glob("**/*.html", recursive=True) if not f.startswith("_"))
json.dump(u, open(sys.argv[1], "w"))
print(len(u), "/why/" in u)
