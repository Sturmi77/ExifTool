"""Gap finder JSON API and HTML UI."""
from __future__ import annotations

import csv
import io
from collections.abc import Callable
from urllib.parse import quote, urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from src.core.gap_index import GapQuery, editor_parts
from src.core.gap_scanner import GapScanner, ScanInProgress

ScannerFactory = Callable[[], GapScanner]

CSV_FIELDS = [
    "relpath", "root", "has_exif", "has_date", "has_gps", "has_make",
    "datetime", "lat", "lon", "mime", "writable", "scanned_at",
]


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def parse_gap_query(
    missing_exif: str = "",
    missing_date: str = "",
    missing_gps: str = "",
    missing_make: str = "",
    root: str = "",
    prefix: str = "",
    ext: str = "",
    writable: str = "all",
    date_field: str = "exif",
    date_from: str = "",
    date_to: str = "",
    min_count: int = 0,
    min_pct: float = 0,
    page: int = 1,
    per_page: int = 100,
) -> GapQuery:
    return GapQuery(
        missing_exif=_truthy(missing_exif),
        missing_date=_truthy(missing_date),
        missing_gps=_truthy(missing_gps),
        missing_make=_truthy(missing_make),
        root=root.strip(),
        prefix=prefix.strip().strip("/"),
        ext=ext.strip(),
        writable=writable if writable in ("all", "rw", "ro") else "all",
        date_field="file" if date_field == "file" else "exif",
        date_from=date_from.strip(),
        date_to=date_to.strip(),
        min_count=max(0, min_count),
        min_pct=max(0.0, min_pct),
        page=max(1, page),
        per_page=min(max(1, per_page), 500),
    )


def _filter_qs(
    query: GapQuery,
    page: int | None = None,
    prefix: str | None = None,
) -> str:
    data = []
    if query.missing_exif:
        data.append(("missing_exif", "1"))
    if query.missing_date:
        data.append(("missing_date", "1"))
    if query.missing_gps:
        data.append(("missing_gps", "1"))
    if query.missing_make:
        data.append(("missing_make", "1"))
    if query.root:
        data.append(("root", query.root))
    prefix_val = query.prefix if prefix is None else prefix
    if prefix_val:
        data.append(("prefix", prefix_val))
    if query.ext:
        data.append(("ext", query.ext))
    if query.writable != "all":
        data.append(("writable", query.writable))
    if query.date_field != "exif":
        data.append(("date_field", query.date_field))
    if query.date_from:
        data.append(("date_from", query.date_from))
    if query.date_to:
        data.append(("date_to", query.date_to))
    if query.min_count:
        data.append(("min_count", str(query.min_count)))
    if query.min_pct:
        data.append(("min_pct", str(query.min_pct)))
    data.append(("page", str(page if page is not None else query.page)))
    return urlencode(data)


def _enrich_files(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        item = dict(row)
        subdir, name = editor_parts(row["relpath"])
        item["editor_subdir"] = subdir
        item["editor_name"] = name
        item["depth"] = row["relpath"].count("/")
        out.append(item)
    return out


def _enrich_folders(
    rows: list[dict],
    dir_labels: dict[str, str],
    query: GapQuery,
) -> list[dict]:
    out = []
    for row in rows:
        item = dict(row)
        relpath = row["relpath"]
        item["depth"] = 0 if not relpath else relpath.count("/") + 1
        name = "Alle" if not relpath else relpath.rsplit("/", 1)[-1]
        item["label"] = dir_labels.get(name, name)
        item["href"] = "/gaps?" + _filter_qs(query, page=1, prefix=relpath)
        item["editor_href"] = "/?subdir=" + quote(relpath, safe="")
        any_gap = (
            query.missing_exif or query.missing_date
            or query.missing_gps or query.missing_make
        )
        item["show_exif"] = (not any_gap) or query.missing_exif
        item["show_date"] = (not any_gap) or query.missing_date
        item["show_gps"] = (not any_gap) or query.missing_gps
        item["show_make"] = (not any_gap) or query.missing_make
        out.append(item)
    return out


def create_gaps_router(
    get_scanner: ScannerFactory,
    templates: Jinja2Templates,
    dir_labels: dict[str, str] | Callable[[], dict[str, str]],
) -> APIRouter:
    router = APIRouter(prefix="/gaps", tags=["gaps"])

    def _labels() -> dict[str, str]:
        return dir_labels() if callable(dir_labels) else dir_labels

    def _query(
        missing_exif: str = "",
        missing_date: str = "",
        missing_gps: str = "",
        missing_make: str = "",
        root: str = "",
        prefix: str = "",
        ext: str = "",
        writable: str = "all",
        date_field: str = "exif",
        date_from: str = "",
        date_to: str = "",
        min_count: int = 0,
        min_pct: float = 0,
        page: int = 1,
        per_page: int = 100,
    ) -> GapQuery:
        return parse_gap_query(
            missing_exif, missing_date, missing_gps, missing_make,
            root, prefix, ext, writable, date_field, date_from, date_to,
            min_count, min_pct, page, per_page,
        )

    @router.get("", response_class=HTMLResponse)
    @router.get("/", response_class=HTMLResponse)
    def gaps_page(
        request: Request,
        missing_exif: str = "",
        missing_date: str = "",
        missing_gps: str = "",
        missing_make: str = "",
        root: str = "",
        prefix: str = "",
        ext: str = "",
        writable: str = "all",
        date_field: str = "exif",
        date_from: str = "",
        date_to: str = "",
        min_count: int = 0,
        min_pct: float = 0,
        page: int = 1,
    ):
        scanner = get_scanner()
        query = _query(
            missing_exif, missing_date, missing_gps, missing_make,
            root, prefix, ext, writable, date_field, date_from, date_to,
            min_count, min_pct, page,
        )
        files, total = scanner.index.query_files(query)
        folders = scanner.index.list_folders(query)
        pages = max(1, (total + query.per_page - 1) // query.per_page)
        return templates.TemplateResponse(
            request=request,
            name="gaps.html",
            context={
                "query": query,
                "files": _enrich_files(files),
                "folders": _enrich_folders(folders, _labels(), query),
                "total": total,
                "pages": pages,
                "job": scanner.status(),
                "filter_qs": _filter_qs(query),
                "prev_qs": _filter_qs(query, page=max(1, query.page - 1)),
                "next_qs": _filter_qs(query, page=min(pages, query.page + 1)),
                "dir_labels": _labels(),
            },
        )

    @router.get("/status")
    def status():
        return get_scanner().status()

    @router.post("/scan")
    def start_scan():
        try:
            job_id = get_scanner().start()
        except ScanInProgress as exc:
            return JSONResponse({"error": str(exc), "running": True}, status_code=409)
        return {"ok": True, "job_id": job_id, "running": True}

    @router.post("/scan/cancel")
    def cancel_scan():
        cancelled = get_scanner().cancel()
        if not cancelled:
            return JSONResponse(
                {"error": "Kein laufender Scan.", "running": False},
                status_code=409,
            )
        return {"ok": True, "running": True, "status": "cancelling"}

    @router.get("/folders")
    def folders(
        missing_exif: str = "",
        missing_date: str = "",
        missing_gps: str = "",
        missing_make: str = "",
        root: str = "",
        prefix: str = "",
        ext: str = "",
        writable: str = "all",
        date_field: str = "exif",
        date_from: str = "",
        date_to: str = "",
        min_count: int = 0,
        min_pct: float = 0,
    ):
        query = _query(
            missing_exif, missing_date, missing_gps, missing_make,
            root, prefix, ext, writable, date_field, date_from, date_to,
            min_count, min_pct,
        )
        return {"folders": get_scanner().index.list_folders(query)}

    @router.get("/files")
    def files(
        missing_exif: str = "",
        missing_date: str = "",
        missing_gps: str = "",
        missing_make: str = "",
        root: str = "",
        prefix: str = "",
        ext: str = "",
        writable: str = "all",
        date_field: str = "exif",
        date_from: str = "",
        date_to: str = "",
        min_count: int = 0,
        min_pct: float = 0,
        page: int = 1,
        per_page: int = 100,
    ):
        query = _query(
            missing_exif, missing_date, missing_gps, missing_make,
            root, prefix, ext, writable, date_field, date_from, date_to,
            min_count, min_pct, page, per_page,
        )
        rows, total = get_scanner().index.query_files(query)
        return {
            "files": _enrich_files(rows),
            "total": total,
            "page": query.page,
            "per_page": query.per_page,
        }

    @router.get("/export.csv")
    def export_csv(
        missing_exif: str = "",
        missing_date: str = "",
        missing_gps: str = "",
        missing_make: str = "",
        root: str = "",
        prefix: str = "",
        ext: str = "",
        writable: str = "all",
        date_field: str = "exif",
        date_from: str = "",
        date_to: str = "",
        min_count: int = 0,
        min_pct: float = 0,
    ):
        query = _query(
            missing_exif, missing_date, missing_gps, missing_make,
            root, prefix, ext, writable, date_field, date_from, date_to,
            min_count, min_pct,
        )
        def generate():
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)
            for row in get_scanner().index.iter_files(query):
                writer.writerow({key: row.get(key, "") for key in CSV_FIELDS})
                yield buf.getvalue()
                buf.seek(0)
                buf.truncate(0)

        return StreamingResponse(
            generate(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=exif-gaps.csv"},
        )

    return router
