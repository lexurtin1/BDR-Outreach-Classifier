from lead_engine.adapters.registry import get_adapter_cls


def test_registry_contains_adapters():
    assert get_adapter_cls("contracts_finder") is not None
    assert get_adapter_cls("ukri_gtr") is not None
    assert get_adapter_cls("ons") is not None
