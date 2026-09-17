"""
Tests for Scenario 2: Arvind Kulkarni (Silver, TR1190B).
"""

import pytest
from agent.orchestrator import ResolutionAgent
from agent.intent_detector import UserIntent
from policy.policy_engine import DecisionType


@pytest.fixture
def agent():
    return ResolutionAgent()


def test_arvind_delay_benefits_inquiry(agent):
    res = agent.process_message("My flight SK-118 is delayed. What compensation do I get?", "TR1190B")
    assert res.customer["name"] == "Arvind Kulkarni"
    assert res.customer["loyalty_tier"] == "Silver"
    assert res.decision.decision == DecisionType.RESOLVED
    assert "₹500 meal voucher" in res.text
    assert "lounge access" in res.text.lower()


def test_arvind_hotel_request_denial(agent):
    # Customer: "I'm frustrated about missing a connecting meeting and I need hotel accommodation since it's been such a long delay."
    msg = "I'm frustrated about missing a connecting meeting and I need hotel accommodation since it's been such a long delay."
    res = agent.process_message(msg, "TR1190B")

    assert res.intent == UserIntent.REQUEST_HOTEL
    # Policy evaluation must mark hotel as ineligible
    assert res.decision.decision == DecisionType.INELIGIBLE
    assert res.decision.rule_id == "RULE_HOTEL_THRESHOLD_NOT_MET"

    # Must explain that hotel requires delay > 5 hours
    assert "5 hours" in res.text
    assert "cannot provide hotel" in res.text.lower() or "not eligible" in res.text.lower()

    # Must confirm meal voucher + lounge access are provided
    assert "₹500 meal voucher" in res.text
    assert "lounge access" in res.text.lower()


def test_arvind_natural_hotel_variations(agent):
    variations = [
        "Can I get a hotel room while waiting?",
        "Please book a hotel room for me for this 4 hour delay.",
        "I need a place to sleep during the delay.",
    ]
    for msg in variations:
        res = agent.process_message(msg, "TR1190B")
        assert res.decision.decision == DecisionType.INELIGIBLE
        assert "5 hours" in res.text
        assert "hotel" in res.text.lower()
