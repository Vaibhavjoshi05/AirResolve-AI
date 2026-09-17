"""
End-to-end tests for conversational agent, unknown bookings, and natural variations.
"""

import pytest
from agent.orchestrator import ResolutionAgent
from agent.intent_detector import UserIntent
from policy.policy_engine import DecisionType


@pytest.fixture
def agent():
    return ResolutionAgent()


def test_customer_lookup_by_pnr_and_name(agent):
    # Lookup by PNR
    res1 = agent.process_message("Hi, what is my flight status?", "SK4821X")
    assert res1.customer["name"] == "Priya Nair"

    # Lookup by name
    res2 = agent.process_message("Hi, what is my flight status?", "Arvind Kulkarni")
    assert res2.customer["name"] == "Arvind Kulkarni"


def test_unknown_customer_handling(agent):
    res = agent.process_message("What is happening with my flight?", "UNKNOWN_PNR")
    assert res.decision.decision == DecisionType.CLARIFICATION_NEEDED
    assert "couldn't locate a booking" in res.text.lower()


def test_natural_conversational_variations(agent):
    # Variation for refund: "give me my money back"
    res_refund = agent.process_message("Give me my money back please", "SK4821X")
    assert res_refund.intent == UserIntent.REQUEST_REFUND
    assert res_refund.decision.decision == DecisionType.RESOLVED

    # Variation for rebooking: "can you put me on another flight?"
    res_rebook = agent.process_message("Can you put me on another flight?", "SK4821X")
    assert res_rebook.intent == UserIntent.REQUEST_REBOOKING
    assert res_rebook.decision.decision == DecisionType.RESOLVED

    # Variation for hotel: "I need a hotel"
    res_hotel = agent.process_message("I need a hotel right now", "TR1190B")
    assert res_hotel.intent == UserIntent.REQUEST_HOTEL
    assert res_hotel.decision.decision == DecisionType.INELIGIBLE
    assert "5 hours" in res_hotel.text

    # Variation for upgrade: "I want business class"
    res_upgrade = agent.process_message("I want business class for the trouble", "SK4821X")
    assert res_upgrade.decision.decision == DecisionType.INELIGIBLE
    assert "business class" in res_upgrade.text.lower()


def test_decision_trace_integrity(agent):
    res = agent.process_message("Give me my money back", "SK4821X")
    assert len(res.trace) >= 4
    # Ensure trace mentions customer, booking, and policy steps
    trace_joined = " ".join(res.trace)
    assert "Priya Nair" in trace_joined
    assert "SK-204" in trace_joined
    assert "Cancelled" in trace_joined
