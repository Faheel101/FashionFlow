"""Unit tests for Sprint 3 components: generators, quality, quarantine."""

import pytest

from source_system.generators.marketing import generate_marketing_data
from source_system.generators.inventory import generate_inventory_data
from ingestion.quarantine import QuarantineHandler, ValidationRule


class TestMarketingGenerator:
    """Verify marketing data generation."""

    def test_generates_all_tables(self):
        data = generate_marketing_data(seed=99, history_days=90)
        assert "campaigns" in data
        assert "ad_sets" in data
        assert "ads" in data
        assert "daily_performance" in data

    def test_campaigns_have_required_fields(self):
        data = generate_marketing_data(seed=99, history_days=90)
        for c in data["campaigns"]:
            assert c["id"] is not None
            assert c["name"]
            assert c["platform"] in ("google_ads", "meta_ads")
            assert c["daily_budget"] > 0

    def test_ad_sets_reference_campaigns(self):
        data = generate_marketing_data(seed=99, history_days=90)
        campaign_ids = {c["id"] for c in data["campaigns"]}
        for ad_set in data["ad_sets"]:
            assert ad_set["campaign_id"] in campaign_ids

    def test_ads_reference_ad_sets(self):
        data = generate_marketing_data(seed=99, history_days=90)
        ad_set_ids = {a["id"] for a in data["ad_sets"]}
        for ad in data["ads"]:
            assert ad["ad_set_id"] in ad_set_ids

    def test_performance_has_non_negative_metrics(self):
        data = generate_marketing_data(seed=99, history_days=90)
        for p in data["daily_performance"][:100]:
            assert p["impressions"] >= 0
            assert p["clicks"] >= 0
            assert p["spend"] >= 0
            assert p["revenue"] >= 0


class TestInventoryGenerator:
    """Verify inventory data generation."""

    def test_generates_snapshots_and_movements(self):
        data = generate_inventory_data(product_ids=[1, 2, 3], seed=99, history_days=90)
        assert len(data["inventory_snapshots"]) > 0
        assert len(data["inventory_movements"]) > 0

    def test_snapshots_have_required_fields(self):
        data = generate_inventory_data(product_ids=[1], seed=99, history_days=90)
        for s in data["inventory_snapshots"]:
            assert s["product_id"] == 1
            assert s["quantity_on_hand"] >= 0
            assert s["warehouse_location"]

    def test_movements_have_valid_types(self):
        valid_types = {"purchase", "sale", "return", "damage", "adjustment"}
        data = generate_inventory_data(product_ids=[1, 2], seed=99, history_days=90)
        for m in data["inventory_movements"]:
            assert m["movement_type"] in valid_types


class TestQuarantineValidation:
    """Test record-level validation logic (no BigQuery needed)."""

    def test_valid_records_pass(self):
        records = [{"id": 1, "name": "Test", "price": 10.0}]
        rules = [ValidationRule.not_null("id"), ValidationRule.positive("price")]
        qh = QuarantineHandler.__new__(QuarantineHandler)
        valid, quarantined = qh.validate_and_split(records, rules)
        assert len(valid) == 1
        assert len(quarantined) == 0

    def test_null_field_quarantined(self):
        records = [{"id": None, "name": "Test"}]
        rules = [ValidationRule.not_null("id")]
        qh = QuarantineHandler.__new__(QuarantineHandler)
        valid, quarantined = qh.validate_and_split(records, rules)
        assert len(valid) == 0
        assert len(quarantined) == 1
        assert "_quarantine_reasons" in quarantined[0]

    def test_negative_value_quarantined(self):
        records = [{"id": 1, "price": -5.0}]
        rules = [ValidationRule.positive("price")]
        qh = QuarantineHandler.__new__(QuarantineHandler)
        valid, quarantined = qh.validate_and_split(records, rules)
        assert len(valid) == 0
        assert len(quarantined) == 1

    def test_invalid_value_quarantined(self):
        records = [{"id": 1, "status": "invalid_status"}]
        rules = [ValidationRule.in_list("status", ["active", "paused"])]
        qh = QuarantineHandler.__new__(QuarantineHandler)
        valid, quarantined = qh.validate_and_split(records, rules)
        assert len(quarantined) == 1

    def test_mixed_records_split_correctly(self):
        records = [
            {"id": 1, "price": 10.0},
            {"id": 2, "price": -1.0},
            {"id": None, "price": 5.0},
            {"id": 3, "price": 20.0},
        ]
        rules = [ValidationRule.not_null("id"), ValidationRule.positive("price")]
        qh = QuarantineHandler.__new__(QuarantineHandler)
        valid, quarantined = qh.validate_and_split(records, rules)
        assert len(valid) == 2
        assert len(quarantined) == 2
