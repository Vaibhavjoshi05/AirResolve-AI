# AirResolve: 3-5 Minute Video Demonstration Script

**Project**: Customer-Facing Resolution Agent (Airline Disruption)  
**Submission**: Individual Assignment 3  
**Recorded By**: [PASTE YOUR NAME HERE]  
**Google Drive Demo Video Link**: `[PASTE YOUR PUBLIC GOOGLE DRIVE LINK HERE]`

---

## Preparation Checklist Before Recording
1. Start the application locally:
   ```bash
   streamlit run app.py
   ```
2. Maximize the browser window (1920x1080 resolution recommended).
3. Have this script open on a second monitor or printed.
4. Keep the presentation slides ready for the opening/closing if desired.

---

## Timestamped Walkthrough

### ⏱️ 00:00 – 00:20 | Product Introduction & Context
* **Visual on Screen**: Browser showing the AirResolve header and main interface.
* **What to Click**: Point mouse to the AirResolve logo, then highlight the operational date tag (`23 Sep 2026`).
* **What to Say**:
  > *"Hello and welcome. Today I am demonstrating **AirResolve**, an intelligent, policy-grounded disruption resolution agent built for Assignment 3. The operational scenario is Wednesday, 23 September 2026. Unlike traditional generic chatbots that hallucinate policies and make unauthorized promises, AirResolve uses a deterministic Python policy engine as the single source of truth to resolve flight cancellations, delays, and passenger entitlements with absolute compliance and auditability."*

---

### ⏱️ 00:20 – 01:00 | Architecture & Key Principle
* **Visual on Screen**: Slide 5 from PowerPoint or open `assets/architecture.png` in image viewer / browser.
* **What to Point Out**: Point to the separation between the conversational layer and the deterministic policy engine.
* **What to Say**:
  > *"Here is the core architecture. When a passenger messages AirResolve, the Streamlit interface passes the input to our Conversational Orchestrator. The orchestrator extracts the intent and domain entities, and retrieves the verified customer profile and booking. However—and this is the foundational design principle—the conversational layer is NOT the decision maker. The query is evaluated strictly by a deterministic Python policy engine that enforces hard business rules, waiver thresholds, and escalation guardrails. The engine produces a structured decision: Resolve, Clarify, or Escalate, with a complete audit trace."*

---

### ⏱️ 01:00 – 02:00 | Scenario 1 — Priya Nair (Gold Tier, Cancelled Flight SK-204)
* **Visual on Screen**: Switch back to AirResolve Web UI.
* **What to Click**:
  1. In the sidebar, ensure **Priya Nair** is selected (`SK4821X`).
  2. Point out the Red Disruption Banner: Flight SK-204 (Delhi → Goa) is **Cancelled** due to operational reasons. Point out Gold loyalty tier.
  3. Click the Quick Prompt button: `🔴 Scenario 1: Refund + Business Upgrade` (or type: *"I am furious! My flight is cancelled. I want a full cash refund plus a free upgrade to business class on my return flight for the trouble."*).
* **What Appears**:
  - The chat bubble displays an empathetic response.
  - Full refund is initiated to the original payment method within 7 business days per policy.
  - The free Business Class upgrade on the unaffected return flight is **explicitly denied** with the exact policy explanation that Gold tier grants priority rebooking, not complimentary upgrades.
  - Look at the right panel: **Eligible Benefits** shows green check for refund, and **Prohibited Items** shows red cross for free Business Class upgrade.
* **What to Say**:
  > *"In Scenario 1, Priya Nair is furious because her flight to Goa was cancelled. She demands a full refund and a free Business Class upgrade on her return flight. Notice how AirResolve responds with empathy, confirms the cancellation, and approves the full refund processed within 7 business days to her original payment method. But crucially, it refuses the free Business Class upgrade because the policy does not permit complimentary cabin upgrades for flight disruptions or Gold status. The agent does not cave to customer pressure."*
* **Optional Escalation Test**:
  - Click `⚖️ Test Legal Action Escalation`.
  - Point out that the agent immediately detects the legal threat, halts automated processing, and creates an escalation ticket for the specialist support team.

---

### ⏱️ 02:00 – 02:45 | Scenario 2 — Arvind Kulkarni (Silver Tier, 4h Delay SK-118)
* **Visual on Screen**: Change sidebar dropdown to **Arvind Kulkarni** (`TR1190B`).
* **What to Click**:
  1. Point out the Amber Disruption Banner: Flight SK-118 (Mumbai → Bengaluru) is **Delayed 4 hours** (new departure 11:10).
  2. Click the Quick Prompt button: `🟡 Scenario 2: Request Hotel (4h delay)` (or type: *"I'm frustrated about missing a connecting meeting and I need hotel accommodation since it's been such a long delay."*).
* **What Appears**:
  - Agent acknowledges the frustration of missing a meeting.
  - Issues ₹500 meal voucher and lounge access per the Delay Compensation Rule ($> 3$ hours).
  - Explicitly states that hotel accommodation requires a delay of **more than 5 hours**, and therefore cannot be provided for this 4-hour delay.
  - Right panel updates: Hotel Accommodation is marked as **Prohibited / Not Eligible**.
* **What to Say**:
  > *"Next, we select Arvind Kulkarni. His flight is delayed by 4 hours. He is frustrated about missing a meeting and demands hotel accommodation. AirResolve evaluates the delay: at 4 hours, it qualifies for a ₹500 meal voucher and lounge access, which are issued immediately. But under airline policy, hotel accommodation is only available when delays exceed 5 hours. AirResolve politely explains this rule and refuses hotel booking without hallucinating an exception."*

---

### ⏱️ 02:45 – 03:30 | Scenario 3 — Meher Kaur (Platinum Tier, 6h Delay SK-305 & ₹2,000 Fare Diff)
* **Visual on Screen**: Change sidebar dropdown to **Meher Kaur** (`WL7742`).
* **What to Click**:
  1. Point out the Blue Disruption Banner: Flight SK-305 (Delhi → Hyderabad) is **Delayed 6 hours** (new departure 20:00). Platinum tier.
  2. Click `🔵 Scenario 3A: Request Full Night Hotel`.
     - *Observation*: Agent grants accommodation covering **only the delayed hours**, explicitly clarifying that policy does not provide a full night's stay.
  3. Click `🚨 Scenario 3B: Higher-Fare Flight (₹2,000)` (or type: *"Move me onto a different, higher-fare flight instead of waiting. The fare difference is ₹2,000."*).
* **What Appears**:
  - A prominent red **HUMAN ESCALATION REQUIRED** card appears on the right.
  - Generates Escalation Ticket (e.g. `ESC-WL7742-XXXX`).
  - Reason: Requested fare-difference waiver of ₹2,000 exceeds frontline agent authority of ₹1,500.
  - Required action: Supervisor approval required.
* **What to Say**:
  > *"Finally, Scenario 3: Meher Kaur, a Platinum flyer delayed 6 hours. When she asks for a full night's hotel, the agent explains that her delay entitles her to accommodation covering only the delayed hours, not a full night. Then, when she asks to switch to a higher-fare flight with a ₹2,000 fare difference, the policy engine activates a mandatory guardrail: frontline agents can only waive up to ₹1,500. Because ₹2,000 exceeds that ceiling, the system refuses an automated waiver and creates an audited escalation ticket for supervisor approval."*

---

### ⏱️ 03:30 – 04:00 | Decision Trace & Auditability
* **Visual on Screen**: Click on the **Decision Trace & Audit Trail** expander on the right inspector panel.
* **What to Point Out**: Scroll through the numbered trace steps.
* **What to Say**:
  > *"Every single decision is fully auditable. Here in the Decision Trace, we see the step-by-step pipeline: customer identified, booking verified, intent classified, policy rules evaluated with exact rule IDs, and guardrails enforced. This guarantees that airline compliance officers can audit every customer interaction with complete transparency."*

---

### ⏱️ 04:00 – 04:30 | Technical Testing & Closing
* **Visual on Screen**: Show terminal running `pytest -v` with 28 passing tests, or show Slide 10 from the PPT deck.
* **What to Say**:
  > *"AirResolve is backed by a comprehensive automated test suite with 28 unit and scenario tests covering 100% of the Data Pack rules and edge cases. It is fully containerized, easy to run with a single command, and available on GitHub. Thank you for your time, and I look forward to your questions in the technical interview."*

---

## 📹 Post-Recording Steps for the User
1. Record your screen and microphone following the above script.
2. Upload the MP4/WebM video to your Google Drive.
3. Set link sharing to: **"Anyone with the link can view"** (Open/Public access).
4. Paste the URL into `README.md` under the **Demo Video** section and update Slide 10 in the PowerPoint presentation.
