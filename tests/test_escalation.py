"""
Tests for all mandatory escalation triggers and prohibited actions.
"""

import pytest
from agent.orchestrator import ResolutionAgent
from policy.policy_engine import DecisionType


@pytest.fixture
def agent():
    return ResolutionAgent()


def test_escalation_legal_action_threat(agent):
    triggers = [
        "I am going to take legal action against this airline!",
        "My lawyer will contact your legal department.",
        "I'm filing a formal complaint with the consumer court.",
        "This is unacceptable, I will file a complaint with DGCA right now.",
    ]
    for msg in triggers:
        res = agent.process_message(msg, "SK4821X")
        assert res.decision.decision == DecisionType.ESCALATE
        assert res.decision.rule_id == "ESCALATE_LEGAL_FORMAL_COMPLAINT"
        assert res.escalation_ticket is not None
        assert "specialist support team" in res.text.lower()


def test_escalation_alternate_payment_method_refund(agent):
    triggers = [
        "I closed that card, refund me to a different card.",
        "Please send the refund in cash instead.",
        "Transfer the money to another account, not the original card.",
    ]
    for msg in triggers:
        res = agent.process_message(msg, "SK4821X")
        assert res.decision.decision == DecisionType.ESCALATE
        assert res.decision.rule_id == "ESCALATE_REFUND_METHOD_MISMATCH"
        assert res.escalation_ticket is not None
        assert "original payment method" in res.decision.rationale.lower()


def test_escalation_non_airline_disruption_exception(agent):
    triggers = [
        "I woke up late and missed my flight, give me a free rebooking anyway.",
        "I got stuck in traffic jam and missed my flight.",
    ]
    for msg in triggers:
        res = agent.process_message(msg, "TR1190B")
        assert res.decision.decision == DecisionType.ESCALATE
        assert res.decision.rule_id == "ESCALATE_NON_AIRLINE_EXCEPTION"
        assert res.escalation_ticket is not None


def test_escalation_fare_difference_above_threshold(agent):
    # ₹1,800 or ₹2,000 exceeds ₹1,500 limit
    res = agent.process_message("I want to switch to a flight with ₹1,800 fare difference.", "WL7742")
    assert res.decision.decision == DecisionType.ESCALATE
    assert res.decision.rule_id == "RULE_FARE_DIFF_EXCEEDS_AUTHORITY"
    assert res.escalation_ticket is not None
    assert "supervisor" in res.text.lower()


def test_escalation_unsupported_policy_compensation(agent):
    # Prohibited action: Approving any compensation beyond the stated policy amounts
    pe = agent.policy_engine
    res_unsupported = pe.check_escalation_required("I demand 10000 cash compensation for inconvenience", unsupported_compensation_requested=True)
    assert res_unsupported is not None
    assert res_unsupported.decision == DecisionType.ESCALATE
    assert res_unsupported.rule_id == "ESCALATE_UNSUPPORTED_COMPENSATION"
    assert "supervisor" in res_unsupported.required_human_action.lower()
