from capacity_copilot.models.rack import Rack, RackInventory, RackType, RackStatus


def test_rack_can_run_compatible_suite():
    rack = Rack(rack_id="r1", rack_type=RackType.FPGA_PROTOTYPE, compatible_suites={"dft"})
    assert rack.can_run("dft") is True
    assert rack.can_run("dsp") is False


def test_down_rack_cannot_run_anything():
    rack = Rack(
        rack_id="r2",
        rack_type=RackType.EMULATOR,
        compatible_suites={"dft"},
        status=RackStatus.DOWN,
    )
    assert rack.can_run("dft") is False


def test_inventory_available_for_suite():
    racks = [
        Rack(rack_id="r1", rack_type=RackType.FPGA_PROTOTYPE, compatible_suites={"dft"}),
        Rack(rack_id="r2", rack_type=RackType.EMULATOR, compatible_suites={"dsp"}),
        Rack(
            rack_id="r3",
            rack_type=RackType.FPGA_PROTOTYPE,
            compatible_suites={"dft"},
            status=RackStatus.DOWN,
        ),
    ]
    inv = RackInventory(racks=racks)
    assert inv.total_count() == 3
    assert inv.available_count() == 2
    assert [r.rack_id for r in inv.available_for("dft")] == ["r1"]
