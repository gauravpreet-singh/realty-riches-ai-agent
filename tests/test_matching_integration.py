from app.matching.scoring import score_property_for_lead


def test_sector_125_touch_homes_matches_buyer_requirements():
    lead = {
        "preferred_locations": ["Sector 125", "Kharar"],
        "budget_max": 95_000_000,
        "budget_min": None,
        "property_type": "Apartment",
        "bedrooms": 3,
    }
    prop = {
        "title": "Touch Homes Sector 125 Kharar",
        "location": "Sector 125 Kharar",
        "location_slug": "sector-125-kharar",
        "city": "Kharar",
        "description": "3 BHK apartment",
        "property_type": "Apartment",
        "bedrooms": 3,
        "price": 8_900_000,
    }
    result = score_property_for_lead(lead, prop)
    assert result.score == 100
