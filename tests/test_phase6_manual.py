from app.db import supabase
from app.matching.property_matcher import PropertyMatcher

matcher = PropertyMatcher(supabase)

results = matcher.match_lead_to_properties(
    lead_id="1311358d-6bae-4936-9276-a9534f96698a",
    threshold=0,
)

for result in results:
    print(result)