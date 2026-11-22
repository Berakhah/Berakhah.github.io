"""Build the <main> of /resume.html from resume.tex so the site and the PDF share one source.

Usage: python3 make_resume_html.py resume.tex resume.html

Understands the Jake's-style macros used in resume.tex:
  \\resumeSubheading{title}{dates}{org}{place}, \\resumeItem{...}, \\item[] notes,
  a Projects section of \\resumeItem bullets, and a Skills block of \\textbf{Head}{: items} lines.
"""
import html, re, sys

tex_path, html_path = sys.argv[1], sys.argv[2]
tex = open(tex_path, encoding="utf-8").read()
doc = tex[tex.index("\\begin{document}"):tex.index("\\end{document}")]


def braced(s: str, i: int):
    """Return (content, index after closing brace) for the brace group starting at s[i] == '{'."""
    assert s[i] == "{", s[i:i + 30]
    depth, j = 0, i
    while True:
        if s[j] == "\\":
            j += 2
            continue
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1


def args(s: str, i: int, n: int):
    out = []
    for _ in range(n):
        while s[i].isspace():
            i += 1
        a, i = braced(s, i)
        out.append(a)
    return out, i


def clean(s: str) -> str:
    s = s.replace("\\%", "\x00")
    s = re.sub(r"(?<!\\)%.*", "", s).replace("\x00", "%")
    s = s.replace("\\textbullet{}", "·").replace("\\textbullet", "·").replace("\\textbar{}", "|")
    s = s.replace("\\,", " ").replace("\\&", "&").replace("\\#", "#")
    s = s.replace("---", "—").replace("--", "–")
    for _ in range(3):
        s = re.sub(r"\\(?:textbf|textit|underline|small|normalfont)\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\(small|normalfont|vspace\{[^}]*\}|par)\b", "", s)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\s+", " ", s).strip()
    return html.escape(s, quote=False)


def section(name: str) -> str:
    start = doc.index("\\section{%s" % name)
    nxt = doc.find("\\section{", start + 1)
    return doc[start:nxt if nxt != -1 else None]


def items(block: str):
    found, i = [], 0
    while True:
        k = block.find("\\resumeItem{", i)
        if k == -1:
            return found
        (txt,), i = args(block, k + len("\\resumeItem"), 1)
        found.append(txt)


out = []

# Experience
exp = section("Experience")
heads = [m.start() for m in re.finditer(r"\\resumeSubheading\b", exp)]
for n, start in enumerate(heads):
    end = heads[n + 1] if n + 1 < len(heads) else len(exp)
    (title, dates, org, place), after = args(exp, start + len("\\resumeSubheading"), 4)
    body = exp[after:end]
    notes = re.findall(r"\\item\[\]\\small\{(.*?)\}\n", body, re.S)
    pts = items(body)
    out.append(f'<section class="resume-role rv" aria-labelledby="rr{n}">')
    out.append(f'  <div class="resume-role-head"><h2 class="resume-title" id="rr{n}">{clean(title)}</h2>'
               f'<span class="resume-range mono">{clean(dates)}</span></div>')
    out.append(f'  <p class="resume-org">{clean(org)} · {clean(place)}</p>')
    for x in notes:
        out.append(f'  <p class="resume-org">{clean(x)}</p>')
    if pts:
        out.append('  <ul class="bullets resume-points">' + "".join(f"<li>{clean(x)}</li>" for x in pts) + "</ul>")
    out.append("</section>")

# Projects
proj = section("Projects")
intro = re.search(r"\\section\{Projects \\normalfont\\small \((.*?)\)\}", proj).group(1)
links = {"Agent Perimeter": "/work/agent-perimeter.html", "Ledger Sense": "/work/ledger-sense.html",
         "ShopFast": "/work/shopfast-demo.html"}
lis = []
for x in items(proj):
    (name,), rest_i = args(x, x.index("\\textbf") + len("\\textbf"), 1)
    name_c = clean(name)
    href = next((v for k, v in links.items() if name_c.startswith(k)), None)
    label = f'<a href="{href}"><strong>{name_c}</strong></a>' if href else f"<strong>{name_c}</strong>"
    lis.append(f"<li>{label} {clean(x[rest_i:])}</li>")
out.append('<section class="resume-role rv"><h2 class="resume-title">Projects</h2>')
out.append(f'  <p class="resume-org">{clean(intro[0].upper() + intro[1:])}</p>')
out.append('  <ul class="bullets resume-points">' + "".join(lis) + "</ul>\n</section>")

# Skills
sk = section("Skills")
rows = []
for m in re.finditer(r"\\textbf\{", sk):
    (head,), i = args(sk, m.start() + len("\\textbf"), 1)
    if i < len(sk) and sk[i] == "{" and sk[i + 1] == ":":
        (val,), _ = args(sk, i, 1)
        rows.append((head, val[1:]))
runs = "".join(f'<div class="stack-run"><p class="stack-h">{clean(h)}</p><p class="stack-items">{clean(v)}</p></div>'
               for h, v in rows)
out.append(f'<section class="resume-role rv"><h2 class="resume-title">Skills</h2>\n  <div class="stack-runs">{runs}</div>\n</section>')

# Education
ed = section("Education")
k = ed.index("\\resumeSubheading")
(deg, dates, school, place), _ = args(ed, k + len("\\resumeSubheading"), 4)
out.append('<section class="resume-role rv"><h2 class="resume-title">Education</h2>'
           f'<p class="resume-org">{clean(deg)}, {clean(school)}, {clean(place)} · {clean(dates)}</p></section>')

body = "\n".join(out)
page = open(html_path, encoding="utf-8").read()
head_end = page.index('<div class="wrap resume-body">')
main_end = page.index("</main>")
page = (page[:head_end] + '<div class="wrap resume-body">\n<!-- generated from resume.tex by make_resume_html.py; do not edit by hand -->\n'
        + body + "\n</div>\n" + page[main_end:])
open(html_path, "w", encoding="utf-8").write(page)
print("ok", len(body))
