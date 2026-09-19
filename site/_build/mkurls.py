import json, sys, glob, os, re
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
u = sorted(re.sub(r"(^|/)index\.html$", r"\1", "/" + f.replace(os.sep, "/")) for f in glob.glob("**/*.html", recursive=True) if not f.startswith("_"))   # 파일명 안의 index.html(예: smartplace-help-index.html)은 건드리지 않는다 (B24, 2026-09-19)
json.dump(u, open(sys.argv[1], "w"))
print(len(u), "/why/" in u)
