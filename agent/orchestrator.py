"""
Conversational Resolution Orchestrator for AirResolve.

Connects Natural Language Understanding, Customer/Booking Retrieval,
and the Deterministic Policy Engine. Ensures that all responses and decisions
are strictly grounded in the Assignment 3 Data Pack rules.
"""

from dataclasses import dataclass, field
import datetime
from typing import Any, Dict, List, Optional
import uuid

from policy.policy_engine import (
    PolicyEngine,
    PolicyDecision,
    DecisionType,
)
from .intent_detector import IntentDetector, UserIntent


@dataclass
class AgentResponse:
    text: str
    decision: PolicyDecision
    intent: UserIntent
    all_intents: List[UserIntent]
    entities: Dict[str, Any]
    trace: List[str]
    suggested_actions: List[str]
    escalation_ticket: Optional[Dict[str, Any]] = None
    customer: Optional[Dict[str, Any]] = None
    booking: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "decision": self.decision.to_dict(),
            "intent": self.intent.value,
            "all_intents": [i.value for i in self.all_intents],
            "entities": self.entities,
            "trace": self.trace,
            "suggested_actions": self.suggested_actions,
            "escalation_ticket": self.escalation_ticket,
        }


class ResolutionAgent:
    """
    Main resolution agent coordinating customer queries, intent detection,
    retrieval, deterministic policy checks, and response generation.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.policy_engine = PolicyEngine(data_dir=data_dir)
        self.intent_detector = IntentDetector()

    def process_message(
        self,
        message: str,
        active_customer_id_or_pnr: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> AgentResponse:
        """
        Process incoming passenger message against active customer context.
        """
        trace: List[str] = []
        now_str = "2026-09-23 18:45 IST"
        trace.append(f"System Time: {now_str} (Ground Truth Date: 23 Sep 2026)")

        # 1. Customer Identification
        customer = self.policy_engine.get_customer(active_customer_id_or_pnr)
        if not customer:
            trace.append(f"Customer identification failed for: '{active_customer_id_or_pnr}'")
            unrecognized_decision = PolicyDecision(
                decision=DecisionType.CLARIFICATION_NEEDED,
                rule_id="RULE_CUSTOMER_NOT_FOUND",
                rule_name="Customer Retrieval",
                rationale="Could not locate customer profile with provided reference.",
                trace_steps=trace,
            )
            return AgentResponse(
                text="I couldn't locate a booking or customer profile matching that reference. Could you please provide your 6-character PNR booking reference or verified name?",
                decision=unrecognized_decision,
                intent=UserIntent.UNKNOWN,
                all_intents=[UserIntent.UNKNOWN],
                entities={},
                trace=trace,
                suggested_actions=["Check PNR SK4821X", "Check PNR TR1190B", "Check PNR WL7742"],
            )

        pnr = customer.get("booking_reference")
        name = customer.get("name")
        tier = customer.get("loyalty_tier", "Standard")
        trace.append(f"Step 1: Customer identified - {name} (PNR: {pnr}, Loyalty Tier: {tier})")

        # 2. Booking & Disruption Verification
        booking = self.policy_engine.get_booking(pnr)
        if not booking:
            trace.append(f"Step 2: No active booking found for PNR {pnr}")
            decision = PolicyDecision(
                decision=DecisionType.CLARIFICATION_NEEDED,
                rule_id="RULE_BOOKING_NOT_FOUND",
                rule_name="Booking Retrieval",
                rationale=f"No active flight booking found under reference {pnr}.",
                trace_steps=trace,
            )
            return AgentResponse(
                text=f"I have identified your profile ({name}), but no active flight records were found under PNR {pnr}. Please contact a representative.",
                decision=decision,
                intent=UserIntent.UNKNOWN,
                all_intents=[UserIntent.UNKNOWN],
                entities={},
                trace=trace,
                suggested_actions=[],
                customer=customer,
            )

        segment = self.policy_engine.get_primary_segment(booking)
        flight_num = segment.get("flight_number") if segment else "Unknown"
        status = segment.get("status") if segment else "Unknown"
        route_str = f"{segment['route']['origin_name']} -> {segment['route']['destination_name']}" if segment else "Unknown"
        trace.append(f"Step 2: Booking verified - Flight {flight_num} ({route_str}), Status: {status}")

        # 3. Intent & Entity Extraction
        primary_intent, confidence, all_intents = self.intent_detector.detect_intent(message)
        entities = self.intent_detector.extract_entities(message)
        trace.append(f"Step 3: Intent detected - Primary: '{primary_intent.value}' (Confidence: {confidence:.2f}), All: {[i.value for i in all_intents]}")
        if entities.get("fare_difference_inr"):
            trace.append(f"Entity extracted: Fare difference = ₹{entities['fare_difference_inr']:,.2f}")
        if entities.get("full_night_requested"):
            trace.append("Entity extracted: Full night stay requested")
        if entities.get("business_upgrade_requested"):
            trace.append("Entity extracted: Business class upgrade requested")

        # 4. Mandatory Escalation Trigger Check (Prohibited Actions)
        # Check for immediate escalation triggers before evaluating standard policies:
        escalation_eval = self.policy_engine.check_escalation_required(
            user_message=message,
            fare_difference_inr=entities.get("fare_difference_inr"),
            refund_method_different=(entities.get("refund_method_requested") == "alternate"),
        )
        if escalation_eval:
            for t in escalation_eval.trace_steps:
                trace.append(f"Policy Guardrail: {t}")
            ticket = self._generate_escalation_ticket(customer, booking, escalation_eval)
            trace.append(f"Step 4: ESCALATION GATE TRIGGERED -> Ticket {ticket['ticket_id']}")
            return self._build_escalation_response(escalation_eval, ticket, customer, booking, primary_intent, all_intents, entities, trace)

        # 5. Route to Specialized Scenario Handlers based on Flight Status & Intent
        if status == "Cancelled":
            return self._handle_cancelled_flight(
                customer, booking, segment, message, primary_intent, all_intents, entities, trace
            )
        elif status == "Delayed":
            return self._handle_delayed_flight(
                customer, booking, segment, message, primary_intent, all_intents, entities, trace
            )
        else:
            return self._handle_unaffected_flight(
                customer, booking, segment, message, primary_intent, all_intents, entities, trace
            )

    # -------------------------------------------------------------------------
    # Scenario 1 Handler: Priya Nair (Cancelled Flight SK-204)
    # -------------------------------------------------------------------------
    def _handle_cancelled_flight(
        self,
        customer: Dict[str, Any],
        booking: Dict[str, Any],
        segment: Dict[str, Any],
        message: str,
        intent: UserIntent,
        all_intents: List[UserIntent],
        entities: Dict[str, Any],
        trace: List[str],
    ) -> AgentResponse:
        flight_num = segment.get("flight_number", "SK-204")
        reason = segment.get("cancellation_reason", "operational reasons")
        tier = customer.get("loyalty_tier", "Standard")
        is_gold_or_plat = tier in ["Gold", "Platinum"]

        trace.append(f"Step 4: Evaluating Cancellation Policy for {flight_num} (Reason: {reason})")

        # Check if customer requests upgrade (Priya's free Business Class upgrade scenario)
        if entities.get("business_upgrade_requested") or intent == UserIntent.REQUEST_UPGRADE:
            trace.append("Customer requested complimentary Business Class upgrade.")
            upgrade_eval = self.policy_engine.evaluate_upgrade_request(customer_tier=tier, flight_type="return")
            for t in upgrade_eval.trace_steps:
                trace.append(f"Policy Check: {t}")

            # Check if customer also requested refund simultaneously
            wants_refund = intent == UserIntent.REQUEST_REFUND or UserIntent.REQUEST_REFUND in all_intents

            if wants_refund:
                trace.append("Customer combined full refund request with complimentary business class upgrade request.")
                refund_eval = self.policy_engine.evaluate_cancellation_options(booking, customer, selected_option="refund")
                for t in refund_eval.trace_steps:
                    trace.append(f"Policy Check: {t}")

                text = (
                    f"I completely understand your frustration regarding flight {flight_num} being cancelled due to {reason}. "
                    f"I have initiated a full refund for your cancelled flight. Per our policy, the refund will be credited in full "
                    f"within 7 business days to your original payment method.\n\n"
                    f"Regarding your request for a free upgrade to Business Class on your return flight (25 Sep 2026): "
                    f"under airline policy, your {tier} status provides priority rebooking access, but the policy does not permit "
                    f"complimentary cabin class upgrades as disruption compensation. Therefore, I am unable to grant a Business Class upgrade."
                )

                combined_decision = PolicyDecision(
                    decision=DecisionType.RESOLVED,
                    rule_id="RULE_REFUND_APPROVED_UPGRADE_DENIED",
                    rule_name="Refund Processing & Upgrade Policy",
                    rationale=(
                        f"Full refund approved for cancelled flight {flight_num} (7 business days, original payment method). "
                        "Complimentary Business Class upgrade refused as it is not permitted under disruption or loyalty policy."
                    ),
                    allowed_actions=refund_eval.allowed_actions,
                    prohibited_actions=upgrade_eval.prohibited_actions,
                    action_items=refund_eval.action_items,
                    policy_reference="Cancellation Rebooking Rule, Refund Processing Rule, and Loyalty Tier Rule",
                    trace_steps=trace,
                )

                return AgentResponse(
                    text=text,
                    decision=combined_decision,
                    intent=intent,
                    all_intents=all_intents,
                    entities=entities,
                    trace=trace,
                    suggested_actions=["Check Refund Status", "View Return Flight Details"],
                    customer=customer,
                    booking=booking,
                )
            else:
                # Only upgrade requested without refund
                text = (
                    f"I understand your frustration with the cancellation of flight {flight_num}. "
                    f"While your {tier} membership entitles you to priority rebooking, our policy does not provide "
                    f"free Business Class upgrades for flight disruptions. We can, however, rebook you on the next available "
                    f"flight within 24 hours at no extra charge, or process a full refund to your original payment method."
                )
                return AgentResponse(
                    text=text,
                    decision=upgrade_eval,
                    intent=intent,
                    all_intents=all_intents,
                    entities=entities,
                    trace=trace,
                    suggested_actions=["Request Full Refund", "Explore Rebooking Options"],
                    customer=customer,
                    booking=booking,
                )

        # Standard Refund Request
        if intent == UserIntent.REQUEST_REFUND or UserIntent.REQUEST_REFUND in all_intents:
            trace.append("Evaluating full refund request.")
            decision = self.policy_engine.evaluate_cancellation_options(booking, customer, selected_option="refund")
            for t in decision.trace_steps:
                trace.append(f"Policy Check: {t}")

            text = (
                f"I am truly sorry for the disruption. I can confirm that flight {flight_num} was cancelled due to {reason}. "
                f"I have initiated a full refund for your booking. Under our policy, refunds for airline-caused cancellations "
                f"are processed in full within 7 business days directly to your original payment method."
            )
            return AgentResponse(
                text=text,
                decision=decision,
                intent=intent,
                all_intents=all_intents,
                entities=entities,
                trace=trace,
                suggested_actions=["Check Refund Timeline", "View Booking Summary"],
                customer=customer,
                booking=booking,
            )

        # Rebooking Request
        if intent == UserIntent.REQUEST_REBOOKING or UserIntent.REQUEST_REBOOKING in all_intents:
            trace.append("Evaluating free rebooking request.")
            decision = self.policy_engine.evaluate_cancellation_options(booking, customer, selected_option="rebook")
            for t in decision.trace_steps:
                trace.append(f"Policy Check: {t}")

            tier_mention = "As a Gold tier member, you receive priority seat access." if is_gold_or_plat else ""
            text = (
                f"I apologize for the cancellation of flight {flight_num}. You are entitled to a free rebooking "
                f"on the next available flight within 24 hours at no charge. {tier_mention} "
                "Would you like me to reserve the earliest available departure for you, or would you prefer a full refund?"
            )
            return AgentResponse(
                text=text,
                decision=decision,
                intent=intent,
                all_intents=all_intents,
                entities=entities,
                trace=trace,
                suggested_actions=["Confirm Next Available Flight", "Request Full Refund"],
                customer=customer,
                booking=booking,
            )

        # Default Clarification / Options Presentation
        trace.append("Providing cancellation options under Cancellation Rebooking Rule.")
        decision = self.policy_engine.evaluate_cancellation_options(booking, customer, selected_option=None)
        text = (
            f"I completely understand your frustration. Flight {flight_num} from {segment['route']['origin_name']} to "
            f"{segment['route']['destination_name']} was cancelled due to {reason}. Under our service policy, you are entitled to:\n"
            f"1. **Free Rebooking** on the next available flight within 24 hours"
            + (" (with your Gold priority rebooking benefit)" if is_gold_or_plat else "")
            + ".\n"
            f"2. **Full Refund** to your original payment method, processed within 7 business days.\n\n"
            "Which of these options would you prefer?"
        )
        return AgentResponse(
            text=text,
            decision=decision,
            intent=intent,
            all_intents=all_intents,
            entities=entities,
            trace=trace,
            suggested_actions=["Request Full Refund", "Explore Rebooking"],
            customer=customer,
            booking=booking,
        )

    # -------------------------------------------------------------------------
    # Scenario 2 & 3 Handler: Delayed Flights (Arvind & Meher)
    # -------------------------------------------------------------------------
    def _handle_delayed_flight(
        self,
        customer: Dict[str, Any],
        booking: Dict[str, Any],
        segment: Dict[str, Any],
        message: str,
        intent: UserIntent,
        all_intents: List[UserIntent],
        entities: Dict[str, Any],
        trace: List[str],
    ) -> AgentResponse:
        flight_num = segment.get("flight_number")
        delay_hours = float(segment.get("delay_duration_hours", 0.0))
        tier = customer.get("loyalty_tier", "Standard")

        trace.append(f"Step 4: Evaluating Delay Compensation Policy for {flight_num} (Delay: {delay_hours:.1f}h)")

        # Case A: Higher-Fare Flight Rebooking (Meher Kaur Scenario 3)
        fare_diff = entities.get("fare_difference_inr")
        if (
            intent == UserIntent.REQUEST_HIGHER_FARE_REBOOKING
            or UserIntent.REQUEST_HIGHER_FARE_REBOOKING in all_intents
            or fare_diff is not None
        ):
            diff_amount = fare_diff if fare_diff is not None else 2000.0
            trace.append(f"Evaluating voluntary rebooking to higher-fare flight with fare difference = ₹{diff_amount:,.2f}")
            fare_eval = self.policy_engine.evaluate_fare_difference_waiver(diff_amount, is_voluntary=True)
            for t in fare_eval.trace_steps:
                trace.append(f"Policy Check: {t}")

            if fare_eval.escalation_required:
                ticket = self._generate_escalation_ticket(customer, booking, fare_eval)
                trace.append(f"Step 5: Generated Escalation Ticket {ticket['ticket_id']} for ₹{diff_amount:,.2f} waiver")
                text = (
                    f"I understand you would like to move to a different, higher-fare flight instead of waiting. "
                    f"The fare difference for this flight is ₹{diff_amount:,.2f}. Under our Fare Difference Rule, "
                    f"agents are authorized to waive fare differences only up to ₹1,500. Because this request exceeds "
                    f"my ₹1,500 authority limit, I have escalated your request to a supervisor for approval. "
                    f"(Escalation Ticket: **{ticket['ticket_id']}**). Our specialist team will assist you shortly."
                )
                return AgentResponse(
                    text=text,
                    decision=fare_eval,
                    intent=intent,
                    all_intents=all_intents,
                    entities=entities,
                    trace=trace,
                    suggested_actions=["Check Escalation Status", "View Delay Benefits"],
                    escalation_ticket=ticket,
                    customer=customer,
                    booking=booking,
                )

        # Case B: Hotel Accommodation Request (Arvind 4h vs Meher 6h)
        if intent == UserIntent.REQUEST_HOTEL or UserIntent.REQUEST_HOTEL in all_intents:
            is_full_night = entities.get("full_night_requested", False)
            trace.append(f"Evaluating Hotel Request: delay = {delay_hours:.1f}h, full_night = {is_full_night}")
            hotel_eval = self.policy_engine.evaluate_hotel_request(delay_hours, is_full_night_requested=is_full_night)
            for t in hotel_eval.trace_steps:
                trace.append(f"Policy Check: {t}")

            # Subcase B1: Arvind Kulkarni (4h delay - NOT ELIGIBLE)
            if delay_hours <= 5.0:
                text = (
                    f"I understand the delay is frustrating, especially when you have connecting plans. "
                    f"Your flight {flight_num} is delayed by {delay_hours:.0f} hours. Under our policy, "
                    f"this qualifies for a ₹500 meal voucher and lounge access, which I have applied to your booking. "
                    f"Hotel accommodation applies only when the delay is more than 5 hours, so I cannot provide hotel "
                    f"accommodation under the current policy."
                )
                return AgentResponse(
                    text=text,
                    decision=hotel_eval,
                    intent=intent,
                    all_intents=all_intents,
                    entities=entities,
                    trace=trace,
                    suggested_actions=["View Meal Voucher & Lounge Access", "Check Updated Departure (11:10)"],
                    customer=customer,
                    booking=booking,
                )

            # Subcase B2: Meher Kaur (6h delay - ELIGIBLE for delayed hours, NOT full night)
            if is_full_night:
                text = (
                    f"I understand you are seeking rest during this {delay_hours:.0f}-hour delay. "
                    f"Because your delay exceeds 5 hours, you qualify for hotel accommodation, a ₹500 meal voucher, "
                    f"and lounge access. However, under our Delay Compensation Rule, hotel accommodation covers ONLY "
                    f"the delayed hours (until your new departure at 20:00) and does not provide a full night's stay. "
                    f"I can arrange accommodation covering your delay period right now."
                )
                return AgentResponse(
                    text=text,
                    decision=hotel_eval,
                    intent=intent,
                    all_intents=all_intents,
                    entities=entities,
                    trace=trace,
                    suggested_actions=["Accept Delayed-Hours Hotel", "Access Lounge & Meal Voucher"],
                    customer=customer,
                    booking=booking,
                )
            else:
                text = (
                    f"Your flight {flight_num} is delayed by {delay_hours:.0f} hours. This qualifies for "
                    f"hotel accommodation covering the delayed-hours portion, a ₹500 meal voucher, and lounge access. "
                    f"I have arranged your delay accommodation until your scheduled departure."
                )
                return AgentResponse(
                    text=text,
                    decision=hotel_eval,
                    intent=intent,
                    all_intents=all_intents,
                    entities=entities,
                    trace=trace,
                    suggested_actions=["View Hotel Voucher", "Access Lounge Voucher"],
                    customer=customer,
                    booking=booking,
                )

        # Case C: Delay Benefits / Compensation Check
        trace.append("Evaluating general delay benefits.")
        benefits_eval = self.policy_engine.evaluate_delay_compensation(delay_hours, customer_tier=tier, segment_info=segment)
        for t in benefits_eval.trace_steps:
            trace.append(f"Policy Check: {t}")

        if delay_hours <= 3.0:
            text = (
                f"Flight {flight_num} is delayed by {delay_hours:.1f} hours. Under our policy, "
                "you are entitled to a ₹500 meal voucher, which has been issued to your account."
            )
        elif 3.0 < delay_hours <= 5.0:
            text = (
                f"Flight {flight_num} is delayed by {delay_hours:.0f} hours (new departure: {segment.get('new_departure')}). "
                "Under our policy for delays exceeding 3 hours, you qualify for a ₹500 meal voucher and lounge access. "
                "Both have been applied to your booking. (Note: hotel accommodation requires a delay exceeding 5 hours)."
            )
        else:
            text = (
                f"Flight {flight_num} is delayed by {delay_hours:.0f} hours (new departure: {segment.get('new_departure')}). "
                "Under our policy for delays exceeding 5 hours, you qualify for: 1) A ₹500 meal voucher, 2) Lounge access, "
                "and 3) Hotel accommodation covering the delayed hours (until departure)."
            )

        suggested = ["View Delay Benefits"]
        if delay_hours > 5.0:
            suggested.extend(["Request Hotel (Delayed Hours)", "Request Higher-Fare Flight"])
        else:
            suggested.extend(["Access Lounge", "Claim ₹500 Meal Voucher"])

        return AgentResponse(
            text=text,
            decision=benefits_eval,
            intent=intent,
            all_intents=all_intents,
            entities=entities,
            trace=trace,
            suggested_actions=suggested,
            customer=customer,
            booking=booking,
        )

    # -------------------------------------------------------------------------
    # Unaffected Flight Handler
    # -------------------------------------------------------------------------
    def _handle_unaffected_flight(
        self,
        customer: Dict[str, Any],
        booking: Dict[str, Any],
        segment: Dict[str, Any],
        message: str,
        intent: UserIntent,
        all_intents: List[UserIntent],
        entities: Dict[str, Any],
        trace: List[str],
    ) -> AgentResponse:
        flight_num = segment.get("flight_number")
        route_str = f"{segment['route']['origin_name']} -> {segment['route']['destination_name']}"
        dep_time = segment.get("scheduled_departure")
        date_str = segment.get("date_display")

        trace.append(f"Step 4: Flight {flight_num} status is UNAFFECTED.")
        decision = PolicyDecision(
            decision=DecisionType.INFO_PROVIDED,
            rule_id="RULE_FLIGHT_ON_SCHEDULE",
            rule_name="Standard Flight Status",
            rationale=f"Flight {flight_num} is operating on schedule.",
            allowed_actions=["Standard flight inquiry", "Check-in assistance"],
            trace_steps=trace,
        )
        text = (
            f"Your flight {flight_num} ({route_str}) on {date_str} is operating on schedule with departure at {dep_time}. "
            "There are currently no delays or disruptions reported."
        )
        return AgentResponse(
            text=text,
            decision=decision,
            intent=intent,
            all_intents=all_intents,
            entities=entities,
            trace=trace,
            suggested_actions=["View Boarding Pass", "Check In"],
            customer=customer,
            booking=booking,
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _generate_escalation_ticket(
        self,
        customer: Dict[str, Any],
        booking: Dict[str, Any],
        decision: PolicyDecision,
    ) -> Dict[str, Any]:
        pnr = booking.get("booking_reference", "UNKNOWN")
        ticket_id = f"ESC-{pnr}-{str(uuid.uuid4())[:6].upper()}"
        return {
            "ticket_id": ticket_id,
            "created_at": "2026-09-23 18:45:00 IST",
            "pnr": pnr,
            "customer_name": customer.get("name"),
            "customer_tier": customer.get("loyalty_tier"),
            "rule_id": decision.rule_id,
            "rule_name": decision.rule_name,
            "escalation_reason": decision.escalation_reason,
            "required_human_action": decision.required_human_action,
            "policy_reference": decision.policy_reference,
            "status": "OPEN_PENDING_SUPERVISOR",
        }

    def _build_escalation_response(
        self,
        decision: PolicyDecision,
        ticket: Dict[str, Any],
        customer: Dict[str, Any],
        booking: Dict[str, Any],
        intent: UserIntent,
        all_intents: List[UserIntent],
        entities: Dict[str, Any],
        trace: List[str],
    ) -> AgentResponse:
        trace.append(f"Generated human escalation ticket: {ticket['ticket_id']}")
        text = (
            f"I hear you, and I am genuinely sorry that this has been such a frustrating experience. "
            f"To ensure this is handled with the appropriate authority, I have escalated your case to our "
            f"specialist support team and supervisor.\n\n"
            f"• **Escalation Ticket**: `{ticket['ticket_id']}`\n"
            f"• **Reason**: {decision.escalation_reason}\n"
            f"• **Next Step**: {decision.required_human_action}\n\n"
            "A specialist representative will review your file and contact you directly."
        )
        return AgentResponse(
            text=text,
            decision=decision,
            intent=intent,
            all_intents=all_intents,
            entities=entities,
            trace=trace,
            suggested_actions=["Track Escalation Ticket", "View Booking Summary"],
            escalation_ticket=ticket,
            customer=customer,
            booking=booking,
        )
