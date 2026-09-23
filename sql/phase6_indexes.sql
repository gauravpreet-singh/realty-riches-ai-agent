create index if not exists leads_matching_candidates_idx
on public.leads(status,intent,property_type,bedrooms,budget_max)
where intent in ('buy','both') and status not in ('lost','converted');

create index if not exists leads_preferred_locations_gin_idx
on public.leads using gin(preferred_locations);

create index if not exists properties_matching_candidates_idx
on public.properties(status,property_type,bedrooms,price);
