"""Parse ITviec raw HTML into the Layer-2 data contract.

Extraction rules are grounded in the ITviec HTML pilot:
- JSON-LD JobPosting: title, company, datePosted, jobLocation, baseSalary
- HTML row labelled ``Job Expertise:``: category
- ``section.job-content``: only ``Job description`` and
  ``Your skills and experience`` are kept in jd_text
- job_id is the complete filename/URL slug (never the last 4 digits only)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup

from src.contract import validate_parsed

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CRAWL_LOG = PROJECT_ROOT / "data" / "crawl_log.csv"
OUT_PATH = PROJECT_ROOT / "data" / "interim" / "jobs_parsed.parquet"
ERROR_PATH = PROJECT_ROOT / "reports" / "parse_errors.csv"
ITVIEC_BASE = "https://itviec.com/it-jobs"
TZ = ZoneInfo("Asia/Ho_Chi_Minh")
MIN_PARSE_RATE = 0.90

PARSED_COLUMNS = [
    "job_id",
    "url",
    "title",
    "company",
    "level",
    "location",
    "posted_date",
    "category",
    "salary_raw",
    "jd_text",
    "crawled_at",
]

_LEVEL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Director", re.compile(r"\b(director|chief|cto|cio|ciso)\b", re.I)),
    ("Head", re.compile(r"\bhead\b", re.I)),
    ("Manager", re.compile(r"\bmanager\b", re.I)),
    ("Lead", re.compile(r"\b(lead|leader)\b", re.I)),
    ("Principal", re.compile(r"\bprincipal\b", re.I)),
    ("Senior", re.compile(r"\b(senior|sr\.?|sr-)\b", re.I)),
    ("Middle", re.compile(r"\b(middle|mid(?:dle)?[- ]?level|mid|medior)\b", re.I)),
    ("Junior", re.compile(r"\b(junior|jr\.?|jr-)\b", re.I)),
    ("Fresher", re.compile(r"\bfresher\b", re.I)),
    ("Intern", re.compile(r"\b(intern|internship|trainee)\b|tập\s*sự", re.I)),
]


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def _ascii_fold(value: str) -> str:
    """Remove Vietnamese diacritics for robust title-keyword matching."""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def infer_level(title: str | None) -> str | None:
    """Infer one seniority label from the job title only (ASSUMPTION A17)."""
    if not title:
        return None

    folded = _ascii_fold(title).casefold()
    if re.search(r"\b(tap\s*su|thuc\s*tap(?:\s*sinh)?)\b", folded):
        return "Intern"

    for label, pattern in _LEVEL_PATTERNS:
        if pattern.search(title):
            return label
    return None


def _iter_jsonld_nodes(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _iter_jsonld_nodes(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_jsonld_nodes(item)


def _find_jobposting(soup: BeautifulSoup) -> dict[str, Any] | None:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text(" ", strip=False)
        if not raw or "JobPosting" not in raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for node in _iter_jsonld_nodes(payload):
            node_type = node.get("@type")
            types = node_type if isinstance(node_type, list) else [node_type]
            if "JobPosting" in types:
                return node
    return None


def _title_company_fallback(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    if not soup.title:
        return None, None
    core = _clean_text(soup.title.get_text(" ", strip=True))
    if not core:
        return None, None
    core = re.sub(r"\s*\|\s*ITviec.*$", "", core, flags=re.I).strip()
    if " at " not in core:
        return core, None
    title, company = core.rsplit(" at ", 1)
    return _clean_text(title), _clean_text(company)


def _extract_company(job: dict[str, Any] | None) -> str | None:
    if not job:
        return None
    org = job.get("hiringOrganization")
    if isinstance(org, dict):
        return _clean_text(org.get("name"))
    return None


def _extract_salary_raw(job: dict[str, Any] | None) -> str | None:
    if not job:
        return None
    salary = job.get("baseSalary")
    if not isinstance(salary, dict):
        return _clean_text(salary)
    value = salary.get("value")
    if isinstance(value, dict):
        value = value.get("value")
    return _clean_text(value)


def _extract_location(job: dict[str, Any] | None) -> str | None:
    if not job:
        return None
    locations = job.get("jobLocation")
    if isinstance(locations, dict):
        locations = [locations]
    if not isinstance(locations, list):
        return None

    regions: list[str] = []
    for loc in locations:
        if not isinstance(loc, dict):
            continue
        address = loc.get("address")
        if not isinstance(address, dict):
            continue
        region = _clean_text(address.get("addressRegion"))
        if region and region not in regions:
            regions.append(region)
    return "; ".join(regions) if regions else None


def _extract_category(soup: BeautifulSoup) -> str | None:
    label_re = re.compile(r"^\s*Job\s+Expertise\s*:\s*$", re.I)
    for text_node in soup.find_all(string=label_re):
        label = text_node.parent
        row = label.parent if label else None
        if row is None:
            continue
        values: list[str] = []
        for anchor in row.find_all("a"):
            value = _clean_text(anchor.get_text(" ", strip=True))
            if value and value not in values:
                values.append(value)
        if values:
            return "; ".join(values)
    return None


def _extract_jd_text(soup: BeautifulSoup) -> str | None:
    """Keep only the two approved JD sections, never recommended jobs."""
    job_content = soup.select_one(
        "section.job-content[data-jobs--jd-scroll-target='jobContent']"
    ) or soup.select_one("section.job-content")
    if job_content is None:
        return None

    wanted = {
        "job description": "Job description",
        "your skills and experience": "Your skills and experience",
    }
    parts: list[str] = []

    for heading in job_content.find_all(["h2", "h3"]):
        heading_text = _clean_text(heading.get_text(" ", strip=True))
        if not heading_text:
            continue
        canonical = wanted.get(heading_text.casefold())
        if not canonical:
            continue

        block = heading.parent
        block_text = _clean_text(block.get_text("\n", strip=True)) if block else None
        if not block_text:
            continue
        # Remove the heading once, then add it back in canonical form.
        body = re.sub(
            rf"^{re.escape(heading_text)}\s*",
            "",
            block_text,
            count=1,
            flags=re.I,
        ).strip()
        parts.append(f"{canonical}\n{body}" if body else canonical)

    return "\n\n".join(parts) if parts else None


def parse_html(
    html: str,
    *,
    job_id: str,
    url: str,
    crawled_at: str,
) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    job = _find_jobposting(soup)
    fallback_title, fallback_company = _title_company_fallback(soup)

    title = _clean_text(job.get("title")) if job else None
    title = title or fallback_title
    company = _extract_company(job) or fallback_company
    posted_date = _clean_text(job.get("datePosted")) if job else None
    if posted_date:
        posted_date = posted_date[:10]

    record = {
        "job_id": job_id,
        "url": url,
        "title": title,
        "company": company,
        "level": infer_level(title),
        "location": _extract_location(job),
        "posted_date": posted_date,
        "category": _extract_category(soup),
        "salary_raw": _extract_salary_raw(job),
        "jd_text": _extract_jd_text(soup),
        "crawled_at": crawled_at,
    }

    for required in ("job_id", "url", "title", "company", "jd_text", "crawled_at"):
        if not record.get(required):
            raise ValueError(f"missing required field: {required}")
    return record


def _job_id_from_url(url: str) -> str:
    return Path(urlparse(url).path.rstrip("/")).name


def load_crawl_metadata(path: Path = CRAWL_LOG) -> dict[str, tuple[str, str]]:
    """Map job_id -> (url, crawled_at), keeping the latest successful crawl row."""
    result: dict[str, tuple[str, str]] = {}
    if not path.exists():
        return result

    df = pd.read_csv(path)
    required = {"url", "status", "timestamp"}
    if not required.issubset(df.columns):
        return result

    for row in df.itertuples(index=False):
        url = str(row.url)
        try:
            status = int(row.status)
        except (TypeError, ValueError):
            continue
        if status != 200 or "/it-jobs/" not in url:
            continue
        job_id = _job_id_from_url(url)
        ts = _normalise_timestamp(str(row.timestamp))
        result[job_id] = (url, ts)
    return result


def _normalise_timestamp(value: str) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize(TZ)
    else:
        ts = ts.tz_convert(TZ)
    return ts.isoformat()


def _mtime_as_timestamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=TZ).isoformat()


def parse_file(path: Path, crawl_meta: dict[str, tuple[str, str]]) -> dict[str, Any]:
    job_id = path.stem
    url, crawled_at = crawl_meta.get(
        job_id,
        (f"{ITVIEC_BASE}/{job_id}", _mtime_as_timestamp(path)),
    )
    html = path.read_text(encoding="utf-8", errors="replace")
    return parse_html(html, job_id=job_id, url=url, crawled_at=crawled_at)


def _write_parse_errors(errors: list[dict[str, str]], path: Path = ERROR_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "job_id", "error"])
        writer.writeheader()
        writer.writerows(errors)


def parse_all(
    raw_dir: Path = RAW_DIR,
    crawl_log_path: Path = CRAWL_LOG,
    out_path: Path = OUT_PATH,
    error_path: Path = ERROR_PATH,
) -> pd.DataFrame:
    html_files = sorted(raw_dir.glob("*.html"))
    if not html_files:
        raise FileNotFoundError(f"No raw HTML files found in {raw_dir}")

    crawl_meta = load_crawl_metadata(crawl_log_path)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for path in html_files:
        try:
            rows.append(parse_file(path, crawl_meta))
        except Exception as exc:  # log per-file errors; do not stop whole batch
            errors.append({"file": path.name, "job_id": path.stem, "error": str(exc)})

    _write_parse_errors(errors, error_path)
    success_rate = len(rows) / len(html_files)
    if success_rate < MIN_PARSE_RATE:
        raise RuntimeError(
            f"Parse success rate {success_rate:.1%} is below required {MIN_PARSE_RATE:.0%}. "
            f"See {error_path}."
        )

    df = pd.DataFrame(rows, columns=PARSED_COLUMNS)
    validate_parsed(df)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)

    print(f"Parsed {len(rows)}/{len(html_files)} HTML files ({success_rate:.1%}).")
    print(f"Errors: {len(errors)} -> {error_path}")
    print(f"Output: {out_path}")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse ITviec raw HTML -> Layer-2 parquet")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--crawl-log", type=Path, default=CRAWL_LOG)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    parser.add_argument("--errors", type=Path, default=ERROR_PATH)
    args = parser.parse_args()
    parse_all(args.raw_dir, args.crawl_log, args.out, args.errors)


if __name__ == "__main__":
    main()
