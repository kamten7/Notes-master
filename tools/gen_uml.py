# -*- coding: utf-8 -*-
"""只读扫描 Java 源码，输出 表1-1 统计 + PlantUML 源与 PNG。

用法（在源码目录的父目录执行）：
    python gen.py <src_dir> <out_dir> [--changed a.java,b.java]
"""
import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

PKG_ROOT = "net.micode.notes"
CORE = ["data", "gtask", "model", "tool", "ui", "widget"]

RE_PKG = re.compile(r"^package\s+([\w.]+)\s*;")
RE_IMP = re.compile(r"^import\s+(?:static\s+)?([\w.]+)\s*;")
RE_CLASS = re.compile(r"^(?:public\s+|final\s+|abstract\s+)*(class|interface|enum)\s+(\w+)"
                      r"(?:\s+extends\s+([\w.<>, ]+?))?(?:\s+implements\s+([\w.<>, ]+?))?\s*\{")
RE_HEAD = re.compile(r"^(?:public\s+|final\s+|abstract\s+)*(class|interface|enum)\s+\w+")
RE_FIELD = re.compile(r"^ {4}(?:(?:public|private|protected|static|final|volatile|transient)\s+)+"
                      r"([\w.<>\[\]]+)\s+(\w+)\s*[;=]")
RE_METHOD = re.compile(r"^ {4}(?:(?:public|private|protected|static|final|abstract|synchronized|native)\s+)+"
                       r"([\w.<>\[\]]+)\s+(\w+)\s*\([^)]*\)\s*\{")
RE_CTOR = re.compile(r"^ {4}(?:public|private|protected)\s+(\w+)\s*\([^)]*\)\s*\{")


def types_of(s):
    if not s:
        return []
    s = re.sub(r"<[^>]*>", "", s)
    return [t.strip().split(".")[-1] for t in s.split(",") if t.strip()]


class JFile:
    def __init__(self, p, root):
        self.rel = p.relative_to(root).as_posix()
        self.text = p.read_text(encoding="utf-8", errors="replace")
        self.lines = self.text.count("\n")
        self.pkg = ""
        self.imports = []
        self.classes = []
        self._parse()

    def _parse(self):
        cur, depth, pending = None, 0, ""
        for raw in self.text.splitlines():
            line = raw.rstrip()
            m = RE_PKG.match(line)
            if m:
                self.pkg = m.group(1)
                continue
            m = RE_IMP.match(line)
            if m:
                self.imports.append(m.group(1))
                continue
            if cur is None:
                cand = (pending + " " + line.strip()).strip() if pending else line
                m = RE_CLASS.match(cand)
                if m:
                    pending = ""
                    cur = {"kind": m.group(1), "name": m.group(2),
                           "ext": types_of(m.group(3)), "impl": types_of(m.group(4)),
                           "fields": [], "methods": []}
                    self.classes.append(cur)
                    depth += cand.count("{") - cand.count("}")
                    if depth <= 0:
                        cur, depth = None, 0
                    continue
                pending = cand if RE_HEAD.match(cand) else ""
                continue
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                cur, depth = None, 0
                continue
            m = RE_FIELD.match(line)
            if m:
                cur["fields"].append((m.group(1), m.group(2)))
                continue
            m = RE_METHOD.match(line)
            if m:
                cur["methods"].append((m.group(1), m.group(2)))
                continue
            m = RE_CTOR.match(line)
            if m and m.group(1) == cur["name"]:
                cur["methods"].append(("ctor", m.group(1)))


def scan(src):
    root = Path(src)
    return [JFile(p, root) for p in sorted(root.rglob("*.java"))]


def core_of(pkg):
    if not pkg.startswith(PKG_ROOT):
        return "其他"
    rest = pkg[len(PKG_ROOT):].strip(".")
    h = rest.split(".")[0] if rest else "根"
    return h if h in CORE else "其他"


def stats(files):
    by = OrderedDict()
    for f in files:
        by.setdefault(f.pkg, []).append(f)
    s = {"files": len(files), "lines": sum(f.lines for f in files),
         "classes": sum(len(f.classes) for f in files),
         "methods": sum(len(c["methods"]) for f in files for c in f.classes),
         "packages": len(by), "by": {}}
    for p, fs in by.items():
        s["by"][p] = {"files": len(fs), "lines": sum(x.lines for x in fs),
                      "classes": sum(len(x.classes) for x in fs),
                      "methods": sum(len(c["methods"]) for x in fs for c in x.classes)}
    return s


def pkg_diagram(files, out):
    pkgs = sorted({f.pkg for f in files})
    alias = {p: p.replace(".", "_") for p in pkgs}
    deps = defaultdict(set)
    for f in files:
        for imp in f.imports:
            if imp.startswith(PKG_ROOT + "."):
                t = imp.rsplit(".", 1)[0]
                if t in alias and t != f.pkg:
                    deps[f.pkg].add(t)
    L = ["@startuml", "skinparam packageStyle rectangle", "skinparam shadowing false",
         "skinparam defaultFontName Microsoft YaHei", "skinparam arrowColor #555555",
         "skinparam packageBorderColor #333333", "left to right direction",
         "title 图 1-1 小米便签体系结构包图（箭头由依赖方指向被依赖方）", ""]
    for p in pkgs:
        L.append(f'package "{p}" as {alias[p]} {{')
        L.append("}")
    L.append("")
    for a, bs in sorted(deps.items()):
        for b in sorted(bs):
            L.append(f"{alias[a]} --> {alias[b]}")
    L += ["@enduml", ""]
    out.write_text("\n".join(L), encoding="utf-8")
    return deps


def cls_diagram(files, core, out, changed=(), title=None, maxf=7, maxm=8):
    sub = [f for f in files if core_of(f.pkg) == core]
    if not sub:
        return 0
    known = {c["name"] for f in sub for c in f.classes}
    L = ["@startuml", "skinparam shadowing false",
         "skinparam defaultFontName Microsoft YaHei",
         "skinparam classAttributeIconSize 0",
         "set separator none",
         "skinparam classBorderColor #333333",
         "skinparam classBackgroundColor #FFFFFF",
         "title " + (title or f"{core} 包类图"), ""]
    by = OrderedDict()
    for f in sub:
        by.setdefault(f.pkg, []).append(f)
    for pkg, fs in by.items():
        L.append(f'package "{pkg}" {{')
        for f in fs:
            hot = Path(f.rel).name in changed
            for c in f.classes:
                kw = {"interface": "interface", "enum": "enum"}.get(c["kind"], "class")
                if hot:
                    L.append(f"  {kw} {c['name']} #FFE0E0 ##C00000 {{")
                else:
                    L.append(f"  {kw} {c['name']} {{")
                for t, n in c["fields"][:maxf]:
                    L.append(f"    - {n}: {t}")
                if len(c["fields"]) > maxf:
                    L.append(f"    - ... 另 {len(c['fields']) - maxf} 个")
                for t, n in c["methods"][:maxm]:
                    L.append(f"    + {n}()" if t == "ctor" else f"    + {n}(): {t}")
                if len(c["methods"]) > maxm:
                    L.append(f"    + ... 另 {len(c['methods']) - maxm} 个")
                L.append("  }")
        L.append("}")
    L.append("")
    for f in sub:
        for c in f.classes:
            for p in c["ext"] + c["impl"]:
                if p in known and p != c["name"]:
                    L.append(f"{p} <|-- {c['name']}")
    L += ["@enduml", ""]
    out.write_text("\n".join(L), encoding="utf-8")
    return len(sub)


def main():
    src, outdir = sys.argv[1], Path(sys.argv[2])
    changed = set()
    if "--changed" in sys.argv:
        changed = {x.strip() for x in sys.argv[sys.argv.index("--changed") + 1].split(",") if x.strip()}
    outdir.mkdir(parents=True, exist_ok=True)
    files = scan(src)
    s = stats(files)
    print(f"files={s['files']} lines={s['lines']} classes={s['classes']} "
          f"methods={s['methods']} packages={s['packages']}")
    for p, v in s["by"].items():
        print(f"  {p}\t{v['files']}\t{v['lines']}\t{v['classes']}\t{v['methods']}")
    pkg_diagram(files, outdir / "01-packages.puml")
    idx = 2
    for core in CORE:
        n = cls_diagram(files, core, outdir / f"{idx:02d}-{core}.puml")
        if n:
            print(f"  diagram {idx:02d}-{core} files={n}")
            idx += 1
    if changed:
        cls_diagram(files, "data", outdir / f"0{idx}-changed-data.puml", changed,
                    "图 4-1 data 包维护后类图（红色为本次改动）")
        cls_diagram(files, "ui", outdir / f"0{idx+1}-changed-ui.puml", changed,
                    "图 4-2 ui 包维护后类图（红色为本次改动）")


if __name__ == "__main__":
    main()
