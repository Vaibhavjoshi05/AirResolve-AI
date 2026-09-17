"""
Tests for Scenario 3: Meher Kaur (Platinum, WL7742).
"""

import pytest
from agent.orchestrator import ResolutionAgent
from agent.intent_detector import UserIntent
from policy.policy_engine import DecisionType


@pytest.fixture
def agent():
    return ResolutionAgent()


def test_meher_delay_status_and_benefits(agent):
    res = agent.process_message("How long is the delay on SK-305 and what do I receive?", "WL7742")
    assert res.customer["name"] == "Meher Kaur"
    assert res.customer["loyalty_tier"] == "Platinum"
    assert res.decision.decision == DecisionType.RESOLVED
    assert "6 hours" in res.text or "6" in res.text
    assert "₹500 meal voucher" in res.text
    assert "lounge access" in res.text.lower()
    assert "hotel accommodation" in res.text.lower()


def test_meher_full_night_hotel_request(agent):
    # Customer: "I want a full night's hotel stay rather than just coverage for delayed hours"
    msg = "I need a full night's hotel stay rather than coverage for just the delayed hours."
    res = agent.process_message(msg, "WL7742")

    assert res.entities["full_night_requested"] is True
    assert res.decision.rule_id == "RULE_HOTEL_DELAYED_HOURS_ONLY"
    # Agent must explain hotel covers ONLY delayed hours, not full night
    assert "delayed hours" in res.text.lower()
    assert "full night" in res.text.lower()
    assert "not provide a full night's stay" in res.text.lower() or "does not" in res.text.lower()


def test_meher_higher_fare_rebooking_escalation(agent):
    # Customer: "I want to be moved onto a different, higher-fare flight instead of waiting — the fare difference is ₹2,000."
    msg = "Move me onto a different, higher-fare flight instead of waiting. The fare difference is ₹2,000."
    res = agent.process_message(msg, "WL7742")

    assert res.entities["fare_difference_inr"] == 2000.0
    assert res.decision.decision == DecisionType.ESCALATE
    assert res.decision.rule_id == "RULE_FARE_DIFF_EXCEEDS_AUTHORITY"
    assert res.decision.escalation_required is True

    # Must generate escalation ticket
    assert res.escalation_ticket is not None
    assert "ESC-WL7742-" in res.escalation_ticket["ticket_id"]
    assert "supervisor" in res.text.lower()
    assert "1,500" in res.text
    assert "2,000" in res.text


def test_meher_natural_fare_variations(agent):
    variations = [
        "Can you waive the 2000 rupees fare difference for an alternate flight?",
        "I found a higher fare flight with 2000 inr difference, switch me to it now.",
    ]
    for msg in variations:
        res = agent.process_message(msg, "WL7742")
        assert res.decision.decision == DecisionType.ESCALATE
        assert res.escalation_ticket is not None
        assert "supervisor" in res.text.lower()
