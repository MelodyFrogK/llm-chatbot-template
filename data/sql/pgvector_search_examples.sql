-- 예시 조회
select user_name, category, item_name, count
from public.user_inventory
where user_name = '김택진'
order by category, item_name;

select item_name, attack, accuracy, rarity
from public.items_master
where item_name = '은빛검';

-- 벡터 검색 예시
-- select id, title, content
-- from public.rag_documents
-- order by embedding <=> '[0.1, 0.2, ...]'::cdb_admin.vector
-- limit 5;