# ✈️ AirResolve: Customer-Facing Disruption Resolution Agent

> **Individual Assignment 3 Submission**: Customer-Facing Resolution Agent (Airline Disruption)  
> **Source of Truth**: Assignment 3 Data Pack (Operational Date: Wednesday, 23 September 2026)  
> **Evaluation Mode**: Technical Interview / Live Walkthrough  

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Framework: Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Testing: Pytest](https://img.shields.io/badge/Testing-Pytest%20(28%20Passed)-brightgreen.svg)](https://pytest.org/)
[![Architecture: Policy--First](https://img.shields.io/badge/Architecture-Deterministic%20Policy%20Engine-008DDA.svg)]()

---

## 1. Project Title
**AirResolve — Intelligent, Policy-Grounded Airline Disruption Resolution Agent**

---

## 2. Problem Statement
During large-scale airline disruptions (weather, air traffic control, or operational cancellations), thousands of passengers encounter delayed or cancelled flights simultaneously. Passengers flood airport service desks and customer support call centers with emotionally charged demands for cash refunds, meal vouchers, overnight hotel stays, and cabin class upgrades.

Traditional generic AI chatbots frequently fail in this setting because:
1. **Hallucination of Policy**: Probabilistic LLMs invent compensation rules or promise complimentary Business Class upgrades to appease angry passengers.
2. **Financial Leakage**: Frontline bots waive fees or approve hotel stays beyond authorized authority limits.
3. **Lack of Auditability**: Conversational AI rarely produces structured, deterministic compliance logs explaining *why* an action was taken.

---

## 3. Project Objective
To build a reliable, auditable, customer-facing resolution agent that:
- Accurately identifies passengers and verifies booking and disruption statuses.
- Comprehends natural language requests and emotional context without sacrificing compliance.
- Ground all decisions in a **deterministic Python policy engine** as the single source of truth.
- Transparently displays live eligible benefits vs prohibited actions.
- Automatically routes out-of-scope requests, legal threats, and high fare differences ($> ₹1,500$) to human supervisors via formal escalation tickets.

---

## 4. Key Features
- **Passenger Context Switcher**: Quick toggle between verified customer personas (Priya Nair, Arvind Kulkarni, Meher Kaur) and PNRs.
- **Real-Time Disruption Banner**: Visual flight status badge with route, departure time, and cancellation reason or delay duration.
- **Empathetic & Compliant Chat**: Natural conversation stream that validates customer frustration while firmly adhering to policy limits.
- **Dynamic Suggested Action Chips**: Contextual 1-click action buttons based on active flight status.
- **Live Policy Entitlement Matrix**: Instant side-by-side view of **Eligible Benefits** (✔) vs **Prohibited Actions** (✖).
- **Step-by-Step Decision Trace**: Expandable compliance log detailing every step of reasoning for technical review.
- **Human Escalation Gateway**: High-visibility escalation banner with unique ticket IDs, supervisor action requirements, and policy citations.
- **Zero Policy Inventions**: Strict enforcement of the Assignment 3 Data Pack rules.

---

## 5. System Architecture

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
                                         │
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
                     │  (Pure Python Single Source of Truth) │
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

The high-resolution diagram is available at `assets/architecture.png`.

---

## 6. Technology Stack
| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend UI** | Streamlit + Custom Vanilla CSS | Responsive, branded airline disruption portal |
| **Backend / Orchestration** | Python 3.11 | Conversational session manager, intent routing |
| **Policy Engine** | Pure Deterministic Python | Single source of truth for business rules & limits |
| **Data Storage** | Local Structured JSON | Ground truth customers, bookings, and policies |
| **Testing** | Pytest (28 automated tests) | 100% scenario, boundary, and escalation coverage |
| **Diagrams & Deck** | Matplotlib & python-pptx | High-resolution architecture PNG and 10-slide deck |

---

## 7. How the Agent Works
1. **Identification**: Passenger selected via PNR or name lookup. Active loyalty tier and 12-month travel history retrieved.
2. **Disruption Verification**: Flight segment loaded; cancellation reason or delay duration verified.
3. **Intent Extraction**: User message analyzed for primary intent (refund, rebook, hotel, upgrade, higher-fare rebooking) and monetary entities (e.g. ₹2,000).
4. **Immediate Escalation Gate**: Evaluates if the message contains legal threats, formal complaints, non-airline disruptions, or alternate payment requests.
5. **Policy Engine Execution**: Evaluates exact rule formulas.
6. **Decision Output**: Resolves with vouchers/refund, clarifies options, or creates a supervisor escalation ticket.
7. **Trace Logging**: Formats an auditable step-by-step trace and customer-friendly empathetic response.

---

## 8. Policy Engine Design (`policy/policy_engine.py`)
The deterministic policy engine implements the exact business rules from the Data Pack:
- **Cancellation Rebooking Rule**: Free rebooking within 24 hours OR full refund to original payment method.
- **Delay Compensation Rule**:
  - Delay $< 3$ hours: ₹500 meal voucher.
  - Delay $3 - 5$ hours: ₹500 meal voucher + lounge access.
  - Delay $> 5$ hours: ₹500 meal voucher + lounge access + hotel accommodation covering *only delayed hours*.
- **Refund Processing Rule**: Processed in full within 7 business days to original payment method only.
- **Fare Difference Rule**: Frontline agent waiver ceiling is ₹1,500. Differences above ₹1,500 strictly require supervisor approval.
- **Loyalty Tier Rule**: Gold and Platinum members receive priority rebooking; no additional compensation beyond standard policy.

---

## 9. Escalation Design
The policy engine halts automated resolution and triggers human escalation for the 5 mandatory prohibited categories:
1. **Compensation beyond policy**: Asking for cash compensation or services outside policy.
2. **Fare difference $> ₹1,500$**: Waiver requests above agent authority.
3. **Non-airline disruptions**: Passenger missed flight, personal emergency, etc.
4. **Threats of legal action or formal complaints**: Immediate transfer to specialist support.
5. **Refund to different payment method**: Anti-fraud compliance requirement.

Each escalation produces a structured ticket:
- `ticket_id`: Unique identifier (e.g. `ESC-WL7742-A1B2C3`).
- `rule_name`: The triggering policy rule.
- `escalation_reason`: Specific factual trigger.
- `required_human_action`: Exact action required by the supervisor.

---

## 10. The Three Data Pack Scenarios

### Scenario 1: Priya Nair (Gold Tier, SK4821X)
- **Flight**: SK-204 (Delhi → Goa), Cancelled for operational reasons. Return (25 Sep) unaffected.
- **Request**: Full cash refund + free upgrade to Business Class on return flight. Customer is furious.
- **Agent Behavior**:
  - Initiates full refund to original payment method (processed in 7 business days).
  - Explicitly refuses free Business Class upgrade: explains Gold tier grants priority rebooking, not complimentary cabin upgrades.
  - If she threatens legal action: immediately escalates to specialist support.

### Scenario 2: Arvind Kulkarni (Silver Tier, TR1190B)
- **Flight**: SK-118 (Mumbai → Bengaluru), Delayed 4 hours (07:10 → 11:10).
- **Request**: Hotel accommodation due to long delay and missed connecting meeting.
- **Agent Behavior**:
  - Issues ₹500 meal voucher + lounge access (qualifies for delays $> 3$ hours).
  - Politely refuses hotel accommodation: explains policy requires delay $> 5$ hours. Does not make unauthorized promises.

### Scenario 3: Meher Kaur (Platinum Tier, WL7742)
- **Flight**: SK-305 (Delhi → Hyderabad), Delayed 6 hours (14:00 → 20:00).
- **Requests**:
  1. Full night's hotel stay rather than just coverage for delayed hours.
  2. Move onto higher-fare flight with ₹2,000 fare difference.
- **Agent Behavior**:
  - Grants ₹500 meal voucher, lounge access, and hotel covering *only delayed hours*. Refuses full night stay.
  - Evaluates ₹2,000 fare difference against ₹1,500 agent waiver ceiling.
  - Generates Escalation Ticket for supervisor approval; does not waive ₹2,000.

---

## 11. Testing & Quality Assurance
The project includes a robust automated test suite built with `pytest`:
- `tests/test_policy_engine.py`: Unit tests for all deterministic policy rules and thresholds.
- `tests/test_priya.py`: Scenario 1 tests (refund, upgrade denial, legal escalation).
- `tests/test_arvind.py`: Scenario 2 tests (delay vouchers, hotel denial).
- `tests/test_meher.py`: Scenario 3 tests (6h benefits, delayed-hours hotel, ₹2,000 fare difference escalation).
- `tests/test_escalation.py`: Tests for all 5 prohibited action triggers.
- `tests/test_agent_scenarios.py`: Multi-turn flows, entity extraction, and conversational variations.

### Running the Tests
```bash
pytest -v
```
**Result**: **28 passed in ~0.07s (100% pass rate)**.

---

## 12. Installation
Ensure Python 3.10+ is installed.

```bash
# Clone the repository
git clone https://github.com/USERNAME/airline-resolution-agent.git
cd airline-resolution-agent

# Create and activate virtual environment (optional but recommended)
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 13. Running Locally
Launch the Streamlit web application:

```bash
streamlit run app.py
```

The application will open automatically in your browser at `http://localhost:8501`.

---

## 14. User Interface & Screenshots
The visual interface includes:
- **Airline Header**: Navy & Electric Blue gradient with operational date tag (`23 Sep 2026`).
- **Disruption Banner**: Red (Cancelled) or Amber/Blue (Delayed) visual card with route details.
- **Interactive Chat**: Conversational bubbles with clickable suggestion chips.
- **Live Eligibility Card**: Clear visual matrix of eligible vs prohibited items.
- **Decision Trace Expander**: Step-by-step execution trail for full transparency.

*(See `assets/architecture.png` for complete system flow diagram).*

---

## 15. Deployment Instructions

### Option A: Deploy to Vercel (Recommended)
AirResolve includes native Vercel support via `vercel.json`, `api/index.py` (Python serverless function), and `public/` (web dashboard).

1. Push the code to GitHub:
   ```bash
   git add .
   git commit -m "feat: vercel deployment ready"
   git push -u origin main
   ```
2. Log into [vercel.com](https://vercel.com) and click **"Add New..." $\rightarrow$ "Project"**.
3. Select your GitHub repository and click **"Deploy"**.
4. Your application will be live at `https://<YOUR-PROJECT>.vercel.app`.
*(See detailed guide in [docs/VERCEL_DEPLOYMENT.md](docs/VERCEL_DEPLOYMENT.md))*

### Option B: Deploy to Streamlit Community Cloud
1. Push your repository to GitHub.
2. Visit [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
3. Click **"New app"**.
4. Select your repository, branch (`main`), and set Main file path to `app.py`.
5. Click **"Deploy"**. The app will be live within 2 minutes.

---

## 16. Demo Video
- **Public Google Drive Link**:  
  `[PASTE YOUR PUBLIC GOOGLE DRIVE LINK HERE]`  
  *(Ensure access is set to "Anyone with the link can view")*
- A detailed, timestamped script for recording this video is in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

---

## 17. GitHub Repository
- **Repository URL**: `https://github.com/USERNAME/airline-resolution-agent`
- Contains clean commit history, `.gitignore`, production documentation, and tests.

---

## 18. Technical Interview Defense Guide
A comprehensive technical defense handbook is prepared in [docs/TECHNICAL_DEFENSE.md](docs/TECHNICAL_DEFENSE.md).  
It answers 15 core architectural questions:
1. Architectural choices and trade-offs.
2. Deterministic policy engine vs probabilistic LLMs.
3. Hallucination prevention via structural inversion.
4. Scale, caching, and enterprise GDS API connectivity.
5. Full 60-second elevator pitch for the evaluator.

---

## 19. Known Limitations
- Operates on local structured JSON rather than live GDS/NDC APIs.
- Voucher distribution is simulated via visual UI cards rather than sending live SMS/Apple Wallet passes.
- Escalations create auditable supervisor tickets but do not connect to a dual-screen supervisor portal in this single-screen demo.

---

## 20. Future Improvements (Version 2)
1. **Supervisor Review Dashboard**: Dual-sided portal for supervisors to approve or deny escalated fare waivers in real time.
2. **Apple & Google Wallet Integration**: Generate live barcode passes for meal vouchers and lounge entry.
3. **Multilingual Support**: Indian regional language support (Hindi, Marathi, Tamil, Telugu).
4. **Direct PSS / NDC Connectors**: Real-time seat inventory booking via Amadeus/Sabre APIs.
