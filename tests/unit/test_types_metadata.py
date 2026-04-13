from __future__ import annotations

import pytest
from pydantic import BaseModel

from ogpu.types.enums import DeliveryMethod
from ogpu.types.metadata import (
    ImageEnvironments,
    ResponseParams,
    SourceInfo,
    SourceMetadata,
    SourceParams,
    TaskInfo,
    TaskInput,
    TaskParams,
)


class SampleInput(BaseModel):
    prompt: str
    n: int = 1


class TestSourceMetadata:
    def test_construction(self):
        meta = SourceMetadata(
            cpu="cpu.yml",
            nvidia="nvidia.yml",
            amd="amd.yml",
            name="demo",
            description="desc",
            logoUrl="https://l.png",
        )
        d = meta.to_dict()
        assert d["cpu"] == "cpu.yml"
        assert d["name"] == "demo"
        assert set(d.keys()) == {"cpu", "nvidia", "amd", "name", "description", "logoUrl"}


class TestImageEnvironments:
    def test_defaults_empty(self):
        env = ImageEnvironments()
        assert env.cpu == ""
        assert env.nvidia == ""
        assert env.amd == ""

    def test_partial(self):
        env = ImageEnvironments(cpu="a", nvidia="b")
        assert env.amd == ""


class TestSourceParams:
    def test_to_tuple(self):
        params = SourceParams(
            client="0xC",
            imageMetadataUrl="ipfs://Qm",
            imageEnvironments=3,
            minPayment=10,
            minAvailableLockup=1,
            maxExpiryDuration=60,
            privacyEnabled=False,
            optionalParamsUrl="",
            deliveryMethod=0,
            lastUpdateTime=1234,
        )
        t = params.to_tuple()
        assert t[0] == "0xC"
        assert t[2] == 3
        assert t[-1] == 1234
        assert len(t) == 10


class TestTaskParams:
    def test_to_tuple(self):
        params = TaskParams(source="0xS", config="ipfs://Qm", expiryTime=100, payment=50)
        assert params.to_tuple() == ("0xS", "ipfs://Qm", 100, 50)


class TestResponseParams:
    def test_construction_frozen(self):
        rp = ResponseParams(task="0xT", provider="0xP", data="blob", payment=5)
        assert rp.task == "0xT"
        assert rp.provider == "0xP"
        with pytest.raises(Exception):
            rp.task = "0xX"  # type: ignore[misc]


class TestTaskInput:
    def test_with_dict_data(self):
        ti = TaskInput(function_name="fn", data={"k": "v"})
        assert ti.to_dict() == {"function_name": "fn", "data": {"k": "v"}}

    def test_with_pydantic_data(self):
        ti = TaskInput(function_name="fn", data=SampleInput(prompt="hi", n=2))
        out = ti.to_dict()
        assert out["function_name"] == "fn"
        assert out["data"] == {"prompt": "hi", "n": 2}

    def test_with_extra_kwargs(self):
        ti = TaskInput(function_name="fn", data={}, campus="ucsd", sensitivity="high")
        out = ti.to_dict()
        assert out["campus"] == "ucsd"
        assert out["sensitivity"] == "high"


class TestSourceInfoIsPureDataclass:
    def test_has_no_to_source_params_method(self):
        """SourceInfo must not trigger network I/O on construction or conversion."""
        info = SourceInfo(
            name="demo",
            description="desc",
            logoUrl="https://l.png",
            imageEnvs=ImageEnvironments(cpu="cpu.yml"),
            minPayment=10,
            minAvailableLockup=0,
            maxExpiryDuration=3600,
            deliveryMethod=DeliveryMethod.FIRST_RESPONSE,
        )
        assert not hasattr(info, "to_source_params")


class TestTaskInfoIsPureDataclass:
    def test_has_no_to_task_params_method(self):
        ti = TaskInfo(
            source="0xSRC",
            config=TaskInput(function_name="predict", data={"x": 1}),
            expiryTime=1000,
            payment=42,
        )
        assert not hasattr(ti, "to_task_params")
