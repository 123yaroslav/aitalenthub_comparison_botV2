import re, json, time, sys, os, io, sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import httpx
from bs4 import BeautifulSoup
import pdfplumber

# Optional imports for better table extraction
try:
    import camelot
except Exception:
    camelot = None
try:
    import tabula
except Exception:
    tabula = None

from scraper.schema import Plan, Course, Rules

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
NORM = BASE / "data" / "normalized"
RAW.mkdir(parents=True, exist_ok=True)
NORM.mkdir(parents=True, exist_ok=True)

PROGRAM_PAGES = {
    "AI": "https://abit.itmo.ru/program/master/ai",
    "AI Product": "https://abit.itmo.ru/program/master/ai_product",
}

# Fallback direct plan links discovered from official pages
DIRECT_PLAN_PDFS = {
    "AI": "https://api.itmo.su/constructor-ep/api/v1/static/programs/10033/plan/abit/pdf",
    "AI Product": "https://api.itmo.su/constructor-ep/api/v1/static/programs/10130/plan/abit/pdf",
}

HEADERS = {"User-Agent": "itmo-masters-advisor/1.0 (+https://example.org)"}

def resolve_plan_link(html: str) -> Optional[str]:
    # look for a direct /programs/<id>/plan/abit/pdf
    m = re.search(r"/programs/(\d+)/plan/abit/pdf", html)
    if m:
        return f"https://api.itmo.su/constructor-ep/api/v1/static/programs/{m.group(1)}/plan/abit/pdf"
    return None

def fetch(url: str) -> str:
    with httpx.Client(headers=HEADERS, timeout=30) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text

def download(url: str, dest: Path) -> None:
    with httpx.stream("GET", url, headers=HEADERS, timeout=60) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)

def extract_tables_pdf(pdf_path: Path) -> List[Tuple[int, 'pandas.DataFrame']]:
    import pandas as pd
    out = []
    # 1) Camelot (best when lattice/stream works)
    if camelot is not None:
        try:
            tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="lattice")
            for t in tables:
                df = t.df
                out.append((t.page, df))
        except Exception:
            pass
        try:
            tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="stream")
            for t in tables:
                df = t.df
                out.append((t.page, df))
        except Exception:
            pass
    # 2) Tabula
    if not out and tabula is not None:
        try:
            dfs = tabula.read_pdf(str(pdf_path), pages="all", multiple_tables=True)
            for i, df in enumerate(dfs, start=1):
                out.append((i, df))
        except Exception:
            pass
    # 3) Fallback: pdfplumber (extract lines and try to split)
    if not out:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                rows = []
                for line in text.splitlines():
                    # heuristic split by multiple spaces or tabs
                    parts = re.split(r"\s{2,}|\t", line.strip())
                    if len(parts) >= 4:
                        rows.append(parts)
                if rows:
                    out.append((i, pd.DataFrame(rows)))
    return out

def normalize_tables(tables: List[Tuple[int, 'pandas.DataFrame']]) -> List[Course]:
    import pandas as pd
    cols_candidates = [
        ["code", "name", "semester", "ects", "type", "module"],
        ["Код", "Дисциплина", "Семестр", "ЗЕТ", "Тип", "Модуль"],
        ["Наименование", "Сем", "Кредиты", "Тип"],
    ]
    courses: List[Course] = []

    def normalize_type(x: str) -> str:
        x = (x or "").lower()
        if "выбор" in x:
            return "elective"
        return "required"

    for page, df in tables:
        # Clean header row heuristically
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        # Try to guess columns
        name_col = None
        sem_col = None
        ects_col = None
        type_col = None
        module_col = None
        code_col = None

        # Heuristic matching
        for c in df.columns:
            lc = str(c).lower()
            if name_col is None and ("наименование" in lc or "дисцип" in lc or "name" in lc):
                name_col = c
            if sem_col is None and ("сем" in lc or "semester" in lc):
                sem_col = c
            if ects_col is None and ("зет" in lc or "ects" in lc or "кредит" in lc):
                ects_col = c
            if type_col is None and ("тип" in lc or "type" in lc):
                type_col = c
            if module_col is None and ("модул" in lc or "module" in lc):
                module_col = c
            if code_col is None and ("код" in lc or "code" in lc):
                code_col = c

        # If name/ects/semester not found, try row 0 as header
        if name_col is None or ects_col is None or sem_col is None:
            if len(df) > 1:
                header = [str(x).strip() for x in df.iloc[0].tolist()]
                df2 = df.iloc[1:].copy()
                if len(header) == len(df2.columns):
                    df2.columns = header
                    df = df2
                    # retry
                    name_col = next((c for c in df.columns if str(c).lower().startswith("наим") or "дисцип" in str(c).lower()), None)
                    sem_col = next((c for c in df.columns if "сем" in str(c).lower()), None)
                    ects_col = next((c for c in df.columns if "зет" in str(c).lower() or "кредит" in str(c).lower() or "ects" in str(c).lower()), None)
                    type_col = next((c for c in df.columns if "тип" in str(c).lower()), None)
                    module_col = next((c for c in df.columns if "модул" in str(c).lower()), None)
                    code_col = next((c for c in df.columns if "код" in str(c).lower()), None)

        for ridx, row in df.iterrows():
            name = str(row.get(name_col, "")).strip()
            if not name or name.lower().startswith("наименование") or len(name) < 3:
                continue
            try:
                semester = int(str(row.get(sem_col, "1")).strip().split()[0])
            except Exception:
                semester = 1
            try:
                ects = float(str(row.get(ects_col, "0")).replace(",", ".").split()[0])
            except Exception:
                ects = 0.0
            ctype = normalize_type(str(row.get(type_col, "")))
            module = str(row.get(module_col, "")).strip() or "Unknown"
            code = str(row.get(code_col, "")).strip() or None
            source_ref = f"pdf:page={page},row={ridx}"

            course = Course(
                code=code, name=name, semester=semester, ects=ects,
                type=ctype, module=module, prerequisites=[], notes=None,
                source_ref=source_ref
            )
            courses.append(course)
    return courses

def build_rules(courses: List[Course]) -> Rules:
    total = int(round(sum(c.ects for c in courses)))
    per_sem = {}
    for s in sorted(set(c.semester for c in courses)):
        per_sem[str(s)] = {"min": 24, "max": 36}
    # conservative guess for min electives
    min_electives = int(sum(c.ects for c in courses if c.type == "elective") // 2) or 24
    return Rules(total_ects=total or 120, min_electives_ects=min_electives, per_semester_constraints=per_sem)

def save_sqlite(plan: Plan, db_path: Path):
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS courses(program TEXT, version TEXT, name TEXT, semester INT, ects REAL, type TEXT, module TEXT, source_ref TEXT)")
    cur.execute("DELETE FROM courses WHERE program=?", (plan.program,))
    for c in plan.courses:
        cur.execute("INSERT INTO courses VALUES (?,?,?,?,?,?,?,?)", (plan.program, plan.version, c.name, c.semester, c.ects, c.type, c.module, c.source_ref))
    conn.commit()
    conn.close()

def scrape_program(key: str) -> Plan:
    page_url = PROGRAM_PAGES[key]
    print(f"[i] Fetch page: {page_url}")
    html = fetch(page_url)
    link = resolve_plan_link(html)
    if not link:
        link = DIRECT_PLAN_PDFS[key]
    print(f"[i] Plan link resolved: {link}")
    pdf_path = RAW / f"{key.replace(' ', '_')}.pdf"
    download(link, pdf_path)
    print(f"[i] Saved PDF to {pdf_path}")
    tables = extract_tables_pdf(pdf_path)
    courses = normalize_tables(tables)
    version = time.strftime("%Y-%Y", time.gmtime())
    plan = Plan(
        program=key,
        version=version,
        source_url=page_url,
        courses=courses,
        rules=build_rules(courses)
    )
    out_json = NORM / f"{key.replace(' ', '_')}.json"
    out_json.write_text(plan.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[i] Wrote normalized JSON to {out_json}")
    save_sqlite(plan, BASE / "data" / "plans.sqlite")
    return plan

def main():
    plans = []
    for key in ["AI", "AI Product"]:
        try:
            plans.append(scrape_program(key))
        except Exception as e:
            print(f"[!] Failed to scrape {key}: {e}", file=sys.stderr)
    print("[i] Done. Parsed plans:", [p.program for p in plans])

if __name__ == "__main__":
    main()
