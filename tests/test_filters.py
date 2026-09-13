from tesla_monitor.filters import vehicle_id, vehicle_matches

SAMPLE_VEHICLE = {
    "VIN": "LRW3XXXXXXXXXXXXX",
    "Model": "my",
    "TrimName": "Long Range All-Wheel Drive",
    "Price": 44990,
    "OptionCodeData": [
        {"code": "PPSW", "name": "Pearl White Multi-Coat"},
        {"code": "IN3PB", "name": "All Black Premium Interior"},
        {"code": "W40B", "name": "19\" Gemini Wheels"},
        {"code": "APBS", "name": "Enhanced Autopilot"},
    ],
}


def test_matches_with_no_filters():
    assert vehicle_matches(SAMPLE_VEHICLE, {}) is True


def test_price_max_filters_out_expensive_vehicle():
    assert vehicle_matches(SAMPLE_VEHICLE, {"price_max": 40000}) is False


def test_price_max_allows_cheaper_vehicle():
    assert vehicle_matches(SAMPLE_VEHICLE, {"price_max": 50000}) is True


def test_exterior_color_match_is_case_insensitive_substring():
    assert vehicle_matches(SAMPLE_VEHICLE, {"exterior_contains": ["pearl white"]}) is True
    assert vehicle_matches(SAMPLE_VEHICLE, {"exterior_contains": ["Deep Blue"]}) is False


def test_multiple_categories_are_combined_with_and():
    filters = {
        "trim_contains": ["Long Range"],
        "exterior_contains": ["Pearl White"],
        "interior_contains": ["Black"],
    }
    assert vehicle_matches(SAMPLE_VEHICLE, filters) is True

    filters["interior_contains"] = ["White Interior"]
    assert vehicle_matches(SAMPLE_VEHICLE, filters) is False


def test_vehicle_id_prefers_vin():
    assert vehicle_id(SAMPLE_VEHICLE) == "vin:LRW3XXXXXXXXXXXXX"


def test_vehicle_id_falls_back_to_spec_when_no_vin():
    vehicle = {k: v for k, v in SAMPLE_VEHICLE.items() if k != "VIN"}
    vid = vehicle_id(vehicle)
    assert vid.startswith("spec:")
