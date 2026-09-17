# AirResolve: Technical Interview Defense Handbook

**Project**: Customer-Facing Resolution Agent (Airline Disruption)  
**Role**: Technical Interview Preparation & System Defense Guide

---

## ⚡ The 60-Second Elevator Pitch
> *"AirResolve is an enterprise-grade airline disruption resolution agent designed specifically to solve the trust and compliance issues inherent in generative AI. When flights are cancelled or delayed, passengers flood support channels demanding refunds, hotels, and compensation. Traditional LLM-based bots frequently hallucinate policies or make unauthorized promises that cost airlines millions. 
> 
> AirResolve solves this through a **policy-first architecture**: we decouple natural language understanding from business rule execution. While the conversational layer handles intent extraction and empathetic dialogue, every decision—such as the ₹1,500 fare-difference waiver ceiling or the 5-hour hotel threshold—is enforced by a **deterministic Python policy engine**. If an action is permitted, it executes with a transparent audit trail; if it exceeds policy or involves legal threats, it triggers an immediate human escalation. The entire system is backed by 28 automated tests covering 100% of our ground truth rules."*

---

## 🎯 Top 15 Technical Interview Questions & Strong Answers

### 1. Why did you choose this architecture?
**Strong Answer**:  
*"In high-stakes enterprise domains like airline customer operations, regulatory compliance and financial liability make pure LLM decision-making unacceptable. An LLM is a probabilistic text-generation model, not a rule engine. 
We selected a tiered architecture that cleanly decouples the **Conversational Layer** (NLU, entity extraction, tone) from the **Deterministic Policy Engine** (business rules, eligibility thresholds, supervisor gates). This guarantees that customer interactions feel empathetic and natural, while every compensation decision is provably compliant with published tariffs and operating policies."*

---

### 2. Why use a deterministic policy engine?
**Strong Answer**:  
*"A deterministic policy engine produces identical, mathematically provable outputs for identical inputs. For example, if a delay is 4 hours, hotel accommodation is strictly ineligible; if a fare difference is ₹2,000, it strictly exceeds the ₹1,500 waiver ceiling. 
Using pure Python logic provides:
1. **Zero Hallucination**: Business rules cannot be bent by adversarial prompt injection or emotional customer phrasing.
2. **Auditability**: Every decision returns a structured rule ID (e.g. `RULE_DELAY_3H_TO_5H`) and execution trace for compliance reviews.
3. **Maintainability**: Rule changes (e.g. changing meal vouchers from ₹500 to ₹750) are made in a single configuration file without retraining or re-prompting models."*

---

### 3. Why shouldn't the LLM make the final policy decision?
**Strong Answer**:  
*"LLMs suffer from three critical flaws in policy enforcement:
1. **Probabilistic Non-Determinism**: A prompt given to an LLM might return 'refund approved' 95% of the time, but mistakenly promise a complimentary Business Class upgrade 5% of the time.
2. **Susceptibility to Social Engineering**: When a customer says 'I am furious and I will sue you if you don't give me a hotel', standard LLMs tend to be agreeable and capitulate to reduce perceived user friction.
3. **No Financial Guardrails**: An LLM does not inherently understand fiduciary boundaries like a ₹1,500 waiver cap unless constrained by hard code. Therefore, code—not the LLM—must be the final gatekeeper."*

---

### 4. How does intent detection work in your system?
**Strong Answer**:  
*"We use a layered intent classification strategy:
- First, we run regex and semantic pattern matching across 14 domain-specific intent classes (e.g., `REQUEST_REFUND`, `REQUEST_HOTEL`, `LEGAL_OR_FORMAL_COMPLAINT`).
- Second, we extract critical domain entities, such as monetary fare differences (`₹2,000`), stay scopes (`full night` vs `delayed hours`), and cabin classes.
- Third, we enforce priority weighting: safety and compliance intents (such as legal threats or formal complaints) take absolute precedence over standard informational inquiries.
In an enterprise deployment, this is easily backed by an embedding classifier or fine-tuned intent model, but the deterministic post-processor always validates the output."*

---

### 5. How does customer and booking identification work?
**Strong Answer**:  
*"Customer and booking state is bound to verified session credentials. When a passenger enters their PNR (e.g. `SK4821X`) or name, the system queries the customer and booking repository. 
The agent retrieves:
- Passenger profile, contact details, loyalty tier (`Gold`, `Silver`, `Platinum`), and past 12-month travel history.
- Disrupted flight segments, delay durations, cancellation reasons, and whether the disruption was airline-caused.
This prevents the user from having to re-enter basic context and allows the policy engine to immediately evaluate tier-specific perks like priority rebooking."*

---

### 6. How does human escalation work?
**Strong Answer**:  
*"Escalation is treated as a first-class architectural state, not an unhandled exception. 
When a prohibited action or policy boundary is encountered—such as:
- Threats of legal action or formal complaints
- Fare differences exceeding the ₹1,500 agent waiver ceiling
- Non-airline-caused disruptions (e.g. customer missed flight)
- Requests for refunds to a non-original payment method
The engine halts automated resolution, generates a cryptographically unique Escalation Ticket (e.g., `ESC-WL7742-A83F12`), logs the exact triggering policy rule and reason, and presents an escalation alert with the required human action (e.g. 'Supervisor approval required')."*

---

### 7. How do you prevent hallucination?
**Strong Answer**:  
*"We prevent hallucination through **Structural Inversion**:
1. The conversational agent does not generate compensation terms from free text; it selects and formats pre-verified action items generated by the policy engine.
2. The response generator is constrained to only speak to the fields present in the `PolicyDecision` object.
3. The UI independently renders the **Live Policy Entitlements Matrix** directly from the policy engine output, allowing the passenger and reviewers to see verified allowed vs prohibited actions side-by-side with the chat."*

---

### 8. How do you test the agent?
**Strong Answer**:  
*"We test at both the unit and end-to-end integration layers using `pytest`:
- **Policy Engine Tests (`test_policy_engine.py`)**: Boundary testing of delay brackets (<3h, 3-5h, >5h), hotel thresholds, and the ₹1,500 waiver cap.
- **Scenario Tests (`test_priya.py`, `test_arvind.py`, `test_meher.py`)**: Exact replication of the three Data Pack customer personas.
- **Escalation Tests (`test_escalation.py`)**: Verifies all 5 prohibited action categories.
- **Robustness Tests (`test_agent_scenarios.py`)**: Tests linguistic variations like 'give me my money back' or 'place to sleep'.
Currently, our test suite contains **28 automated tests with a 100% pass rate** executing in under 0.1 seconds."*

---

### 9. What happens if the policy doesn't cover a situation?
**Strong Answer**:  
*"By design, our system follows a **Fail-Safe Closed Default**:
If a user requests something outside our codified rules (e.g. rental car reimbursement, cash hotel compensation beyond vouchers), the system does not invent a compromise. It either:
1. Explains that the supplied airline disruption policy does not cover that benefit, or
2. Routes the inquiry to human customer support.
This aligns with Rule 1 of our system: *Never invent business policy*."*

---

### 10. How would you scale this system to handle thousands of concurrent users?
**Strong Answer**:  
*"Because the core policy engine is completely stateless and deterministic, it scales horizontally with zero inter-process locking:
1. **Containerization**: Deploy the application in Docker containers behind an Application Load Balancer (ALB) on AWS ECS, EKS, or Google Cloud Run.
2. **Session Persistence**: Move dialogue state from in-memory session states to a distributed cache like Redis.
3. **Database Integration**: Replace local JSON with a PostgreSQL or Amazon Aurora database with read replicas.
4. **Asynchronous Processing**: Offload notification delivery (emailing meal vouchers or lounge passes) to a message queue like RabbitMQ or AWS SQS."*

---

### 11. How would you connect this to real airline APIs?
**Strong Answer**:  
*"We would implement an **Adapter / Gateway Pattern**:
- Connect to standard airline Global Distribution Systems (GDS) or New Distribution Capability (NDC) APIs like Amadeus, Sabre, or Navitaire.
- The `get_customer()` and `get_booking()` methods would call GDS PNR retrieval endpoints.
- The `action_items` in `PolicyDecision` (such as `INITIATE_FULL_REFUND` or `ISSUE_VOUCHER`) would publish events to the airline's passenger service system (PSS) via authenticated REST/gRPC endpoints."*

---

### 12. How would you add authentication and security?
**Strong Answer**:  
*"For passenger authentication:
- Integrate **OAuth2 / OIDC** with the airline's frequent flyer identity provider.
- Require two-factor authentication (OTP sent to verified phone/email) before exposing PNR data or approving refunds.
- Implement strict Role-Based Access Control (RBAC) so that supervisor accounts have waiver capabilities up to higher limits while frontline agents remain capped at ₹1,500."*

---

### 13. How would you monitor the agent in production?
**Strong Answer**:  
*"We would implement three observability tiers:
1. **Operational Telemetry**: Latency, error rates, and throughput tracked via Prometheus and Grafana.
2. **Business & Compliance Metrics**: Track resolution rate vs escalation rate, total vouchers issued (INR value), and average waiver amounts.
3. **Trace Logging**: Centralize structured decision traces in OpenTelemetry or Datadog to audit any disputed customer claims."*

---

### 14. What are the key limitations of the current prototype?
**Strong Answer**:  
*"The prototype is deliberately scoped to demonstrate compliance and policy grounding:
1. Data is stored in structured local JSON rather than a live transactional database.
2. Voucher delivery is simulated through UI cards rather than sending live SMS/email bar codes.
3. The supervisor escalation generates an auditable ticket but does not have a live dual-sided supervisor portal in this single-screen demo."*

---

### 15. What would you improve in Version 2?
**Strong Answer**:  
*"In Version 2, I would:
1. Add a **Supervisor Dashboard** where escalated tickets (like Meher's ₹2,000 waiver) can be reviewed, approved, or rejected in real time.
2. Introduce **Multimodal Vouchers**: Generating Apple Wallet / Google Wallet boarding passes and QR vouchers for lounge and meals.
3. Add **Multilingual Support**: Supporting Hindi, regional Indian languages, and international languages through localized intent schemas."*
