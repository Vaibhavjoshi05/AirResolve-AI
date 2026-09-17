"""
Tests for Scenario 1: Priya Nair (Gold, SK4821X).
"""

import pytest
from agent.orchestrator import ResolutionAgent
from agent.intent_detector import UserIntent
from policy.policy_engine import DecisionType


@pytest.fixture
def agent():
    return ResolutionAgent()


def test_priya_cancellation_status_inquiry(agent):
    res = agent.process_message("What happened to my flight SK-204?", "SK4821X")
    assert "cancelled due to operational reasons" in res.text.lower()
    assert res.customer["name"] == "Priya Nair"
    assert res.customer["loyalty_tier"] == "Gold"
    assert res.decision.decision in [DecisionType.CLARIFICATION_NEEDED, DecisionType.RESOLVED]


def test_priya_full_refund_request(agent):
    # Customer request: "My flight got cancelled and I want my money back."
    res = agent.process_message("My flight has been cancelled. I want my money back.", "SK4821X")
    assert res.intent == UserIntent.REQUEST_REFUND
    assert res.decision.decision == DecisionType.RESOLVED
    assert res.decision.rule_id == "RULE_REFUND_PROCESSING"
    assert "7 business days" in res.text
    assert "original payment method" in res.text.lower()
    assert not res.decision.escalation_required


def test_priya_unsupported_free_business_upgrade(agent):
    # Customer: "I'm furious and I want a full cash refund plus a free upgrade to business class on my return flight"
    msg = "I am furious! I want a full cash refund plus a free upgrade to business class on my return flight for the trouble."
    res = agent.process_message(msg, "SK4821X")
    
    # Must initiate refund
    assert "refund" in res.text.lower()
    assert "7 business days" in res.text
    
    # Must REFUSE complimentary business class upgrade
    assert "business class" in res.text.lower()
    assert "not permit" in res.text.lower() or "unable" in res.text.lower() or "cannot provide" in res.text.lower()
    assert any("Business Class" in p for p in res.decision.prohibited_actions)


def test_priya_free_rebooking_choice(agent):
    res = agent.process_message("Can you rebook me on the next flight?", "SK4821X")
    assert res.intent == UserIntent.REQUEST_REBOOKING
    assert res.decision.decision == DecisionType.RESOLVED
    assert "free rebooking" in res.text.lower()
    assert "24 hours" in res.text
    # Gold priority rebooking mentioned
    assert "gold" in res.text.lower() or "priority" in res.text.lower()


def test_priya_legal_action_escalation(agent):
    # If Priya threatens legal action or formal complaint
    res = agent.process_message("This is unacceptable, I will take legal action against your company!", "SK4821X")
    assert res.decision.decision == DecisionType.ESCALATE
    assert res.decision.escalation_required is True
    assert res.escalation_ticket is not None
    assert "specialist support team" in res.text.lower()
    assert "ESCALATE_LEGAL_FORMAL_COMPLAINT" == res.decision.rule_id
