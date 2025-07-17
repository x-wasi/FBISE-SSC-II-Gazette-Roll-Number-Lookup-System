import re
import argparse
from pathlib import Path
import pandas as pd
import pdfplumber

PDF_NAME = "Result-Gazette-SSC-II-Ist-Annual-2025.pdf"
CACHE_DIR = Path(__file__).parent / "data"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_FILE = CACHE_DIR / "results.csv"  # use CSV for streaming

STATUS_TOKENS = ("PASS", "COMPT", "FAIL")
GRADE_TOKENS = {"A1","A","B","C","D","E","F","UF","R","M"}
ROLL_LINE_RE = re.compile(r"^\s*(\d{7})\s+(.+)$")
INST_HINT_WORDS = ("CANTT", "F.G", "F. G", "FG.", "SCHOOL", "COLLEGE")

def parse_roll_line(line):
    m = ROLL_LINE_RE.match(line)
    if not m:
        return None
    roll, body = m.group(1), m.group(2).strip()

    status = ""
    cut = None
    for kw in STATUS_TOKENS:
        pos = body.find(kw)
        if pos != -1 and (cut is None or pos < cut):
            cut = pos
            status = kw

    if cut is None:
        return {"RollNo": roll, "Name": body, "Status": "", "Marks": None, "Grade": ""}

    name = body[:cut].strip()
    rest_tokens = body[cut:].replace(".", "").split()
    status = rest_tokens[0]
    tail = rest_tokens[1:]
    marks = None
    grade = ""
    if status == "PASS" and tail:
        last = tail[-1].upper()
        if last in GRADE_TOKENS:
            grade = last
            if len(tail) >= 2:
                try:
                    marks = int(tail[-2])
                except:
                    marks = None
    return {"RollNo": roll, "Name": name, "Status": status, "Marks": marks, "Grade": grade}

def is_institution_line(line):
    if not line or line[0].isdigit():
        return False
    u = line.upper()
    if not any(word in u for word in INST_HINT_WORDS):
        return False
    return True

def extract_inst_code(line):
    import re
    m = re.search(r"\((\d{3,5})\)", line)
    if m:
        return m.group(1)
    m = re.search(r"(\d{3,5})\s*$", line)
    if m:
        return m.group(1)
    return None

def build_cache():
    pdf_path = Path(__file__).parent / PDF_NAME
    if not pdf_path.exists():
        raise FileNotFoundError(f"{PDF_NAME} not found.")
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()  # remove old file
    current_school = ""
    current_code = None
    with pdfplumber.open(pdf_path) as pdf:
        for pageno, page in enumerate(pdf.pages, start=1):
            rows = []
            text = page.extract_text() or ""
            for raw in text.splitlines():
                line = raw.strip()
                if not line:
                    continue
                if is_institution_line(line):
                    current_school = line
                    current_code = extract_inst_code(line)
                    continue
                rec = parse_roll_line(line)
                if rec:
                    rec["SchoolName"] = current_school
                    rec["SchoolCode"] = current_code
                    rec["PageNo"] = pageno
                    rows.append(rec)
            if rows:
                pd.DataFrame(rows).to_csv(CACHE_FILE, mode="a", index=False, header=not CACHE_FILE.exists())
            print(f"Processed page {pageno}/{len(pdf.pages)}")
    print(f"Saved streaming results to {CACHE_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    build_cache()





# """
# parse_gazette.py
# ----------------
# Heuristically parse the FBISE SSC-II 1st Annual 2025 Gazette PDF into a
# structured table (RollNo, Name, Status, Marks, Grade, SchoolName, SchoolCode, PageNo).

# Expected PDF filename (same directory as this file):
#     Result-Gazette-SSC-II-Ist-Annual-2025.pdf

# Usage:
#     python parse_gazette.py          # build cache if missing
#     python parse_gazette.py --force  # rebuild cache

# The Gazette layout is irregular; parser captures most PASS lines and many
# COMPT/FAIL lines. Marks may be None where not printed.
# """

# import re
# import sys
# import argparse
# from pathlib import Path

# import pandas as pd
# import pdfplumber

# PDF_NAME = "Result-Gazette-SSC-II-Ist-Annual-2025.pdf"
# HERE = Path(__file__).parent
# CACHE_DIR = HERE / "data"
# CACHE_DIR.mkdir(exist_ok=True)
# CACHE_FILE = CACHE_DIR / "results.parquet"

# STATUS_TOKENS = ("PASS", "COMPT", "FAIL")
# GRADE_TOKENS = {"A1", "A", "B", "C", "D", "E", "F", "UF", "R", "M"}

# ROLL_LINE_RE = re.compile(r"^\s*(?P<roll>\d{7})\s+(?P<body>.+)$")


# # ------------------------------------------------------------------
# # Roll Line Parser
# # ------------------------------------------------------------------
# def parse_roll_line(text: str):
#     m = ROLL_LINE_RE.match(text)
#     if not m:
#         return None
#     roll = m.group("roll")
#     body = m.group("body").strip()

#     status = ""
#     cut = None
#     for kw in STATUS_TOKENS:
#         pos = body.find(kw)
#         if pos != -1 and (cut is None or pos < cut):
#             cut = pos
#             status = kw
#     if cut is None:
#         # Not formatted as expected but keep line
#         return {
#             "RollNo": roll,
#             "Name": body,
#             "Status": "",
#             "Marks": None,
#             "Grade": ""
#         }

#     name = body[:cut].strip()
#     rest = body[cut:].strip()

#     rest_tokens = rest.replace(".", "").split()
#     if not rest_tokens:
#         return {
#             "RollNo": roll,
#             "Name": name,
#             "Status": status,
#             "Marks": None,
#             "Grade": ""
#         }

#     status = rest_tokens[0].upper()
#     tail = rest_tokens[1:]

#     marks = None
#     grade = ""
#     if status == "PASS" and tail:
#         last = tail[-1].upper().rstrip(",")
#         if last in GRADE_TOKENS:
#             grade = last
#             if len(tail) >= 2:
#                 try:
#                     marks = int(tail[-2])
#                 except ValueError:
#                     marks = None
#     return {
#         "RollNo": roll,
#         "Name": name,
#         "Status": status,
#         "Marks": marks,
#         "Grade": grade,
#     }


# # ------------------------------------------------------------------
# # Institution Header Detection
# # ------------------------------------------------------------------
# INST_HINT_WORDS = ("CANTT", "F.G", "F. G", "FG.", "SCHOOL", "COLLEGE")


# def is_institution_line(line: str) -> bool:
#     if not line or line[0].isdigit():
#         return False
#     u = line.upper()
#     if not any(h in u for h in INST_HINT_WORDS):
#         return False
#     letters = [c for c in line if c.isalpha()]
#     if not letters:
#         return False
#     uc = sum(1 for c in letters if c.isupper())
#     return (uc / len(letters)) >= 0.5


# def extract_inst_code(line: str):
#     m = re.search(r"\((\d{3,5})\)", line)
#     if m:
#         return m.group(1)
#     m = re.search(r"(\d{3,5})\s*$", line)
#     if m:
#         return m.group(1)
#     return None


# # ------------------------------------------------------------------
# # PDF Parse
# # ------------------------------------------------------------------
# def parse_pdf(pdf_path: Path) -> pd.DataFrame:
#     rows = []
#     current_school = ""
#     current_code = None
#     with pdfplumber.open(pdf_path) as pdf:
#         for pageno, page in enumerate(pdf.pages, start=1):
#             txt = page.extract_text() or ""
#             for raw in txt.splitlines():
#                 line = raw.strip()
#                 if not line:
#                     continue
#                 if is_institution_line(line):
#                     current_school = line
#                     current_code = extract_inst_code(line)
#                     continue
#                 rec = parse_roll_line(line)
#                 if rec:
#                     rec["SchoolName"] = current_school
#                     rec["SchoolCode"] = current_code
#                     rec["PageNo"] = pageno
#                     rows.append(rec)
#     df = pd.DataFrame(rows).drop_duplicates(subset=["RollNo"], keep="first")
#     df["Marks"] = pd.to_numeric(df["Marks"], errors="coerce").astype("Int64")
#     return df


# # ------------------------------------------------------------------
# # Cache Build / Load
# # ------------------------------------------------------------------
# def build_cache(force: bool = False) -> pd.DataFrame:
#     pdf_path = HERE / PDF_NAME
#     if not pdf_path.exists():
#         raise FileNotFoundError(
#             f"{PDF_NAME} not found in {HERE}. Upload the Gazette PDF.")
#     if CACHE_FILE.exists() and not force:
#         return pd.read_parquet(CACHE_FILE)
#     df = parse_pdf(pdf_path)
#     df.to_parquet(CACHE_FILE, index=False)
#     return df


# # ------------------------------------------------------------------
# # CLI
# # ------------------------------------------------------------------
# def main():
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--force",
#                     action="store_true",
#                     help="Rebuild cache even if exists.")
#     args = ap.parse_args()
#     df = build_cache(force=args.force)
#     print(f"Parsed {len(df)} records into {CACHE_FILE}.")


# if __name__ == "__main__":
#     main()
