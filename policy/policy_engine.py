"""
Deterministic Policy Engine for Airline Disruption Resolution (AirResolve).

This module is the SINGLE SOURCE OF TRUTH for all airline business rules,
entitlements, compensation thresholds, agent authority limits, and escalation triggers.
It strictly enforces the Assignment 3 Data Pack rules (Date: 23 September 2026).
Conversational and LLM layers MUST NOT override or bypass this engine.
"""

from dataclasses import dataclass, field
from enum import Enum
import json
import os
from typing import Any, Dict, List, Optional, Tuple


class DecisionType(str, Enum):
    RESOLVED = "RESOLVED"
    INELIGIBLE = "INELIGIBLE"
    ESCALATE = "ESCALATE"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    INFO_PROVIDED = "INFO_PROVIDED"


class DisruptionType(str, Enum):
    CANCELLED = "CANCELLED"
    DELAYED = "DELAYED"
    UNAFFECTED = "UNAFFECTED"
    UNKNOWN = "UNKNOWN"


@dataclass
class PolicyDecision:
    decision: DecisionType
    rule_id: str
    rule_name: str
    rationale: str
    allowed_actions: List[str] = field(default_factory=list)
    prohibited_actions: List[str] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    escalation_required: bool = False
    escalation_reason: Optional[str] = None
    required_human_action: Optional[str] = None
    policy_reference: Optional[str] = None
    trace_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "rationale": self.rationale,
            "allowed_actions": self.allowed_actions,
            "prohibited_actions": self.prohibited_actions,
            "action_items": self.action_items,
            "escalation_required": self.escalation_required,
            "escalation_reason": self.escalation_reason,
            "required_human_action": self.required_human_action,
            "policy_reference": self.policy_reference,
            "trace_steps": self.trace_steps,
        }


class PolicyEngine:
    """
    Deterministic rule engine implementing strict business policies.
    """

    AGENT_FARE_DIFFERENCE_LIMIT_INR: float = 1500.0
    HOTEL_MIN_DELAY_HOURS: float = 5.0
    MEAL_VOUCHER_MIN_DELAY_HOURS: float = 0.0
    LOUNGE_MIN_DELAY_HOURS: float = 3.0
    REFUND_PROCESSING_DAYS: int = 7
    REBOOKING_WINDOW_HOURS: int = 24

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            # Default to ../data relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")

        self.data_dir = data_dir
        self.customers_data = self._load_json("customers.json")
        self.bookings_data = self._load_json("bookings.json")
        self.policies_data = self._load_json("policies.json")

    def _load_json(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required policy data file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # -------------------------------------------------------------------------
    # Retrieval Helpers
    # -------------------------------------------------------------------------
    def get_customer(self, pnr_or_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve customer profile by PNR or full/partial name."""
        clean_key = pnr_or_name.strip().upper()
        customers = self.customers_data.get("customers", {})

        if clean_key in customers:
            return customers[clean_key]

        # Try matching by name
        target_name = pnr_or_name.strip().lower()
        for pnr, cust in customers.items():
            if cust.get("name", "").strip().lower() == target_name:
                return cust
            if target_name in cust.get("name", "").strip().lower():
                return cust

        return None

    def get_booking(self, pnr: str) -> Optional[Dict[str, Any]]:
        """Retrieve booking transaction data by PNR."""
        clean_pnr = pnr.strip().upper()
        return self.bookings_data.get("bookings", {}).get(clean_pnr)

    def get_primary_segment(self, booking: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return the disrupted or first active flight segment from booking."""
        segments = booking.get("segments", [])
        if not segments:
            return None
        # Prefer disrupted flight (Cancelled or Delayed)
        for seg in segments:
            if seg.get("status") in ["Cancelled", "Delayed"]:
                return seg
        return segments[0]

    # -------------------------------------------------------------------------
    # Scenario Evaluation 1: Cancellation & Rebooking / Refund
    # -------------------------------------------------------------------------
    def evaluate_cancellation_options(
        self,
        booking: Dict[str, Any],
        customer: Dict[str, Any],
        selected_option: Optional[str] = None,  # "refund", "rebook", or None
    ) -> PolicyDecision:
        """
        Cancellation Rebooking Rule:
        If flight is cancelled by airline, customer entitled to free rebooking
        on next available flight within 24 hours, or a full refund, customer's choice.
        Loyalty Tier Rule: Gold and Platinum get priority rebooking, no extra compensation.
        """
        trace = [
            f"Evaluated booking: {booking.get('booking_reference')}",
            f"Customer: {customer.get('name')} (Tier: {customer.get('loyalty_tier')})",
        ]

        segment = self.get_primary_segment(booking)
        if not segment or segment.get("status") != "Cancelled":
            trace.append("Segment status is NOT cancelled.")
            return PolicyDecision(
                decision=DecisionType.INELIGIBLE,
                rule_id="RULE_CANCELLATION_NOT_APPLICABLE",
                rule_name="Cancellation Rebooking Rule",
                rationale="The primary flight segment is not marked as cancelled.",
                trace_steps=trace,
            )

        is_airline_caused = segment.get("is_airline_caused", True)
        if not is_airline_caused:
            trace.append("Cancellation was not airline-caused -> Escalate")
            return PolicyDecision(
                decision=DecisionType.ESCALATE,
                rule_id="RULE_NON_AIRLINE_DISRUPTION",
                rule_name="Prohibited Action: Non-Airline Disruption",
                rationale="Policy strictly prohibits automated exceptions for non-airline-caused disruptions.",
                escalation_required=True,
                escalation_reason="Disruption is not airline-caused. Human agent review required.",
                required_human_action="Agent supervisor review for non-airline disruption exception.",
                policy_reference="Allowed vs. Prohibited Actions: Making exceptions for non-airline-caused disruptions",
                trace_steps=trace,
            )

        tier = customer.get("loyalty_tier", "Standard")
        has_priority = tier in ["Gold", "Platinum"]
        tier_perk = "Priority rebooking (first access to next-available seats)" if has_priority else "Standard rebooking"

        allowed = [
            f"Free rebooking on next available flight within {self.REBOOKING_WINDOW_HOURS} hours",
            f"Full refund to original payment method (processed in {self.REFUND_PROCESSING_DAYS} business days)",
        ]
        if has_priority:
            allowed.append(tier_perk)

        prohibited = [
            "Free upgrade to Business Class (not permitted under policy)",
            "Additional cash compensation beyond standard policy",
            "Refund to alternate payment method",
        ]

        trace.append(f"Identified cancellation due to {segment.get('cancellation_reason')}.")
        trace.append(f"Customer tier {tier} grants: {tier_perk}.")

        # If user explicitly picked refund
        if selected_option == "refund":
            trace.append("Customer elected full refund option.")
            return PolicyDecision(
                decision=DecisionType.RESOLVED,
                rule_id="RULE_REFUND_PROCESSING",
                rule_name="Refund Processing Rule",
                rationale=(
                    f"Full refund initiated for flight {segment.get('flight_number')} "
                    f"due to cancellation ({segment.get('cancellation_reason')}). "
                    f"Refund will be credited in full within {self.REFUND_PROCESSING_DAYS} business days "
                    "to the original payment method only."
                ),
                allowed_actions=allowed,
                prohibited_actions=prohibited,
                action_items=[
                    {
                        "action": "INITIATE_FULL_REFUND",
                        "flight_number": segment.get("flight_number"),
                        "processing_timeline": f"{self.REFUND_PROCESSING_DAYS} business days",
                        "payment_destination": "Original payment method only",
                        "status": "APPROVED",
                    }
                ],
                policy_reference="Refund Processing Rule & Cancellation Rebooking Rule",
                trace_steps=trace,
            )

        # If user explicitly picked rebooking
        if selected_option == "rebook":
            trace.append("Customer elected rebooking option.")
            return PolicyDecision(
                decision=DecisionType.RESOLVED,
                rule_id="RULE_CANCELLATION_REBOOKING",
                rule_name="Cancellation Rebooking Rule",
                rationale=(
                    f"Free rebooking authorized on the next available flight within "
                    f"{self.REBOOKING_WINDOW_HOURS} hours at no charge. "
                    + (f"Customer holds {tier} status and is granted priority seat access." if has_priority else "")
                ),
                allowed_actions=allowed,
                prohibited_actions=prohibited,
                action_items=[
                    {
                        "action": "FREE_REBOOKING_NEXT_FLIGHT",
                        "window_hours": self.REBOOKING_WINDOW_HOURS,
                        "priority": has_priority,
                        "status": "AUTHORIZED",
                    }
                ],
                policy_reference="Cancellation Rebooking Rule & Loyalty Tier Rule",
                trace_steps=trace,
            )

        # Default: Offer customer's choice
        trace.append("Awaiting customer choice between free rebooking or full refund.")
        return PolicyDecision(
            decision=DecisionType.CLARIFICATION_NEEDED,
            rule_id="RULE_CANCELLATION_REBOOKING",
            rule_name="Cancellation Rebooking Rule",
            rationale=(
                f"Flight {segment.get('flight_number')} was cancelled due to {segment.get('cancellation_reason')}. "
                f"Under policy, customer is entitled to: 1) Free rebooking on the next available flight within 24 hours "
                f"({tier_perk}), OR 2) Full refund to original payment method within 7 business days."
            ),
            allowed_actions=allowed,
            prohibited_actions=prohibited,
            policy_reference="Cancellation Rebooking Rule & Loyalty Tier Rule",
            trace_steps=trace,
        )

    # -------------------------------------------------------------------------
    # Scenario Evaluation 2: Delay Compensation
    # -------------------------------------------------------------------------
    def evaluate_delay_compensation(
        self,
        delay_hours: float,
        customer_tier: str = "Standard",
        segment_info: Optional[Dict[str, Any]] = None,
    ) -> PolicyDecision:
        """
        Delay Compensation Rule:
        - Delay under 3 hours: ₹500 meal voucher
        - Delay more than 3 hours: meal voucher + lounge access
        - Delay more than 5 hours: meal voucher + hotel accommodation, covering only delayed hours (not full night)
        Loyalty Tier Rule:
        Gold/Platinum get priority rebooking if needed, NO additional compensation beyond standard policy.
        """
        trace = [
            f"Evaluating delay compensation for {delay_hours:.1f} hours delay.",
            f"Customer Loyalty Tier: {customer_tier}",
        ]

        allowed_actions = []
        action_items = []
        prohibited_actions = [
            "Cash compensation beyond stated policy vouchers",
            "Automatic full-night hotel stay",
        ]

        if delay_hours < 0:
            return PolicyDecision(
                decision=DecisionType.INELIGIBLE,
                rule_id="RULE_NO_DELAY",
                rule_name="Delay Compensation Rule",
                rationale="No delay detected.",
                trace_steps=trace,
            )

        if delay_hours < 3.0:
            trace.append("Delay is under 3 hours: qualifies for ₹500 meal voucher.")
            allowed_actions = ["₹500 meal voucher"]
            action_items.append({"type": "MEAL_VOUCHER", "amount_inr": 500, "status": "ISSUED"})
            prohibited_actions.extend(["Lounge access", "Hotel accommodation"])
            rationale = (
                f"Flight delayed by {delay_hours:.1f} hours (under 3 hours). "
                "Per policy, customer is entitled to a ₹500 meal voucher."
            )
            rule_id = "RULE_DELAY_UNDER_3H"

        elif 3.0 <= delay_hours <= 5.0:
            # "Delay more than 3 hours: meal voucher + lounge access"
            trace.append("Delay is between 3 and 5 hours: qualifies for meal voucher + lounge access.")
            allowed_actions = ["₹500 meal voucher", "Lounge access"]
            action_items.append({"type": "MEAL_VOUCHER", "amount_inr": 500, "status": "ISSUED"})
            action_items.append({"type": "LOUNGE_ACCESS", "status": "GRANTED"})
            prohibited_actions.append("Hotel accommodation (requires delay > 5 hours)")
            rationale = (
                f"Flight is delayed by {delay_hours:.1f} hours (more than 3 hours, up to 5 hours). "
                "Per policy, customer is entitled to a ₹500 meal voucher and lounge access. "
                "Hotel accommodation is NOT eligible as hotel policy requires a delay of more than 5 hours."
            )
            rule_id = "RULE_DELAY_3H_TO_5H"

        else:
            # "Delay more than 5 hours: meal voucher + hotel accommodation, covering only delayed hours (not full night)"
            trace.append("Delay is greater than 5 hours: qualifies for meal voucher, lounge access, and delayed-hours hotel.")
            allowed_actions = [
                "₹500 meal voucher",
                "Lounge access",
                "Hotel accommodation (covering only delayed hours, not a full night's stay)",
            ]
            action_items.append({"type": "MEAL_VOUCHER", "amount_inr": 500, "status": "ISSUED"})
            action_items.append({"type": "LOUNGE_ACCESS", "status": "GRANTED"})
            action_items.append({
                "type": "HOTEL_ACCOMMODATION",
                "scope": "delayed_hours_only",
                "duration_hours": delay_hours,
                "status": "ARRANGED",
            })
            prohibited_actions.append("Full night's hotel stay (only delayed hours are covered)")
            rationale = (
                f"Flight is delayed by {delay_hours:.1f} hours (more than 5 hours). "
                "Per policy, customer is entitled to a ₹500 meal voucher, lounge access, "
                "and hotel accommodation covering ONLY the delayed hours (not a full night's stay)."
            )
            rule_id = "RULE_DELAY_MORE_THAN_5H"

        if customer_tier in ["Gold", "Platinum"]:
            trace.append(f"{customer_tier} tier verified: standard policy compensation applies without additional tier compensation.")

        return PolicyDecision(
            decision=DecisionType.RESOLVED,
            rule_id=rule_id,
            rule_name="Delay Compensation Rule",
            rationale=rationale,
            allowed_actions=allowed_actions,
            prohibited_actions=prohibited_actions,
            action_items=action_items,
            policy_reference="Delay Compensation Rule & Loyalty Tier Rule",
            trace_steps=trace,
        )

    # -------------------------------------------------------------------------
    # Hotel Eligibility Evaluator
    # -------------------------------------------------------------------------
    def evaluate_hotel_request(
        self,
        delay_hours: float,
        is_full_night_requested: bool = False,
    ) -> PolicyDecision:
        """
        Evaluates explicit hotel accommodation requests.
        Rule: Hotel accommodation applies ONLY for delays > 5 hours,
        covering ONLY delayed hours (not a full night's stay).
        """
        trace = [
            f"Checking hotel eligibility: delay = {delay_hours:.1f}h, full_night_requested = {is_full_night_requested}",
        ]

        if delay_hours <= self.HOTEL_MIN_DELAY_HOURS:
            trace.append(f"Delay ({delay_hours:.1f}h) <= {self.HOTEL_MIN_DELAY_HOURS}h threshold -> INELIGIBLE.")
            return PolicyDecision(
                decision=DecisionType.INELIGIBLE,
                rule_id="RULE_HOTEL_THRESHOLD_NOT_MET",
                rule_name="Delay Compensation Rule - Hotel Policy",
                rationale=(
                    f"Your flight delay is {delay_hours:.1f} hours. Under airline policy, "
                    f"hotel accommodation is provided only when a delay exceeds {self.HOTEL_MIN_DELAY_HOURS:g} hours. "
                    "Therefore, hotel accommodation cannot be provided."
                ),
                allowed_actions=["₹500 meal voucher", "Lounge access"] if delay_hours > 3.0 else ["₹500 meal voucher"],
                prohibited_actions=["Hotel accommodation for delays of 5 hours or less"],
                policy_reference="Delay Compensation Rule: Delay more than 5 hours",
                trace_steps=trace,
            )

        # Delay > 5h:
        if is_full_night_requested:
            trace.append("Delay > 5h, but customer requested full night's stay -> Only delayed hours permitted.")
            return PolicyDecision(
                decision=DecisionType.RESOLVED,
                rule_id="RULE_HOTEL_DELAYED_HOURS_ONLY",
                rule_name="Delay Compensation Rule - Hotel Policy",
                rationale=(
                    f"Your flight is delayed by {delay_hours:.1f} hours, which qualifies for hotel accommodation. "
                    "However, under airline policy, hotel accommodation covers ONLY the delayed-hours portion "
                    "and does not provide a full night's stay. We can arrange accommodation strictly for the duration of the delay."
                ),
                allowed_actions=[
                    f"Hotel accommodation covering only the {delay_hours:.1f}-hour delay period",
                    "₹500 meal voucher",
                    "Lounge access",
                ],
                prohibited_actions=[
                    "Full night's hotel stay (exceeds policy scope)",
                ],
                action_items=[
                    {"type": "MEAL_VOUCHER", "amount_inr": 500, "status": "ISSUED"},
                    {"type": "LOUNGE_ACCESS", "status": "GRANTED"},
                    {
                        "type": "HOTEL_ACCOMMODATION",
                        "scope": "delayed_hours_only",
                        "duration_hours": delay_hours,
                        "status": "APPROVED_PARTIAL",
                    }
                ],
                policy_reference="Delay Compensation Rule: Delay more than 5 hours (covering only the delayed hours)",
                trace_steps=trace,
            )

        # Standard delayed hours hotel
        trace.append(f"Delay > 5h ({delay_hours:.1f}h) -> Hotel accommodation covering delayed hours approved.")
        return PolicyDecision(
            decision=DecisionType.RESOLVED,
            rule_id="RULE_HOTEL_ELIGIBLE",
            rule_name="Delay Compensation Rule - Hotel Policy",
            rationale=(
                f"Flight delay of {delay_hours:.1f} hours qualifies for hotel accommodation covering the delayed-hours portion."
            ),
            allowed_actions=["Hotel accommodation for delayed hours", "₹500 meal voucher", "Lounge access"],
            action_items=[
                {
                    "type": "HOTEL_ACCOMMODATION",
                    "scope": "delayed_hours_only",
                    "duration_hours": delay_hours,
                    "status": "ARRANGED",
                }
            ],
            policy_reference="Delay Compensation Rule: Delay more than 5 hours",
            trace_steps=trace,
        )

    # -------------------------------------------------------------------------
    # Fare Difference Rule & Agent Waiver Authority
    # -------------------------------------------------------------------------
    def evaluate_fare_difference_waiver(
        self,
        fare_difference_inr: float,
        is_voluntary: bool = True,
    ) -> PolicyDecision:
        """
        Fare Difference Rule:
        If a customer voluntarily chooses to rebook on a higher-fare flight (not airline-caused),
        they must pay the fare difference. Agents cannot waive fare differences above ₹1,500
        without supervisor approval.
        """
        trace = [
            f"Evaluating voluntary rebooking fare difference: ₹{fare_difference_inr:,.2f}",
            f"Agent waiver ceiling: ₹{self.AGENT_FARE_DIFFERENCE_LIMIT_INR:,.2f}",
        ]

        if not is_voluntary:
            trace.append("Disruption is airline-caused: rebooking is free of charge.")
            return PolicyDecision(
                decision=DecisionType.RESOLVED,
                rule_id="RULE_AIRLINE_CAUSED_NO_FARE_DIFF",
                rule_name="Cancellation Rebooking Rule",
                rationale="For airline-caused disruptions, rebooking on the next available flight within 24 hours is free of charge.",
                allowed_actions=["Free rebooking within 24 hours"],
                trace_steps=trace,
            )

        if fare_difference_inr <= 0:
            trace.append("Fare difference is zero or negative.")
            return PolicyDecision(
                decision=DecisionType.RESOLVED,
                rule_id="RULE_NO_FARE_DIFFERENCE",
                rule_name="Fare Difference Rule",
                rationale="No additional fare difference is required for this flight change.",
                allowed_actions=["Rebooking at no extra charge"],
                trace_steps=trace,
            )

        if fare_difference_inr <= self.AGENT_FARE_DIFFERENCE_LIMIT_INR:
            trace.append(f"Fare difference ₹{fare_difference_inr:,.2f} is within agent authority (<= ₹1,500).")
            return PolicyDecision(
                decision=DecisionType.RESOLVED,
                rule_id="RULE_FARE_DIFF_WITHIN_AUTHORITY",
                rule_name="Fare Difference Rule",
                rationale=(
                    f"The fare difference is ₹{fare_difference_inr:,.2f}, which is within the "
                    f"agent waiver authority limit of ₹{self.AGENT_FARE_DIFFERENCE_LIMIT_INR:,.2f}. "
                    "Customer must pay the difference or an authorized waiver may be applied up to ₹1,500."
                ),
                allowed_actions=[f"Apply agent waiver up to ₹{self.AGENT_FARE_DIFFERENCE_LIMIT_INR:,.2f}"],
                action_items=[{
                    "type": "FARE_DIFFERENCE_WAIVER",
                    "amount_inr": fare_difference_inr,
                    "status": "WITHIN_AGENT_AUTHORITY",
                }],
                policy_reference="Fare Difference Rule: Agents cannot waive fare differences above ₹1,500 without supervisor approval",
                trace_steps=trace,
            )

        # Exceeds ₹1,500: STRICT ESCALATION REQUIRED
        trace.append(
            f"Fare difference ₹{fare_difference_inr:,.2f} EXCEEDS agent authority threshold of ₹{self.AGENT_FARE_DIFFERENCE_LIMIT_INR:,.2f} -> ESCALATE TO SUPERVISOR."
        )
        return PolicyDecision(
            decision=DecisionType.ESCALATE,
            rule_id="RULE_FARE_DIFF_EXCEEDS_AUTHORITY",
            rule_name="Prohibited Action: Waiving Fare Difference Above ₹1,500",
            rationale=(
                f"The requested flight has a fare difference of ₹{fare_difference_inr:,.2f}. "
                f"Under policy, frontline agents cannot waive fare differences above ₹{self.AGENT_FARE_DIFFERENCE_LIMIT_INR:,.2f} "
                "without supervisor approval. This request must be escalated to a supervisor for review."
            ),
            allowed_actions=["Customer pays ₹2,000 fare difference", "Escalate to supervisor for waiver exception"],
            prohibited_actions=[f"Automated waiver of fare difference above ₹{self.AGENT_FARE_DIFFERENCE_LIMIT_INR:,.2f}"],
            escalation_required=True,
            escalation_reason=(
                f"Requested fare-difference waiver of ₹{fare_difference_inr:,.2f} exceeds "
                f"the agent's ₹{self.AGENT_FARE_DIFFERENCE_LIMIT_INR:,.2f} authority."
            ),
            required_human_action="Supervisor approval required to waive fare difference exceeding ₹1,500.",
            policy_reference="Fare Difference Rule & Prohibited Actions (Waiving a fare difference above ₹1,500)",
            trace_steps=trace,
        )

    # -------------------------------------------------------------------------
    # Cabin Class / Upgrade Request Evaluator
    # -------------------------------------------------------------------------
    def evaluate_upgrade_request(
        self,
        customer_tier: str,
        flight_type: str = "return",
    ) -> PolicyDecision:
        """
        Evaluates requests for complimentary cabin class upgrades.
        Rule: The supplied policy does NOT provide free Business Class upgrades
        for disruptions or loyalty tiers (Gold/Platinum get priority rebooking only).
        """
        trace = [
            f"Evaluating complimentary upgrade request for {customer_tier} tier customer on {flight_type} flight.",
            "Checking policy for complimentary business class upgrades...",
        ]

        trace.append("No rule permits complimentary cabin upgrade for flight disruption or tier status.")
        return PolicyDecision(
            decision=DecisionType.INELIGIBLE,
            rule_id="RULE_COMPLIMENTARY_UPGRADE_PROHIBITED",
            rule_name="Loyalty Tier & Disruption Policy",
            rationale=(
                "Under airline policy, flight disruptions and loyalty tier status (including Gold and Platinum) "
                "entitle customers to priority rebooking, but do NOT provide complimentary upgrades to Business Class. "
                "We cannot provide a free cabin class upgrade."
            ),
            allowed_actions=["Priority rebooking in original cabin class (Economy)"],
            prohibited_actions=["Complimentary upgrade to Business Class (not supported by policy)"],
            policy_reference="Loyalty Tier Rule & Prohibited Actions: Approving compensation beyond stated policy amounts",
            trace_steps=trace,
        )

    # -------------------------------------------------------------------------
    # Comprehensive Escalation Detection
    # -------------------------------------------------------------------------
    def check_escalation_required(
        self,
        user_message: str,
        fare_difference_inr: Optional[float] = None,
        refund_method_different: bool = False,
        non_airline_caused: bool = False,
        unsupported_compensation_requested: bool = False,
    ) -> Optional[PolicyDecision]:
        """
        Strictly enforces the 5 mandatory prohibited escalation triggers:
        1. Approving compensation beyond stated policy amounts
        2. Waiving fare difference above ₹1,500
        3. Making exceptions for non-airline-caused disruptions
        4. Handling threats of legal action or formal complaints
        5. Processing refunds to a different payment method than original
        """
        text_lower = user_message.lower()

        # 1. Threat of legal action or formal complaint
        legal_keywords = [
            "legal action", "lawyer", "attorney", "sue", "court",
            "formal complaint", "consumer forum", "consumer court",
            "file a complaint", "regulatory complaint", "take legal"
        ]
        for kw in legal_keywords:
            if kw in text_lower:
                return PolicyDecision(
                    decision=DecisionType.ESCALATE,
                    rule_id="ESCALATE_LEGAL_FORMAL_COMPLAINT",
                    rule_name="Prohibited Action: Legal Action / Formal Complaint",
                    rationale=(
                        "Customer has indicated an intention of legal action or filing a formal complaint. "
                        "Policy mandates immediate escalation to the specialist support / legal escalation team."
                    ),
                    escalation_required=True,
                    escalation_reason=f"Customer mentioned: '{kw}'. Prohibited action for automated agent.",
                    required_human_action="Immediate transfer to specialist customer relations / legal escalation team.",
                    policy_reference="Prohibited Actions: Handling threats of legal action or formal complaints — must be escalated immediately",
                    trace_steps=[
                        f"Detected legal/formal complaint trigger matching '{kw}' in customer message.",
                        "Enforcing immediate escalation gate.",
                    ],
                )

        # 2. Fare difference above ₹1,500
        if fare_difference_inr is not None and fare_difference_inr > self.AGENT_FARE_DIFFERENCE_LIMIT_INR:
            return self.evaluate_fare_difference_waiver(fare_difference_inr, is_voluntary=True)

        # 3. Refund to a different payment method
        if refund_method_different or any(k in text_lower for k in [
            "different card", "another account", "cash instead", "different payment method", "send to another bank"
        ]):
            return PolicyDecision(
                decision=DecisionType.ESCALATE,
                rule_id="ESCALATE_REFUND_METHOD_MISMATCH",
                rule_name="Prohibited Action: Alternate Payment Method Refund",
                rationale=(
                    "Under Refund Processing Rule, refunds must be issued strictly to the original payment method only. "
                    "Processing refunds to a different payment method is prohibited and requires human compliance review."
                ),
                escalation_required=True,
                escalation_reason="Customer requested refund to an alternate payment method.",
                required_human_action="Finance & compliance team verification for payment method exception.",
                policy_reference="Refund Processing Rule & Prohibited Actions: Processing refunds to a different payment method",
                trace_steps=[
                    "Customer requested refund to a non-original payment destination.",
                    "Flagged prohibited refund deviation -> Escalate to human supervisor.",
                ],
            )

        # 4. Non-airline-caused disruption exception
        if non_airline_caused or any(k in text_lower for k in [
            "i woke up late", "missed my flight", "traffic delay", "my personal emergency", "customer missed"
        ]):
            return PolicyDecision(
                decision=DecisionType.ESCALATE,
                rule_id="ESCALATE_NON_AIRLINE_EXCEPTION",
                rule_name="Prohibited Action: Non-Airline Disruption Exception",
                rationale=(
                    "Making exceptions for non-airline-caused disruptions (e.g. passenger missing the flight) "
                    "is strictly prohibited for the automated agent and requires human agent review."
                ),
                escalation_required=True,
                escalation_reason="Exception requested for non-airline-caused disruption.",
                required_human_action="Human supervisor evaluation for personal missed flight exception.",
                policy_reference="Prohibited Actions: Making exceptions for non-airline-caused disruptions",
                trace_steps=[
                    "Identified non-airline disruption circumstance in conversation.",
                    "Triggering human agent transfer per policy.",
                ],
            )

        # 5. Unsupported compensation
        if unsupported_compensation_requested:
            return PolicyDecision(
                decision=DecisionType.ESCALATE,
                rule_id="ESCALATE_UNSUPPORTED_COMPENSATION",
                rule_name="Prohibited Action: Compensation Beyond Stated Policy",
                rationale=(
                    "Customer requested compensation amounts beyond the stated service policy. "
                    "Frontline automated agent cannot approve compensation beyond policy."
                ),
                escalation_required=True,
                escalation_reason="Requested compensation exceeds stated policy amounts.",
                required_human_action="Supervisor authorization required for ex-gratia compensation request.",
                policy_reference="Prohibited Actions: Approving any compensation beyond the stated policy amounts",
                trace_steps=[
                    "Compensation request exceeds published policy thresholds.",
                    "Routing to human supervisor for review.",
                ],
            )

        return None
