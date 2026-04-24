PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_product_id TEXT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subtype TEXT,
    price_rub INTEGER,
    min_height_cm INTEGER,
    max_height_cm INTEGER,
    width_cm INTEGER,
    depth_cm INTEGER,
    motors_count INTEGER,
    lifting_capacity_kg INTEGER,
    tabletop_material TEXT,
    description_short TEXT,
    availability TEXT,
    raw_payload_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_source ON products(source);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    tags_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_knowledge_doc_type ON knowledge_documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge_documents(source);

CREATE TABLE IF NOT EXISTS source_pages (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    page_type TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    content_hash TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_source_pages_source ON source_pages(source);

CREATE TABLE IF NOT EXISTS import_runs (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    products_count INTEGER NOT NULL DEFAULT 0,
    knowledge_count INTEGER NOT NULL DEFAULT 0,
    errors_json TEXT
);
