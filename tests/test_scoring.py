from app.matching.scoring import score_property_for_lead


def test_exact_sector_125_match():
    lead={"preferred_locations":["Sector 125","Kharar"],
          "budget_max":9500000,"property_type":"apartment","bedrooms":3}
    prop={"title":"Touch Homes","location":"Sector 125","city":"Kharar",
          "price":8900000,"property_type":"Apartment","bedrooms":3}
    assert score_property_for_lead(lead,prop).score==100

def test_zero_price_not_budget_match():
    lead={"preferred_locations":["Kharar"],"budget_max":10000000,
          "property_type":"apartment","bedrooms":3}
    prop={"location":"Kharar","price":0,"property_type":"Apartment","bedrooms":3}
    assert score_property_for_lead(lead,prop).budget==0
