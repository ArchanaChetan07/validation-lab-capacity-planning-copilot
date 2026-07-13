import pytest

from capacity_copilot.models.license_pool import LicensePool, LicenseRegistry


def test_hold_and_release():
    pool = LicensePool(name="dft_tool", total_seats=4)
    pool.hold(3)
    assert pool.available() == 1
    pool.release(1)
    assert pool.available() == 2


def test_cannot_overhold():
    pool = LicensePool(name="dft_tool", total_seats=2)
    pool.hold(2)
    assert pool.can_hold(1) is False
    with pytest.raises(ValueError):
        pool.hold(1)


def test_release_does_not_go_negative():
    pool = LicensePool(name="dft_tool", total_seats=2)
    pool.release(5)
    assert pool.held_seats == 0


def test_registry_utilization():
    reg = LicenseRegistry()
    reg.add(LicensePool(name="dsp_tool", total_seats=10))
    reg.get("dsp_tool").hold(5)
    assert reg.utilization("dsp_tool") == 0.5
