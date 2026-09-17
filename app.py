"""
AirResolve - Customer-Facing Airline Disruption Resolution Agent.
Assignment 3 Submission: Customer-Facing Resolution Agent (Airline Disruption).
"""

import json
import os
import streamlit as st

from agent.orchestrator import ResolutionAgent
from agent.intent_detector import UserIntent
from policy.policy_engine import DecisionType

# -----------------------------------------------------------------------------
# Streamlit Page Setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AirResolve | Airline Disruption Resolution",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "agent" not in st.session_state:
    st.session_state.agent = ResolutionAgent()

if "selected_pnr" not in st.session_state:
    st.session_state.selected_pnr = "SK4821X"  # Default: Priya Nair

if "chat_history" not in st.session_state:
    st.session_state.chat_history = {
        "SK4821X": [],
        "TR1190B": [],
        "WL7742": [],
    }

if "last_response" not in st.session_state:
    st.session_state.last_response = {
        "SK4821X": None,
        "TR1190B": None,
        "WL7742": None,
    }

agent: ResolutionAgent = st.session_state.agent

# -----------------------------------------------------------------------------
# Sidebar: Passenger Identification & Scenario Selection
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 10px 0 16px 0;">
            <div style="font-size: 32px;">✈️</div>
            <div style="font-size: 20px; font-weight: 800; color: #0B192C;">AirResolve</div>
            <div style="font-size: 11px; color: #64748B; letter-spacing: 0.5px; text-transform: uppercase; font-weight: 700;">
                Disruption Resolution Agent
            </div>
            <div style="font-size: 11px; background: #EEF2F6; color: #334155; padding: 4px 8px; border-radius: 6px; margin-top: 8px; display: inline-block;">
                📅 23 Sep 2026 (Operational Date)
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### Select Customer / Scenario")
    customer_options = {
        "SK4821X": "Priya Nair (Gold) — Cancelled SK-204",
        "TR1190B": "Arvind Kulkarni (Silver) — Delayed 4h SK-118",
        "WL7742": "Meher Kaur (Platinum) — Delayed 6h SK-305",
    }

    selected_pnr = st.selectbox(
        "Passenger Context",
        options=list(customer_options.keys()),
        format_func=lambda k: customer_options[k],
        index=list(customer_options.keys()).index(st.session_state.selected_pnr),
    )
    if selected_pnr != st.session_state.selected_pnr:
        st.session_state.selected_pnr = selected_pnr
        st.rerun()

    # Retrieve current customer & booking
    active_customer = agent.policy_engine.get_customer(st.session_state.selected_pnr)
    active_booking = agent.policy_engine.get_booking(st.session_state.selected_pnr)
    active_segment = agent.policy_engine.get_primary_segment(active_booking)

    # Customer Profile Card
    tier = active_customer.get("loyalty_tier", "Standard")
    tier_badge_class = f"badge-tier-{tier.lower()}"

    st.markdown(f"""
        <div class="air-card" style="margin-top: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 700; font-size: 15px; color: #0F172A;">{active_customer.get('name')}</span>
                <span class="{tier_badge_class}">{tier}</span>
            </div>
            <div style="font-size: 12px; color: #64748B; line-height: 1.6;">
                <b>PNR:</b> <code style="color: #008DDA;">{active_customer.get('booking_reference')}</code><br>
                <b>Email:</b> {active_customer['contact']['email']}<br>
                <b>Phone:</b> {active_customer['contact']['phone']}<br>
                <b>Past 12M:</b> {active_customer['travel_history_last_12m']['flights_count']} flights
            </div>
        </div>
    """, unsafe_allow_html=True)

    if active_customer["travel_history_last_12m"]["prior_complaints"]:
        complaint = active_customer["travel_history_last_12m"]["prior_complaints"][0]
        st.caption(f"⚠️ Prior note: {complaint['issue']} ({complaint['resolution']})")

    st.divider()

    # Scenario Quick Actions
    st.markdown("#### ⚡ Quick Scenario Prompts")
    st.caption("Inject exact Data Pack scenarios:")

    if st.session_state.selected_pnr == "SK4821X":
        if st.button("🔴 Scenario 1: Refund + Business Upgrade", use_container_width=True):
            st.session_state.pending_prompt = "I am furious! My flight is cancelled. I want a full cash refund plus a free upgrade to business class on my return flight for the trouble."
            st.rerun()
        if st.button("⚖️ Test Legal Action Escalation", use_container_width=True):
            st.session_state.pending_prompt = "This cancellation ruined my trip! I will take legal action against your company."
            st.rerun()

    elif st.session_state.selected_pnr == "TR1190B":
        if st.button("🟡 Scenario 2: Request Hotel (4h delay)", use_container_width=True):
            st.session_state.pending_prompt = "I'm frustrated about missing a connecting meeting and I need hotel accommodation since it's been such a long delay."
            st.rerun()
        if st.button("🍽️ Ask for Delay Benefits", use_container_width=True):
            st.session_state.pending_prompt = "What compensation and vouchers do I qualify for during this 4 hour delay?"
            st.rerun()

    elif st.session_state.selected_pnr == "WL7742":
        if st.button("🔵 Scenario 3A: Request Full Night Hotel", use_container_width=True):
            st.session_state.pending_prompt = "My flight is delayed 6 hours. I need a full night's hotel stay rather than coverage for just the delayed hours."
            st.rerun()
        if st.button("🚨 Scenario 3B: Higher-Fare Flight (₹2,000)", use_container_width=True):
            st.session_state.pending_prompt = "Move me onto a different, higher-fare flight instead of waiting. The fare difference is ₹2,000."
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.chat_history[st.session_state.selected_pnr] = []
        st.session_state.last_response[st.session_state.selected_pnr] = None
        st.rerun()


# -----------------------------------------------------------------------------
# Main Application Content
# -----------------------------------------------------------------------------
# Brand Banner
st.markdown("""
    <div class="brand-header">
        <div>
            <div class="brand-title">
                ✈️ AirResolve
                <span class="brand-badge">Policy Grounded</span>
            </div>
            <div class="brand-sub">
                "Let's get your journey back on track." — Deterministic Resolution & Disruption Care
            </div>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 11px; background: rgba(255,255,255,0.15); padding: 4px 10px; border-radius: 6px; font-weight: 600;">
                Deterministic Policy Engine Active
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Layout: 7 cols main chat, 5 cols right inspector
col_main, col_inspector = st.columns([7, 5], gap="large")

# -----------------------------------------------------------------------------
# Column 1: Flight Status Card & Main Interactive Chat
# -----------------------------------------------------------------------------
with col_main:
    # Disruption Overview Card
    seg = active_segment
    if seg:
        is_cancelled = seg.get("status") == "Cancelled"
        banner_class = "disruption-banner-cancelled" if is_cancelled else "disruption-banner-delayed"
        status_badge_class = "badge-cancelled" if is_cancelled else "badge-delayed"
        status_text = seg.get("status")

        disruption_desc = ""
        if is_cancelled:
            disruption_desc = f"Cancelled due to <b>{seg.get('cancellation_reason')}</b>"
        else:
            disruption_desc = f"<b>{seg.get('delay_description')}</b> (Original: {seg.get('scheduled_departure')})"

        origin_name = seg["route"]["origin_name"]
        dest_name = seg["route"]["destination_name"]

        st.markdown(f"""
            <div class="{banner_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 18px; font-weight: 800; color: #0F172A;">
                        Flight {seg.get('flight_number')} • {origin_name} ({seg['route']['origin']}) → {dest_name} ({seg['route']['destination']})
                    </span>
                    <span class="{status_badge_class}">{status_text}</span>
                </div>
                <div style="font-size: 13.5px; color: #334155;">
                    📅 <b>{seg.get('date_display')}</b> &nbsp;|&nbsp; {disruption_desc}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Initial greeting if history is empty
    current_history = st.session_state.chat_history[st.session_state.selected_pnr]
    if len(current_history) == 0:
        # Generate welcoming initial state
        initial_msg = (
            f"Hello {active_customer.get('name')}. I see your flight {active_segment.get('flight_number')} "
            f"from {active_segment['route']['origin_name']} to {active_segment['route']['destination_name']} "
            f"is currently **{active_segment.get('status').lower()}**.\n\n"
            f"I am here to resolve your disruption in accordance with airline policies. How can I assist you?"
        )
        current_history.append({"role": "assistant", "content": initial_msg, "suggested_actions": []})

    # Render Chat History
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(current_history):
            with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "✈️"):
                st.markdown(msg["content"])

    # Suggested Action Chips (clickable)
    last_resp = st.session_state.last_response[st.session_state.selected_pnr]
    suggested = []
    if last_resp and last_resp.suggested_actions:
        suggested = last_resp.suggested_actions
    elif len(current_history) > 0 and current_history[-1].get("suggested_actions"):
        suggested = current_history[-1].get("suggested_actions")
    else:
        # Default scenario chips
        if st.session_state.selected_pnr == "SK4821X":
            suggested = ["Request Full Refund", "Explore Free Rebooking", "Ask for Business Class Upgrade"]
        elif st.session_state.selected_pnr == "TR1190B":
            suggested = ["View Delay Benefits", "Request Hotel Accommodation", "Check New Departure Time"]
        elif st.session_state.selected_pnr == "WL7742":
            suggested = ["View Delay Benefits", "Request Full Night Hotel", "Request Higher-Fare Flight (₹2,000)"]

    if suggested:
        st.markdown("<p style='font-size: 12px; font-weight: 700; color: #64748B; margin: 8px 0 4px 0;'>Suggested Actions:</p>", unsafe_allow_html=True)
        cols = st.columns(len(suggested))
        for idx, chip_text in enumerate(suggested):
            if cols[idx].button(chip_text, key=f"chip_{idx}_{chip_text}", use_container_width=True):
                st.session_state.pending_prompt = chip_text
                st.rerun()

    # Handle incoming messages
    user_input = st.chat_input("Type your message or query here...")
    if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
        user_input = st.session_state.pending_prompt
        st.session_state.pending_prompt = None

    if user_input:
        # 1. Add user message
        current_history.append({"role": "user", "content": user_input})

        # 2. Process via Agent Orchestrator
        response = agent.process_message(
            message=user_input,
            active_customer_id_or_pnr=st.session_state.selected_pnr,
        )
        st.session_state.last_response[st.session_state.selected_pnr] = response

        # 3. Add assistant response
        current_history.append({
            "role": "assistant",
            "content": response.text,
            "suggested_actions": response.suggested_actions,
        })
        st.rerun()


# -----------------------------------------------------------------------------
# Column 2: Secondary Inspector (Status, Live Eligibility, Decision Trace, Escalation)
# -----------------------------------------------------------------------------
with col_inspector:
    last_resp = st.session_state.last_response[st.session_state.selected_pnr]

    # ESCALATION BANNER (Shown prominently when triggered)
    if last_resp and last_resp.escalation_ticket:
        ticket = last_resp.escalation_ticket
        st.markdown(f"""
            <div class="escalation-box">
                <div class="escalation-title">
                    ⚠️ HUMAN ESCALATION REQUIRED
                </div>
                <div style="font-size: 13px; color: #881337; line-height: 1.6;">
                    <b>Ticket ID:</b> <code>{ticket['ticket_id']}</code><br>
                    <b>Trigger Rule:</b> {ticket.get('rule_name')}<br>
                    <b>Reason:</b> {ticket.get('escalation_reason')}<br>
                    <b>Required Action:</b> {ticket.get('required_human_action')}
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # 1. LIVE POLICY ELIGIBILITY MATRIX
    st.markdown("""
        <div style="font-size: 15px; font-weight: 800; color: #0F172A; margin-bottom: 8px;">
            📋 Policy Entitlements & Guardrails
        </div>
    """, unsafe_allow_html=True)

    allowed_list = []
    prohibited_list = []

    if last_resp and last_resp.decision:
        allowed_list = last_resp.decision.allowed_actions
        prohibited_list = last_resp.decision.prohibited_actions

    if not allowed_list and not prohibited_list:
        # Pre-populate default entitlement view based on active flight status
        if active_segment.get("status") == "Cancelled":
            allowed_list = [
                "Full refund to original payment method (7 business days)",
                "Free rebooking on next flight within 24 hours",
                f"Priority rebooking ({active_customer.get('loyalty_tier')} tier perk)",
            ]
            prohibited_list = [
                "Complimentary Business Class upgrade (not supported by policy)",
                "Cash compensation beyond standard refund",
                "Refund to alternate payment method",
            ]
        elif active_segment.get("status") == "Delayed":
            delay_h = active_segment.get("delay_duration_hours", 0)
            if delay_h <= 5:
                allowed_list = ["₹500 meal voucher", "Lounge access (delay > 3h)"]
                prohibited_list = [
                    "Hotel accommodation (requires delay > 5 hours)",
                    "Cash compensation beyond meal voucher",
                ]
            else:
                allowed_list = [
                    "₹500 meal voucher",
                    "Lounge access",
                    "Hotel accommodation (delayed hours only)",
                ]
                prohibited_list = [
                    "Full night's hotel stay (only delayed hours covered)",
                    "Waiving fare difference > ₹1,500 without supervisor approval",
                ]

    with st.container():
        st.markdown("""<div class="air-card">""", unsafe_allow_html=True)
        st.markdown("<b style='color: #065F46; font-size: 13px;'>✓ ELIGIBLE BENEFITS</b>", unsafe_allow_html=True)
        for item in allowed_list:
            st.markdown(f"""<div class="eligibility-check"><span>✔</span> <span>{item}</span></div>""", unsafe_allow_html=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        st.markdown("<b style='color: #991B1B; font-size: 13px;'>✕ PROHIBITED / NOT AVAILABLE</b>", unsafe_allow_html=True)
        for item in prohibited_list:
            st.markdown(f"""<div class="eligibility-cross"><span>✖</span> <span>{item}</span></div>""", unsafe_allow_html=True)
        st.markdown("""</div>""", unsafe_allow_html=True)

    # 2. DECISION TRACE / AUDIT TRAIL (PROGRESSIVE DISCLOSURE)
    st.markdown("""
        <div style="font-size: 15px; font-weight: 800; color: #0F172A; margin-top: 14px; margin-bottom: 8px;">
            🔍 Decision Trace & Audit Trail
        </div>
    """, unsafe_allow_html=True)

    trace_steps = last_resp.trace if last_resp else [
        f"1. Customer verified: {active_customer.get('name')} ({active_customer.get('loyalty_tier')})",
        f"2. Flight verified: {active_segment.get('flight_number')} ({active_segment.get('status')})",
        "3. Policy Engine awaiting customer interaction...",
    ]

    with st.expander("Show step-by-step reasoning", expanded=True):
        st.caption("Deterministic execution trace logged by the policy engine:")
        for step in trace_steps:
            st.markdown(f"""<div class="trace-item">{step}</div>""", unsafe_allow_html=True)

        if last_resp and last_resp.decision:
            st.markdown(f"""
                <div style="margin-top: 10px; padding: 8px 12px; background: #EEF2F6; border-radius: 8px; font-size: 12px;">
                    <b>Policy Reference:</b> <i>{last_resp.decision.policy_reference or last_resp.decision.rule_name}</i><br>
                    <b>Decision Code:</b> <code>{last_resp.decision.rule_id}</code> ({last_resp.decision.decision.value})
                </div>
            """, unsafe_allow_html=True)

    # 3. GROUND TRUTH POLICY INSPECTOR
    with st.expander("📖 Ground Truth Service Rules (Data Pack)", expanded=False):
        st.markdown("""
            - **Cancellation Rebooking Rule**: Free rebooking within 24 hours OR full refund (7 business days, original payment method only).
            - **Delay Compensation Rule**:
              - `< 3h`: ₹500 meal voucher
              - `3h - 5h`: ₹500 meal voucher + lounge access
              - `> 5h`: ₹500 meal voucher + lounge access + hotel covering *only delayed hours*.
            - **Fare Difference Rule**: Frontline agent waiver ceiling is ₹1,500. Differences > ₹1,500 require supervisor approval.
            - **Loyalty Tier Rule**: Gold & Platinum get priority rebooking, NO additional compensation.
            - **Strict Escalations**: Legal threats, refunds to alternate payment methods, fare diff > ₹1,500.
        """)
