-- 일반 테이블은 public 스키마에 생성
create table if not exists public.items_master (
    item_id      text primary key,
    category     text not null,
    item_name    text not null,
    attack       integer,
    accuracy     integer,
    defense      integer,
    effect       text,
    rarity       text
);

create table if not exists public.user_inventory (
    inventory_id bigserial primary key,
    user_id      text not null,
    user_name    text not null,
    category     text not null,
    item_name    text not null,
    count        integer not null check (count >= 0)
);

create table if not exists public.rag_documents (
    id         text primary key,
    source     text not null,
    doc_type   text not null,
    category   text not null,
    title      text not null,
    content    text not null,
    embedding  cdb_admin.vector(1024)
);