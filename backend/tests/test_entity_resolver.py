import pytest
from app.data_layer.entity_resolver import entity_resolver


def test_canonical_tenant_resolution():
    res = entity_resolver.resolve_tenant("Cascade Fuel Services")
    assert res is not None
    assert res[0] == 1

    res = entity_resolver.resolve_tenant("Summit Energy Group")
    assert res is not None
    assert res[0] == 3


def test_alias_resolution():
    # CFS -> 1
    res = entity_resolver.resolve_tenant("CFS")
    assert res is not None
    assert res[0] == 1

    # Heartland -> 2
    res = entity_resolver.resolve_tenant("Heartland")
    assert res is not None
    assert res[0] == 2

    # DSP -> 4
    res = entity_resolver.resolve_tenant("DSP")
    assert res is not None
    assert res[0] == 4

    # TRO -> 8
    res = entity_resolver.resolve_tenant("TRO")
    assert res is not None
    assert res[0] == 8


def test_email_domain_resolution():
    res = entity_resolver.resolve_tenant("contact_4_0@desertsunpetroleum.com")
    assert res is not None
    assert res[0] == 4

    res = entity_resolver.resolve_tenant("contact_1_1@cascadefuelservices.com")
    assert res is not None
    assert res[0] == 1


def test_explicit_tenant_id_syntax():
    res = entity_resolver.resolve_tenant("How many orders did tenant 3 complete?")
    assert res is not None
    assert res[0] == 3

    res = entity_resolver.resolve_tenant("tenant_id: 4")
    assert res is not None
    assert res[0] == 4


def test_fuzzy_name_matching():
    res = entity_resolver.resolve_tenant("Cascad Fuel Servces")
    assert res is not None
    assert res[0] == 1

