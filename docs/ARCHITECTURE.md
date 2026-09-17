# AirResolve: System Architecture Specification

**Project**: Customer-Facing Resolution Agent (Airline Disruption)  
**Source of Truth**: Assignment 3 Data Pack (Operational Date: Wednesday, 23 September 2026)

---

## 1. Architectural Philosophy & Guiding Principle

> [!IMPORTANT]
> **Core Principle: Deterministic Policy Primacy**  
> Conversational models (LLMs or pattern matchers) must **NEVER** serve as the final authority on airline business rules, compensation limits, or fee waivers.
>
> In AirResolve, conversational layers are strictly confined to:
> 1. Natural language understanding and intent extraction.
> 2. Entity recognition (e.g. fare difference amounts, stay duration).
> 3. Empathetic, customer-centric response formatting.
>
> All business decisions, eligibility checks, waiver thresholds, and escalation triggers are executed by a **deterministic Python policy engine**.

---

## 2. End-to-End System Architecture

```
                                  PASSENGER (User)
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │       AirResolve Streamlit Web UI     │
                     │  - Interactive Chat + Customer Switch │
                     │  - Live Disruption Banner (Status)    │
                     │  - Eligibility & Guardrail Inspector  │
                     │  - Step-by-Step Decision Audit Trace  │
                     │  - Action Chips & Escalation Modal    │
                     └───────────────────┬───────────────────┘
                                         │ User Query / Prompt
                                         ▼
                     ┌───────────────────────────────────────┐
                     │      Conversational Orchestrator      │
                     │  - Session & Dialogue State Tracking  │
                     │  - Contextual History Management      │
                     │  - Empathetic Response Generation     │
                     └───────────────────┬───────────────────┘
                                         │
                     ┌───────────────────┴───────────────────┐
                     ▼                                       ▼
        ┌─────────────────────────┐             ┌─────────────────────────┐
        │     Intent Detector     │             │     Data Repository     │
        │ - User Intent Classifier│             │ - Customer Profiles     │
        │ - Entity Extraction     │             │ - Booking Transactions  │
        │   (₹ amounts, stay, etc)│             │ - Ground Truth Policies │
        └────────────┬────────────┘             └────────────┬────────────┘
                     │                                       │
                     └───────────────────┬───────────────────┘
                                         │ Identified Intent & Entities
                                         ▼
                     ┌───────────────────────────────────────┐
                     │      Deterministic Policy Engine      │
                     │  - evaluate_cancellation_options()    │
                     │  - evaluate_delay_compensation()      │
                     │  - evaluate_hotel_request()           │
                     │  - evaluate_fare_difference_waiver()  │
                     │  - evaluate_upgrade_request()         │
                     │  - check_escalation_required()        │
                     └───────────────────┬───────────────────┘
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │       Decision & Guardrail Gateway    │
                     └───────────────────┬───────────────────┘
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
          [ RESOLVE ]              [ CLARIFY ]             [ ESCALATE ]
       Apply policy action,     Prompt customer for     Route to supervisor with
       issue vouchers/refund,   missing choice or       ticket, policy citation,
       or explain ineligibility clarification           and audit trail
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │       Structured Decision Trace       │
                     │       + Natural Language Output       │
                     └───────────────────────────────────────┘
```

---

## 3. Component Breakdown

### 3.1. Presentation Layer (`app.py` & `assets/style.css`)
- **Technology**: Streamlit + Vanilla CSS.
- **Features**:
  - **Passenger Context Switcher**: Seamlessly toggles between Priya Nair (Gold), Arvind Kulkarni (Silver), and Meher Kaur (Platinum).
  - **Flight Disruption Banner**: Live visual status for Cancelled (operational reasons) or Delayed (4h / 6h).
  - **Conversational Interface**: Natural multi-turn chat stream with quick suggested action chips.
  - **Live Eligibility Matrix**: Explicit real-time breakdown of eligible benefits vs prohibited actions.
  - **Decision Trace Accordion**: Exposes step-by-step reasoning for complete transparency and technical auditability.
  - **Escalation Alert**: High-visibility banner when human supervisor intervention is required.

### 3.2. Conversational Orchestrator (`agent/orchestrator.py`)
- Coordinates the pipeline:
  1. Identifies the active passenger and retrieves verified PNR booking data.
  2. Runs intent and entity detection on the passenger's message.
  3. Checks for mandatory immediate escalation triggers (legal threats, formal complaints, alternate payment methods).
  4. Invokes the appropriate policy engine evaluator.
  5. Assembles a structured audit trace and formats an empathetic, policy-grounded natural response.

### 3.3. Intent & Entity Detector (`agent/intent_detector.py`)
- Classifies user inputs across 14 categories (Refund, Rebooking, Hotel, Upgrade, Higher-Fare Flight, Legal Action, etc.).
- Normalizes diverse phrasing (e.g. *"give me my money back"* $\rightarrow$ `REQUEST_REFUND`; *"place to sleep"* $\rightarrow$ `REQUEST_HOTEL`).
- Extracts numeric parameters (e.g. `₹2,000` fare difference, full night indicators).

### 3.4. Deterministic Policy Engine (`policy/policy_engine.py`)
- The single source of truth for business logic.
- Implements exact parameters from the Data Pack:
  - **Cancellation Rule**: Free rebooking within 24h OR full refund in 7 business days to original payment method.
  - **Delay Compensation Rule**:
    - $< 3$ hours: ₹500 meal voucher.
    - $3 - 5$ hours: ₹500 meal voucher + lounge access.
    - $> 5$ hours: Meal voucher + lounge access + hotel accommodation covering *only delayed hours*.
  - **Fare Difference Waiver Ceiling**: Frontline agent threshold is ₹1,500. Differences exceeding ₹1,500 strictly require supervisor approval.
  - **Loyalty Tier Rule**: Gold and Platinum members receive priority rebooking; no additional compensation beyond standard policy.
  - **Prohibited Actions**: Escalates legal action, formal complaints, non-airline disruptions, and refund method overrides.

---

## 4. Policy Guardrails & Escalation Gates

| Condition | Agent Action | Decision Type | Rationale / Citation |
| :--- | :--- | :--- | :--- |
| **Legal Threat / Formal Complaint** | Escalate immediately | `ESCALATE` | Mandated by Prohibited Actions: specialist team transfer |
| **Fare Difference $> ₹1,500$** | Escalate to supervisor | `ESCALATE` | Frontline waiver ceiling is ₹1,500 |
| **Alternate Payment Method** | Escalate to supervisor | `ESCALATE` | Refunds strictly to original payment method only |
| **Non-Airline Disruption** | Escalate to human | `ESCALATE` | Automated exceptions prohibited for personal delays |
| **Business Class Upgrade** | Refuse politely | `INELIGIBLE` | Disruption & loyalty rules do not permit free cabin upgrades |
| **Hotel for $\le 5$h Delay** | Refuse hotel, give vouchers | `INELIGIBLE` | Policy strictly requires delay $> 5$ hours |
| **Full Night Hotel for $> 5$h Delay** | Approve delayed hours only | `RESOLVED` (Partial) | Hotel coverage covers delayed hours only, not full night |

---

## 5. Decision Auditability & Data Contracts

Every interaction produces a structured `PolicyDecision` object:
```json
{
  "decision": "ESCALATE",
  "rule_id": "RULE_FARE_DIFF_EXCEEDS_AUTHORITY",
  "rule_name": "Prohibited Action: Waiving Fare Difference Above ₹1,500",
  "rationale": "The requested flight has a fare difference of ₹2,000.00. Under policy, frontline agents cannot waive fare differences above ₹1,500.00 without supervisor approval.",
  "allowed_actions": ["Customer pays ₹2,000 fare difference", "Escalate to supervisor for waiver exception"],
  "prohibited_actions": ["Automated waiver of fare difference above ₹1,500.00"],
  "escalation_required": true,
  "escalation_reason": "Requested fare-difference waiver of ₹2,000.00 exceeds the agent's ₹1,500.00 authority.",
  "required_human_action": "Supervisor approval required to waive fare difference exceeding ₹1,500.",
  "policy_reference": "Fare Difference Rule & Prohibited Actions",
  "trace_steps": [
    "Step 1: Customer identified - Meher Kaur (PNR: WL7742, Loyalty Tier: Platinum)",
    "Step 2: Booking verified - Flight SK-305 (Delhi -> Hyderabad), Status: Delayed",
    "Step 3: Intent detected - 'REQUEST_HIGHER_FARE_REBOOKING', Fare diff: ₹2,000.00",
    "Step 4: Fare difference ₹2,000.00 EXCEEDS agent authority threshold of ₹1,500.00 -> ESCALATE TO SUPERVISOR."
  ]
}
```
