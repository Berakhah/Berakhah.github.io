"""Build the <main> of /resume.html from resume.tex so the site and the PDF share one source.

Usage: python3 make_resume_html.py resume.tex site/resume.html
"""
import html, re, sys

tex_path, html_path = sys.argv[1], sys.argv[2]
tex = open(tex_path, encoding="utf-8").read()
doc = tex[tex.index("% ---------------- Experience"):tex.index("\\end{document}")]


def clean(s: str) -> str:
    s = s.replace("\\%", "\x00")
    s = re.sub(r"%.*", "", s).replace("\x00", "%")
    s = s.replace("\\sep", "·").replace("\\,", " ").replace("\\%", "%").replace("\\&", "&")
    s = s.replace("--", "–").replace("$\\kappa$", "κ").replace("\\\\[1pt]", "").replace("\\\\", "")
    s = re.sub(r"\\textbf\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\(small|vspace\{[^}]*\}|par)\b", "", s)
    s = re.sub(r"\s+", " ", s).strip(" {}")
    return html.escape(s, quote=False)


def section(name: str) -> str:
    start = doc.index("\\section{%s}" % name)
    nxt = doc.find("\\section{", start + 1)
    return doc[start + len(name) + 10: nxt if nxt != -1 else None]


out = []
# Experience
exp = section("Experience")
roles = re.split(r"(?=\\role\{)", exp)[1:]
for i, r in enumerate(roles):
    title, dates, org = re.match(r"\\role\{(.*?)\}\{(.*?)\}\{(.*?)\}", r, re.S).groups()
    notes = re.findall(r"\\note\{(.*?)\}\n", r, re.S)
    items = re.findall(r"\\item (.*?)(?=\\item|\\end\{itemize\})", r, re.S)
    out.append(f'<section class="resume-role rv" aria-labelledby="rr{i}">')
    out.append(f'  <div class="resume-role-head"><h2 class="resume-title" id="rr{i}">{clean(title)}</h2>'
               f'<span class="resume-range mono">{clean(dates)}</span></div>')
    out.append(f'  <p class="resume-org">{clean(org)}</p>')
    for n in notes:
        out.append(f'  <p class="resume-org">{clean(n)}</p>')
    if items:
        out.append('  <ul class="bullets resume-points">' + "".join(f"<li>{clean(x)}</li>" for x in items) + "</ul>")
    out.append("</section>")

# Projects
proj = section("Projects")
intro = re.search(r"\{\\small (.*?)\}\n\\begin", proj, re.S).group(1)
items = re.findall(r"\\item (.*?)(?=\\item|\\end\{itemize\})", proj, re.S)
links = {"ShopFast sample audit": "/work/shopfast-demo.html", "Agent Perimeter": "/work/agent-perimeter.html",
         "Ledger Sense": "/work/ledger-sense.html"}
lis = []
for x in items:
    name = re.match(r"\\textbf\{(.*?)\}", x).group(1)
    rest = clean(x[len(name) + 9:])
    lis.append(f'<li><a href="{links[name]}"><strong>{clean(name)}</strong></a> {rest}</li>')
out.append('<section class="resume-role rv"><h2 class="resume-title">Projects</h2>')
out.append(f'  <p class="resume-org">{clean(intro)}</p>')
out.append('  <ul class="bullets resume-points">' + "".join(lis) + "</ul>\n</section>")

# Skills
sk = section("Skills")
rows = re.findall(r"\\textbf\{(.*?)\} & (.*?)\\\\", sk, re.S)
runs = "".join(f'<div class="stack-run"><p class="stack-h">{clean(h)}</p><p class="stack-items">{clean(v)}</p></div>'
               for h, v in rows)
out.append(f'<section class="resume-role rv"><h2 class="resume-title">Skills</h2>\n  <div class="stack-runs">{runs}</div>\n</section>')

# Education
ed = section("Education")
deg = re.search(r"\\textbf\{(.*?)\}(.*?)\\hfill\{\\small (.*?)\}", ed, re.S)
note = re.search(r"\{\\small (Part-time.*?)\}\n", ed, re.S).group(1)
out.append('<section class="resume-role rv"><h2 class="resume-title">Education</h2>'
           f'<p class="resume-org">{clean(deg.group(1))}{clean(deg.group(2))} · {clean(deg.group(3))}</p>'
           f'<p class="resume-org">{clean(note)}</p></section>')

body = "\n".join(out)
page = open(html_path, encoding="utf-8").read()
head_end = page.index('<div class="wrap resume-body">')
main_end = page.index("</main>")
page = page[:head_end] + '<div class="wrap resume-body">\n<!-- generated from resume.tex by make_resume_html.py; do not edit by hand -->\n' + body + "\n</div>\n" + page[main_end:]
open(html_path, "w", encoding="utf-8").write(page)
print("ok", len(body))
