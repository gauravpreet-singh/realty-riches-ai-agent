import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MatchResult:
    score: int
    location: int
    budget: int
    property_type: int
    bedrooms: int

def norm(v): return re.sub(r"\s+", " ", str(v or "").strip().lower())

def score_property_for_lead(lead, prop):
    locations = [norm(x) for x in (lead.get("preferred_locations") or []) if x]
    hay = " ".join(norm(prop.get(k)) for k in
                   ("title","location","location_slug","city","description"))
    if not locations:
        loc = 20
    elif any(x in hay for x in locations):
        loc = 35
    else:
        loc = 0

    price = prop.get("price")
    bmin, bmax = lead.get("budget_min"), lead.get("budget_max")
    if price in (None, 0):
        budget = 0 if bmin is not None or bmax is not None else 20
    elif bmin is not None and price < bmin:
        budget = 12 if price >= bmin * .95 else 0
    elif bmax is not None and price > bmax:
        budget = 12 if price <= bmax * 1.05 else 0
    else:
        budget = 30

    aliases = {"flat":"apartment","flats":"apartment","house":"villa","home":"villa"}
    req, actual = norm(lead.get("property_type")), norm(prop.get("property_type"))
    req, actual = aliases.get(req, req), aliases.get(actual, actual)
    typ = 20 if not req else (20 if req == actual else 0)

    rb, pb = lead.get("bedrooms"), prop.get("bedrooms")
    bed = 10 if rb is None else (0 if pb is None else
          (15 if int(rb)==int(pb) else (8 if int(pb)>int(rb) else 0)))

    return MatchResult(min(100,loc+budget+typ+bed),loc,budget,typ,bed)
