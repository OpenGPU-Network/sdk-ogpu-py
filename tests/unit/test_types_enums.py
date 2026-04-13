from __future__ import annotations

from ogpu.types.enums import (
    DeliveryMethod,
    Environment,
    ResponseStatus,
    Role,
    SourceStatus,
    TaskStatus,
    combine_environments,
    environment_names,
    parse_environments,
)


class TestStatusEnums:
    def test_task_status_values(self):
        assert TaskStatus.NEW == 0
        assert TaskStatus.ATTEMPTED == 1
        assert TaskStatus.RESPONDED == 2
        assert TaskStatus.CANCELED == 3
        assert TaskStatus.EXPIRED == 4
        assert TaskStatus.FINALIZED == 5

    def test_source_status_values(self):
        assert SourceStatus.ACTIVE == 0
        assert SourceStatus.INACTIVE == 1

    def test_response_status_values(self):
        assert ResponseStatus.SUBMITTED == 0
        assert ResponseStatus.CONFIRMED == 1

    def test_status_enums_compare_to_ints(self):
        assert TaskStatus.NEW == 0
        assert SourceStatus.ACTIVE == 0
        assert ResponseStatus.CONFIRMED == 1


class TestEnvironment:
    def test_bitmask_values(self):
        assert Environment.CPU.value == 1
        assert Environment.NVIDIA.value == 2
        assert Environment.AMD.value == 4

    def test_combine_environments(self):
        assert combine_environments(Environment.CPU, Environment.NVIDIA) == 3
        assert combine_environments(Environment.CPU, Environment.AMD) == 5
        assert combine_environments(
            Environment.CPU, Environment.NVIDIA, Environment.AMD
        ) == 7
        assert combine_environments() == 0

    def test_parse_environments(self):
        parsed = parse_environments(3)
        assert Environment.CPU in parsed
        assert Environment.NVIDIA in parsed
        assert Environment.AMD not in parsed

    def test_environment_names(self):
        assert set(environment_names(5)) == {"CPU", "AMD"}
        assert environment_names(0) == []


class TestDeliveryMethod:
    def test_values(self):
        assert DeliveryMethod.MANUAL_CONFIRMATION.value == 0
        assert DeliveryMethod.FIRST_RESPONSE.value == 1


class TestRole:
    def test_values(self):
        assert Role.CLIENT.value == "client"
        assert Role.PROVIDER.value == "provider"
        assert Role.MASTER.value == "master"
