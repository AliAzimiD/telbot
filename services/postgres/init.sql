-- optional schema
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    url TEXT,
    page_html TEXT,
    requirements TEXT
);
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name TEXT,
    description TEXT,
    status TEXT
);
