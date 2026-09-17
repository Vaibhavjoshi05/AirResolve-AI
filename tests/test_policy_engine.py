"""
Unit tests for deterministic PolicyEngine rules and boundaries.
"""

import pytest
from policy.policy_engine import PolicyEngine, DecisionType


@pytest.fixture
def engine():
    return PolicyEngine()


def test_customer_retrieval(engine):
    priya = engine.get_customer("SK4821X")
    assert priya is not None
    assert priya["name"] == "Priya Nair"
    assert priya["loyalty_tier"] == "Gold"

    arvind = engine.get_customer("TR1190B")
    assert arvind is not None
    assert arvind["name"] == "Arvind Kulkarni"
    assert arvind["loyalty_tier"] == "Silver"

    meher = engine.get_customer("WL7742")
    assert meher is not None
    assert meher["name"] == "Meher Kaur"
    assert meher["loyalty_tier"] == "Platinum"

    # Name-based lookup
    by_name = engine.get_customer("Arvind Kulkarni")
    assert by_name is not None
    assert by_name["booking_reference"] == "TR1190B"

    # Unknown lookup
    unknown = engine.get_customer("NONEXISTENT")
    assert unknown is None


def test_delay_under_3h(engine):
    # Under 3 hours delay qualifies for ₹500 meal voucher only
    dec = engine.evaluate_delay_compensation(2.0, customer_tier="Silver")
    assert dec.decision == DecisionType.RESOLVED
    assert dec.rule_id == "RULE_DELAY_UNDER_3H"
    assert "₹500 meal voucher" in dec.allowed_actions
    assert "Lounge access" not in dec.allowed_actions


def test_delay_3h_to_5h(engine):
    # More than 3 hours qualifies for meal voucher + lounge access
    dec = engine.evaluate_delay_compensation(4.0, customer_tier="Silver")
    assert dec.decision == DecisionType.RESOLVED
    assert dec.rule_id == "RULE_DELAY_3H_TO_5H"
    assert "₹500 meal voucher" in dec.allowed_actions
    assert "Lounge access" in dec.allowed_actions
    assert "Hotel accommodation (requires delay > 5 hours)" in dec.prohibited_actions


def test_delay_more_than_5h(engine):
    # More than 5 hours qualifies for meal voucher, lounge access, and hotel for delayed hours
    dec = engine.evaluate_delay_compensation(6.0, customer_tier="Platinum")
    assert dec.decision == DecisionType.RESOLVED
    assert dec.rule_id == "RULE_DELAY_MORE_THAN_5H"
    assert "₹500 meal voucher" in dec.allowed_actions
    assert "Lounge access" in dec.allowed_actions
    assert any("Hotel accommodation" in a for a in dec.allowed_actions)
    assert any("Full night's hotel stay" in p for p in dec.prohibited_actions)


def test_hotel_threshold_boundary(engine):
    # Delay of 4 hours -> Hotel strictly ineligible
    dec_4h = engine.evaluate_hotel_request(4.0, is_full_night_requested=False)
    assert dec_4h.decision == DecisionType.INELIGIBLE
    assert dec_4h.rule_id == "RULE_HOTEL_THRESHOLD_NOT_MET"

    # Delay of 5 hours exactly -> Under policy (>5h), 5.0h is not >5h -> Ineligible
    dec_5h = engine.evaluate_hotel_request(5.0, is_full_night_requested=False)
    assert dec_5h.decision == DecisionType.INELIGIBLE

    # Delay of 6 hours -> Eligible for delayed hours
    dec_6h = engine.evaluate_hotel_request(6.0, is_full_night_requested=False)
    assert dec_6h.decision == DecisionType.RESOLVED
    assert dec_6h.rule_id == "RULE_HOTEL_ELIGIBLE"

    # Delay of 6 hours with full night requested -> Approved only for delayed hours
    dec_full_night = engine.evaluate_hotel_request(6.0, is_full_night_requested=True)
    assert dec_full_night.decision == DecisionType.RESOLVED
    assert dec_full_night.rule_id == "RULE_HOTEL_DELAYED_HOURS_ONLY"
    assert any("Full night" in p for p in dec_full_night.prohibited_actions)


def test_fare_difference_authority(engine):
    # Fare diff 1000 INR -> within agent authority (<= 1500)
    dec_1000 = engine.evaluate_fare_difference_waiver(1000.0, is_voluntary=True)
    assert dec_1000.decision == DecisionType.RESOLVED
    assert dec_1000.rule_id == "RULE_FARE_DIFF_WITHIN_AUTHORITY"
    assert not dec_1000.escalation_required

    # Fare diff 1500 INR -> exactly on the limit -> allowed within authority
    dec_1500 = engine.evaluate_fare_difference_waiver(1500.0, is_voluntary=True)
    assert dec_1500.decision == DecisionType.RESOLVED
    assert dec_1500.rule_id == "RULE_FARE_DIFF_WITHIN_AUTHORITY"
    assert not dec_1500.escalation_required

    # Fare diff 2000 INR -> EXCEEDS agent authority threshold of 1500 -> MUST ESCALATE
    dec_2000 = engine.evaluate_fare_difference_waiver(2000.0, is_voluntary=True)
    assert dec_2000.decision == DecisionType.ESCALATE
    assert dec_2000.rule_id == "RULE_FARE_DIFF_EXCEEDS_AUTHORITY"
    assert dec_2000.escalation_required is True
    assert "Supervisor approval required" in dec_2000.required_human_action


def test_upgrade_request_denial(engine):
    # Complimentary business class upgrade is prohibited for all tiers
    dec_gold = engine.evaluate_upgrade_request(customer_tier="Gold")
    assert dec_gold.decision == DecisionType.INELIGIBLE
    assert dec_gold.rule_id == "RULE_COMPLIMENTARY_UPGRADE_PROHIBITED"
    assert any("Business Class" in p for p in dec_gold.prohibited_actions)

    dec_plat = engine.evaluate_upgrade_request(customer_tier="Platinum")
    assert dec_plat.decision == DecisionType.INELIGIBLE
