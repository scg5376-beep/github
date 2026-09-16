import pathlib, re
p = pathlib.Path(__file__).with_name("emphasis.py")
t = p.read_bytes().decode("utf-8")
start = t.index("    holes = []\n    def hole(mm):\n        holes.append(mm.group(0)); return \" ")
end = t.index("def _mark_first_number")
new = '''    holes = []
    def hole(mm):
        holes.append(mm.group(0)); return "\\x00" + str(len(holes) - 1) + "\\x00"
    tmp = re.sub(r"<(q|blockquote|figure|table)\\b[^>]*>.*?</\\1>", hole, html, flags=re.S)   # 인용·그림·표 안의 「」는 원문 그대로
    tmp = _re_bracket.sub(sub, tmp)
    return re.sub(r"\\x00(\\d+)\\x00", lambda mm: holes[int(mm.group(1))], tmp)


'''
t = t[:start] + new + t[end:]
t = t.replace('''    pat = re.compile(r"(<(?:%s)\\b[^>]*>)(.*?)(</(?:%s)>)" % ("|".join(where), "|".join(where)), re.S)''',
              '''    pat = re.compile(r"(<(?:%s)>)(.*?)(</(?:%s)>)" % ("|".join(where), "|".join(where)), re.S)   # 속성 없는 태그만(p.case·p.small 은 제외)''')
p.write_bytes(t.encode("utf-8"))
print("nul" in t, "\x00" in t)
