from capacity_copilot.reasoning.parser import parse_query, MAX_TEST_COUNT, MAX_RACK_COUNT


def test_zero_or_missing_rack_count_clamped_to_minimum():
    # "0 racks" would otherwise crash SimPy with capacity=0
    params = parse_query("500 tests, 0 racks, 4 license seats")
    assert params.rack_count >= 1
    assert any("rack count" in n for n in params.notes)


def test_huge_test_count_clamped_to_max():
    params = parse_query("50000000 tests, 12 racks, 4 license seats")
    assert params.test_count == MAX_TEST_COUNT
    assert any("test count" in n for n in params.notes)


def test_huge_rack_count_clamped_to_max():
    params = parse_query("500 tests, 999999 racks, 4 license seats")
    assert params.rack_count == MAX_RACK_COUNT


def test_normal_query_has_no_notes():
    params = parse_query("2000 tests, 10 racks, 4 license seats")
    assert params.notes == []


def test_license_seats_missing_defaults_and_is_valid():
    params = parse_query("2000 tests, 10 racks")
    assert params.license_seats >= 1
