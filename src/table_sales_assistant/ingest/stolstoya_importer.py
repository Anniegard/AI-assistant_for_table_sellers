from __future__ import annotations

import argparse
import hashlib
import json
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from table_sales_assistant.ingest.normalize import (
    classify_category,
    detect_tabletop_material,
    parse_dimensions_cm,
    parse_height_range_cm,
    parse_lifting_capacity_kg,
    parse_motors_count,
    parse_price_rub,
)
from table_sales_assistant.storage.sqlite import connect_sqlite, ensure_sqlite_schema

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 AI-assistant-demo-importer/1.0"
)


@dataclass(slots=True)
class ImportArgs:
    db_path: Path
    max_pages: int
    delay: float
    dry_run: bool
    refresh_cache: bool
    no_cache: bool
    source_base_url: str


def _parse_cli_args() -> ImportArgs:
    parser = argparse.ArgumentParser(
        description="Import StolStoya public demo data into local SQLite"
    )
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--max-pages", type=int, default=50)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--source-base-url", default="https://stolstoya.ru/")
    args = parser.parse_args()
    return ImportArgs(
        db_path=args.db_path,
        max_pages=args.max_pages,
        delay=args.delay,
        dry_run=args.dry_run,
        refresh_cache=args.refresh_cache,
        no_cache=args.no_cache,
        source_base_url=args.source_base_url,
    )


def _now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def _safe_cache_name(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest() + ".html"


def _extract_summary(text: str, max_sentences: int = 2) -> str:
    parts = [part.strip() for part in text.replace("\n", " ").split(".") if part.strip()]
    return ". ".join(parts[:max_sentences]) + ("." if parts else "")


def _classify_doc_type(url: str, title: str, text: str) -> str:
    haystack = f"{url} {title} {text}".lower()
    if any(token in haystack for token in ("faq", "вопрос", "ответ")):
        return "faq"
    if any(token in haystack for token in ("доставк", "оплат")):
        return "delivery"
    if "гарант" in haystack:
        return "warranty"
    if any(token in haystack for token in ("материал", "лдсп", "мдф", "шпон", "массив")):
        return "material"
    if any(token in haystack for token in ("сборк", "инструкц")):
        return "assembly"
    if any(token in haystack for token in ("blog", "блог", "статья")):
        return "article"
    return "other"


def _extract_links(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not href or href.startswith("#"):
            continue
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.netloc and "stolstoya.ru" not in parsed.netloc:
            continue
        image_exts = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg")
        if any(parsed.path.lower().endswith(ext) for ext in image_exts):
            continue
        normalized = full.split("#")[0]
        parsed_normalized = urlparse(normalized)
        path = (parsed_normalized.path or "/").lower()
        allowed_roots = (
            "/catalog",
            "/blog",
            "/faq",
            "/delivery",
            "/payment",
            "/warranty",
            "/garanti",
            "/assembly",
            "/material",
            "/articles",
        )
        if path == "/" or path.startswith(allowed_roots):
            links.append(normalized)
    return sorted(set(links))


def _extract_text_content(soup: BeautifulSoup) -> str:
    node = soup.select_one("main") or soup.body or soup
    return " ".join(node.get_text(separator=" ", strip=True).split())


def _extract_breadcrumbs(soup: BeautifulSoup) -> str:
    crumbs = [el.get_text(" ", strip=True) for el in soup.select(".breadcrumb a, .breadcrumbs a")]
    return " / ".join([item for item in crumbs if item])


def _parse_product(url: str, html: str) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.select_one("h1") or soup.select_one("title"))
    title_text = title.get_text(" ", strip=True) if title else "Untitled"
    text = _extract_text_content(soup)
    breadcrumbs = _extract_breadcrumbs(soup)
    category = classify_category(url=url, title=title_text, breadcrumbs=breadcrumbs, text=text)
    price_text = ""
    price_node = soup.select_one(".price, .product-price, [itemprop='price']")
    if price_node:
        price_text = price_node.get_text(" ", strip=True)
    else:
        for line in text.split():
            if "₽" in line or "руб" in line:
                price_text = line
                break
    min_height, max_height = parse_height_range_cm(text)
    width, depth = parse_dimensions_cm(text)
    item_id = hashlib.md5(url.encode("utf-8")).hexdigest()[:16]
    return {
        "id": f"stolstoya-{item_id}",
        "source": "stolstoya",
        "source_url": url,
        "source_product_id": None,
        "name": title_text,
        "category": category,
        "subtype": None,
        "price_rub": parse_price_rub(price_text),
        "min_height_cm": min_height,
        "max_height_cm": max_height,
        "width_cm": width,
        "depth_cm": depth,
        "motors_count": parse_motors_count(text),
        "lifting_capacity_kg": parse_lifting_capacity_kg(text),
        "tabletop_material": detect_tabletop_material(text),
        "description_short": _extract_summary(text, max_sentences=1),
        "availability": "in_stock",
        "raw_payload_json": json.dumps({"title": title_text}, ensure_ascii=False),
    }


def _parse_knowledge(url: str, html: str) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.select_one("h1") or soup.select_one("title"))
    title_text = title.get_text(" ", strip=True) if title else "Untitled"
    content = _extract_text_content(soup)
    doc_type = _classify_doc_type(url, title_text, content)
    tag_candidates = []
    for token in ("гарантия", "доставка", "сборка", "мотор", "высота", "нагрузка", "материал"):
        if token in content.lower():
            tag_candidates.append(token)
    doc_id = hashlib.md5(url.encode("utf-8")).hexdigest()[:16]
    return {
        "id": f"stolstoya-doc-{doc_id}",
        "source": "stolstoya",
        "source_url": url,
        "title": title_text,
        "doc_type": doc_type,
        "content": content,
        "summary": _extract_summary(content),
        "tags_json": json.dumps(tag_candidates, ensure_ascii=False),
    }


def _is_knowledge_page(url: str, title: str, text: str) -> bool:
    haystack = f"{url} {title} {text}".lower()
    return any(
        token in haystack
        for token in (
            "faq",
            "блог",
            "статья",
            "доставка",
            "оплата",
            "гарантия",
            "сборка",
            "материал",
        )
    )


def _is_catalog_like(url: str, title: str, text: str) -> bool:
    haystack = f"{url} {title} {text}".lower()
    return any(
        token in haystack
        for token in ("catalog", "каталог", "подстоль", "столеш", "аксессуар", "кресл", "стол")
    )


def _is_product_page(url: str, title: str, text: str) -> bool:
    haystack = f"{url} {title} {text}".lower()
    has_product_markers = any(
        token in haystack
        for token in (
            "цена",
            "руб",
            "₽",
            "характерист",
            "грузоподъем",
            "мотор",
            "размер",
            "столешниц",
        )
    )
    path = urlparse(url).path.lower().strip("/")
    slug_depth = len([part for part in path.split("/") if part]) >= 2
    return has_product_markers and slug_depth


def _insert_records(
    db_path: Path,
    schema_path: Path,
    products: list[dict[str, object]],
    knowledge_docs: list[dict[str, object]],
    source_pages: list[dict[str, object]],
    run_id: str,
    errors: list[str],
) -> None:
    with connect_sqlite(db_path) as connection:
        ensure_sqlite_schema(connection, schema_path)
        now = _now_iso()
        connection.execute(
            """
            INSERT OR REPLACE INTO import_runs
            (
                id, source, started_at, finished_at, status,
                products_count, knowledge_count, errors_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                "stolstoya",
                now,
                now,
                "success" if not errors else "partial",
                len(products),
                len(knowledge_docs),
                json.dumps(errors, ensure_ascii=False),
            ),
        )
        for row in products:
            connection.execute(
                """
                INSERT OR REPLACE INTO products (
                    id, source, source_url, source_product_id, name, category, subtype, price_rub,
                    min_height_cm, max_height_cm, width_cm, depth_cm,
                    motors_count, lifting_capacity_kg,
                    tabletop_material, description_short, availability, raw_payload_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["source"],
                    row["source_url"],
                    row["source_product_id"],
                    row["name"],
                    row["category"],
                    row["subtype"],
                    row["price_rub"],
                    row["min_height_cm"],
                    row["max_height_cm"],
                    row["width_cm"],
                    row["depth_cm"],
                    row["motors_count"],
                    row["lifting_capacity_kg"],
                    row["tabletop_material"],
                    row["description_short"],
                    row["availability"],
                    row["raw_payload_json"],
                    now,
                ),
            )
        for row in knowledge_docs:
            connection.execute(
                """
                INSERT OR REPLACE INTO knowledge_documents
                (id, source, source_url, title, doc_type, content, summary, tags_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["source"],
                    row["source_url"],
                    row["title"],
                    row["doc_type"],
                    row["content"],
                    row["summary"],
                    row["tags_json"],
                    now,
                ),
            )
        for row in source_pages:
            connection.execute(
                """
                INSERT OR REPLACE INTO source_pages
                (id, source, url, page_type, fetched_at, status_code, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["source"],
                    row["url"],
                    row["page_type"],
                    row["fetched_at"],
                    row["status_code"],
                    row["content_hash"],
                ),
            )
        connection.commit()


def _print_report(
    products: list[dict[str, object]],
    knowledge_docs: list[dict[str, object]],
) -> None:
    product_counts = Counter(product.get("category") or "unknown" for product in products)
    knowledge_counts = Counter(doc.get("doc_type") or "other" for doc in knowledge_docs)
    print("Imported products:")
    for category in ("adjustable_desk", "frame", "tabletop", "accessory", "chair", "unknown"):
        print(f"- {category}: {product_counts.get(category, 0)}")
    print("\nImported knowledge:")
    for doc_type in ("faq", "article", "delivery", "warranty", "material", "other"):
        print(f"- {doc_type}: {knowledge_counts.get(doc_type, 0)}")

    without_price = sum(1 for p in products if p.get("price_rub") is None)
    without_category = sum(1 for p in products if not p.get("category"))
    adjustable_no_height = sum(
        1
        for p in products
        if p.get("category") == "adjustable_desk"
        and (p.get("min_height_cm") is None or p.get("max_height_cm") is None)
    )
    adjustable_no_url = sum(
        1 for p in products if p.get("category") == "adjustable_desk" and not p.get("source_url")
    )
    print("\nWarnings:")
    print(f"- products without price: {without_price}")
    print(f"- products without category: {without_category}")
    print(f"- adjustable_desks without height range: {adjustable_no_height}")
    print(f"- adjustable_desks without source_url: {adjustable_no_url}")
    if product_counts.get("unknown", 0) > max(3, int(len(products) * 0.3)):
        print("- warning: unknown category share is high; improve classification rules.")


def run_import(args: ImportArgs) -> None:
    seeds = [
        urljoin(args.source_base_url, "/"),
        urljoin(args.source_base_url, "/catalog"),
        urljoin(args.source_base_url, "/blog"),
    ]
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    cache_dir = Path("data/cache")
    raw_dir = Path("data/raw")
    cache_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    queue = list(dict.fromkeys(seeds))
    visited: set[str] = set()
    products: list[dict[str, object]] = []
    knowledge_docs: list[dict[str, object]] = []
    source_pages: list[dict[str, object]] = []
    errors: list[str] = []
    run_id = f"stolstoya-run-{uuid.uuid4().hex[:10]}"

    while queue and len(visited) < args.max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        cache_file = cache_dir / _safe_cache_name(url)
        status_code = 0
        html = ""
        try:
            use_cache = cache_file.exists() and not args.refresh_cache and not args.no_cache
            if use_cache:
                html = cache_file.read_text(encoding="utf-8")
                status_code = 200
            else:
                response = session.get(url, timeout=20)
                status_code = response.status_code
                response.raise_for_status()
                html = response.text
                if not args.no_cache:
                    cache_file.write_text(html, encoding="utf-8")
            if not html.strip():
                raise ValueError("empty html")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{url}: {exc}")
            source_pages.append(
                {
                    "id": f"src-{hashlib.md5(url.encode('utf-8')).hexdigest()[:16]}",
                    "source": "stolstoya",
                    "url": url,
                    "page_type": "error",
                    "fetched_at": _now_iso(),
                    "status_code": status_code or 0,
                    "content_hash": "",
                }
            )
            print(f"[warn] failed page: {url} ({exc})")
            time.sleep(args.delay)
            continue

        content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
        soup = BeautifulSoup(html, "html.parser")
        title_node = soup.select_one("h1") or soup.select_one("title")
        title = title_node.get_text(" ", strip=True) if title_node else ""
        text = _extract_text_content(soup)
        if _is_catalog_like(url, title, text) and _is_product_page(url, title, text):
            products.append(_parse_product(url, html))
            page_type = "product"
        elif _is_knowledge_page(url, title, text):
            knowledge_docs.append(_parse_knowledge(url, html))
            page_type = "knowledge"
        elif _is_catalog_like(url, title, text):
            page_type = "catalog_listing"
        else:
            page_type = "other"

        source_pages.append(
            {
                "id": f"src-{hashlib.md5(url.encode('utf-8')).hexdigest()[:16]}",
                "source": "stolstoya",
                "url": url,
                "page_type": page_type,
                "fetched_at": _now_iso(),
                "status_code": status_code,
                "content_hash": content_hash,
            }
        )

        for discovered in _extract_links(args.source_base_url, html):
            queue_is_not_full = len(visited) + len(queue) < args.max_pages * 2
            if discovered not in visited and discovered not in queue and queue_is_not_full:
                queue.append(discovered)
        time.sleep(args.delay)

    _print_report(products, knowledge_docs)
    if args.dry_run:
        print("\nDry-run mode: DB write skipped.")
        return

    schema_path = Path(__file__).resolve().parent.parent / "storage" / "sqlite_schema.sql"
    _insert_records(
        db_path=args.db_path,
        schema_path=schema_path,
        products=products,
        knowledge_docs=knowledge_docs,
        source_pages=source_pages,
        run_id=run_id,
        errors=errors,
    )
    print(
        "\nImport completed: "
        f"products={len(products)}, "
        f"knowledge={len(knowledge_docs)}, "
        f"pages={len(source_pages)}"
    )


def main() -> None:
    run_import(_parse_cli_args())


if __name__ == "__main__":
    main()
