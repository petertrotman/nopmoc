create table if not exists
symbols(
    name text,
    library text
);
create table if not exists
properties(
    symbol_rowid references symbols(rowid),
    key text,
    value text
);
create table if not exists
pins(
    symbol_rowid references symbols(rowid),
    number integer,
    name text,
    electrical_type text,
    is_alternate bool default false
);
