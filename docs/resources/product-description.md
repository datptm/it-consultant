# Promise Hub: ideas, methodology, and MVP implementation approach

**IT Consultant Challenge 2026 · Round 1 · Company A (Danish building materials retailer)**

> *"Inventory doesn't sell. Customers buy the promise we keep."*

> **Note:** All figures in this document (store counts, baselines, KPIs, labor costs, etc.) are **the team's assumptions** for illustration and must be measured and confirmed in the MVP's first week.

---

## 1. Executive summary

| Content | Summary |
|---|---|
| **Chosen problem** | Fragmented systems: each country answers "Do we have it in stock? When can it be delivered?" differently, and no one fully trusts the answer. |
| **Core perspective** | Fragmentation is the **root cause** of the three remaining challenges (manual, inconsistent operations, unreliable delivery). |
| **Solution** | **Promise Hub**: a shared data layer and integration built on existing systems (ERP, POS, WMS), providing product information, inventory, and delivery date **with reliability**. |
| **Differentiator** | Rather than hiding inventory inaccuracies, **measure and act on them**: each answer has a confidence level so staff know when to promise and when to verify. |
| **MVP** | 12 weeks, pilot in Sweden, around 15 stores and 1 distribution center, only read data, no ERP replacement. |
| **Scale** | Shared core, adapters and country-specific configurations; each country has a "first win" different from the same platform. |

---

## 2. Context and problem

Company A is a leading Danish building materials retailer with hundreds of stores across Denmark, Norway, and Sweden, serving both businesses (B2B) and consumers (B2C). According to the challenge brief:

- Each country and region has developed its own systems and manual processes.
- Four related challenges: **manual processes, inconsistent operations, delivery and order handling, and fragmented systems**.
- Urgency differs by country (the brief says these issues *may* be especially relevant): Denmark leans toward manual processes, Norway toward store operations, and Sweden toward delivery.
- Management only wants to invest in **one** digital solution, but cannot implement it identically across the three countries.
- Highly competitive market, time to market is the key factor.

**Core question:** *Which area should Company A focus on first?*

---

## 3. Identify the issue (Identify)

### 3.1. The problem is a loss of trust in answers

Saying that each country uses different systems only describes the surface. At a specific moment, store staff cannot answer confidently and quickly: **What is this product, what does it cost, where is it available, and when can it be delivered?**

### 3.2. Cause and effect chain

```
Each country builds its own systems (history, acquisitions, local needs)
   → Product, price, and inventory data diverge and fall out of sync
      → Staff call, use spreadsheets, and reconcile manually (= manual processes)
      → Stores give customers different answers          (= inconsistent operations)
      → Wrong delivery promises and late deliveries       (= unreliable delivery)
         → Every improvement must be repeated three times and is hard to scale
```

The other three challenges are largely **symptoms**; fragmentation is the **root cause**.

### 3.3. Industry context supporting the argument

- Nordic countries have industry-specific product data standards (**NOBB** in Norway, **FINFO** in Sweden, **Byggebasen** in Denmark), so product data is not self-consistent across countries.
- Mergers and acquisitions are consolidating the Nordic building materials industry and are likely to contribute to fragmentation. Competitors' rapid growth increases the cost of delays.
- ERP systems are generally not designed to serve as a digital channel's product data source, so fragmentation becomes most visible when data must reach stores, the web, and B2B customers.

### 3.4. Who is affected

| Group | Pain point |
|---|---|
| Counter/cashier staff | Uncertain stock availability; must contact another store or warehouse, each country has a different interface |
| B2B customers (contractors, craftsmen) | Need to be certain of stock availability and delivery date to avoid project delays; incorrect delivery schedule results in lost customers |
| Individual customers (DIY) | Website shows stock available but store is out of stock |
| Order fulfillment and warehouse management | Planning based on delayed or incorrect data |
| Product data management | Introducing a new product to three markets requires multiple entries and standardization steps |
| Executive Board, IT Group | No consolidated data; each improvement must be redone for each country |

**Primary MVP persona:** a counter employee serving B2B customers (contractors).

**Illustrative scenario (hypothetical):** At 7 a.m., a contractor needs 60 sheets of drywall delivered by Thursday. The counter system says "in stock." The employee calls other stores and warehouses, makes three calls, spends 40 minutes, and promises Thursday. The goods actually arrive on Friday, stopping the project for a day.

---

## 4. Prioritization

### 4.1. Scoring Matrix

Score each option from 1 to 5 (subjective judgment based on the brief):

| Criteria (weight) | Manual | Store operations | Delivery | **Fragmentation** |
|---|---|---|---|---|
| Impact across three countries (25%) | 3 | 3 | 3 | **5** |
| Root cause and foundation (20%) | 2 | 3 | 2 | **5** |
| Speed to Value with MVP (20%) | 4 | 2 | 3 | 3 |
| Feasibility, Risk (15%) | 4 | 2 | 3 | 3 |
| Measurable ROI (10%) | 4 | 2 | 4 | 4 |
| AI potential (10%) | 4 | 3 | 4 | 4 |
| **Weighted score** | 3,35 | 2,55 | 3,00 | **4,10** |

### 4.2. Why Not Choose the Remaining Three Issues

- **Manual Process:** Can deliver results quickly, but automation on data is not reliable and tends to cause more errors.
- **Shipping and Order Processing:** Delivery promises depend on having reliable inventory data beforehand.
- **Store Operations:** To standardize workflows, consistent data and tools must be in place first.

### 4.3. Acknowledged Trade-offs

A "big bang" attempt to integrate every system would be slow and risky. The MVP therefore uses a **thin layer over existing systems, without replacing the ERP**.

---

## 5. Solution: Promise Hub

### 5.1. Five-layer architecture

| Layer | Component |
|---|---|
| **Experience** | Store Assistant App (web/tablet), B2B portal and website status widgets, management dashboard |
| **Shared Services** | Product Master, Unified Inventory, **Promise Engine** (ATP with reliability), Search |
| **Standard Data Model** | Product (mapping NOBB/FINFO/Byggebasen), Price, Stock, Delivery Promise |
| Integration | API gateway, event streaming, **country-specific adapter** |
| **Data source** | ERP, POS, WMS, TMS, supplier feed, e-commerce |

### 5.2. Design principles

1. **Strangler approach:** do not replace the old system, wrap and read data through the adapter; initial phase is read-only to reduce risk.
2. **Shared core, country-specific adapters:** aligns with the requirement "a strategic solution does not mean identical implementation."
3. **API first; favor configuration and ready-made components over custom development** to reduce time to market.
4. **Data sovereignty:** infrastructure located in EU, GDPR compliance, audit logs. This aligns with the organizers' "developing for Europe, by Europe" direction.

---

## 6. Core feature: a reliable promise

### 6.1. Concept

Inventory data **always has some uncertainty**. Instead of displaying a number as certain, Promise Hub shows it **with a confidence score** and the last verification time. Example staff screen:

```
13 mm moisture-resistant plasterboard (product code harmonized across NOBB/FINFO/Byggebasen)
Store: 40 sheets · Confidence 92% · Last checked 2 hours ago
Distribution center: 1,200 sheets · Confidence 97%
Delivery: Thursday · On-time probability 90%
[Promise to customer]   [Verify inventory]   [Report discrepancy]
```

### 6.2. Reliability score calculation

**Input (signal):**
- Time since last inventory check,
- Item throughput rate (faster rotation items are more error-prone),
- Historical error rates by item and location,
- Number of unsynchronized transactions,
- Source system latency,
- Product type (discrete, small items, bulky items).

**Action bands:**

| Band | Meaning | Suggested action |
|---|---|---|
| 🟢 High | Reliable | Promise immediately |
| 🟡 Medium | Needs checking | Scan or count quickly before promising |
| 🔴 Low | Unreliable | Do not promise; suggest another store, warehouse, or a more conservative delivery date |

**Cold start:**
- Weeks 1 to 6: score according to **rules** (e.g., deduct points based on days since last inventory check, unsynchronized transactions, historical discrepancies).
- From week 7: move to an **ML model** trained on historical inventory adjustments and periodic ERP count logs.
- **Calibration:** compare predicted probability with actual inventory check results (calibration curve, Brier score), to ensure "92%" truly means approximately 92% accurate.

### 6.3. Feedback loop (data flywheel)

Each time an employee clicks "Confirm" or "Incorrect," that feedback is recorded and becomes a training label. Staff become **data quality sensors**, supporting adoption of the change.

---

## 7. AI's Role

AI is used selectively, with the right technique for the right task:

| Function | Technique | Stage | Reason |
|---|---|---|---|
| Delivery Date | Rule + ML | MVP | Fixed constraints plus learning delay from history |
| Confidence scoring | Classical ML | MVP (rules first, ML later) | Needs calibrated probabilities at low cost |
| Abnormal inventory detection | Classic ML | MVP-lite | Pattern recognition on structured data |
| Product data harmonization (attribute mapping, duplicates, Danish/Norwegian/Swedish text) | Generative AI with human review | MVP | Unstructured text and many variants |
| Draft integration mappings and tests | Generative AI with developer review | MVP (during development) | Reduce the time and cost of each adapter when scaling |
| Natural language search in three languages | Generative AI, embeddings | MVP lite or Phase 2 | Staff can describe products without remembering codes |
| Demand forecasting and improved delivery date prediction | ML | Phase 2 | Requires clean Hub data first |

**Guardrails:** Keep models and data in the EU; use confidence thresholds and human review; retain full audit logs. The proposed uses appear low risk under the EU AI Act, but this must be checked before deployment. Also account for AI operating costs (tokens and quality evaluation).

---

## 8. Implementation of MVP

### 8.1. Hypotheses to verify

> *If B2B employees and customers have a single source of truth for products, inventory, and delivery dates with confidence, then the time to lookup, number of control calls, and error rate in promised deliveries will decrease significantly.*

### 8.2. Scope

| Within scope | Outside scope |
|---|---|
| 1 ERP adapter and 1 POS/WMS adapter at the pilot country (read-only) | ERP replacement |
| Standard data model for popular SKUs (assumed 10,000 to 20,000 SKUs) | Pricing, finance, HR |
| AI-assisted product data harmonization | Rebuild entire e-commerce |
| Unified inventory and Promise Engine for approximately 15 stores and 1 distribution center | Write-back all order types |
| Store Assistant App: search; nearby store and warehouse inventory; estimated delivery dates; data error reporting | Cross-border logistics, advanced forecasting |
| Dashboard KPI | |

**Why Sweden for the pilot (hypothetical):** The brief identifies delivery and order handling as major pain points there, so the value of a reliable delivery date should become clear quickly. Denmark is an alternative pilot location because it is the home market and may be easier to coordinate.

### 8.3. 12-Week Plan

| Week | Main activities | Handover results |
|---|---|---|
| **1–2 Discovery** | Interview staff and coordinators; select pilot and comparison stores; audit data (SKU duplicates, sampled inventory accuracy); establish baseline KPIs; obtain API access; review security and GDPR | Baseline report, priority SKU list, integration plan |
| **3–4 Foundations** | Canonical data model v1; read-only ERP adapter; event pipeline; product harmonization with a human review queue | Unified product and inventory data for priority SKUs |
| **5–6 Core features** | Unified Inventory; rules-based Promise Engine; Store Assistant alpha; test with two stores | Working demo with real data |
| **7–8 Refinement** | Inventory confidence ML model v1; feedback button; KPI dashboard; performance and security tests | Pilot-ready release |
| **9–10 Pilot** | Deploy to approximately 15 stores and one DC; train staff; assign a champion at each store; hold daily stand-ups for feedback | Real usage data |
| **11–12 Measure and decide** | Compare pilot stores with similar control stores; summarize findings; make a go/no-go decision; plan the next phase | Results report and expansion recommendation |

### 8.4. Suggested team (approximately eight people)

Product owner, architect, three integration/backend engineers, one data/AI engineer, one UX/frontend engineer, and one QA specialist.

### 8.5. Measuring effectiveness

- Measure **baseline at week 1** before intervention.
- Use a **control store** with similar scale and characteristics to isolate the impact of MVP from seasonal factors.
- Track outcome metrics (on-time performance, time saved) and adoption metrics (the share of staff using the tool weekly).

### 8.6. Stop or go criteria (go/no-go)

| Criteria | Threshold |
|---|---|
| Inventory display accuracy | ≥ 92% |
| Counter staff using it weekly | ≥ 60% |
| On-time promise accuracy | 5 percentage points above baseline |

**If not meeting 2 out of 3 criteria:** pause and adjust before scaling up, do not continue investing based on inertia.

---

## 9. Business Impact

| KPI | Baseline (assumed) | Pilot Goal | Expansion Goal |
|---|---|---|---|
| On-time promise accuracy | Measured in week 1 | +5 percentage points | +10 percentage points |
| Inventory display accuracy | ~85% | ≥ 92% | ≥ 95% |
| Time spent by staff for inquiry, reconciliation calls | Measured in Week 1 | −40% | −50% |
| Product Data Standardization Time | 4–6 weeks | ≤ 2 weeks | < 1 week |
| New Market Integration Time | 12 months or more | Not applicable | < 6 months |

**ROI Example (Illustrative):**

- Cost savings = number of stores × number of users × minutes saved per day × number of days × hourly labor cost.
- Example: 300 stores × 3 users × 10 minutes/day × 300 days ≈ 45,000 hours/year; at 35 EUR/hour ≈ **1.6 million EUR/year**.
- Add retained revenue from fewer lost orders caused by uncertainty about stock availability (actual revenue data is needed to calculate this).
- Add an estimate of MVP investment costs and the payback period, preferably as ranges.

---

## 10. Scale

### 10.1. Shared core and customization

| Shared (Global core) | Country-specific (Local) |
|---|---|
| Standard data model, integrated hub, API, security, monitoring | Country-specific ERP/POS/WMS adapters |
| Promise Engine, UX design, AI model | Product data standards (NOBB, FINFO, Byggebasen), language, currency (SEK, NOK, DKK) |
| Data governance process | Shipping rules, transport partners, B2B pricing agreements |
| | Training, change management, labor representative consultation (needs country-specific requirements check) |

**Configuration instead of code:** Differences between countries (shipping rules, units, taxes, language) are declared via configuration. Adding a country means adding a configuration package and an adapter.

### 10.2. One platform, three early wins

| Country | Pain point from the brief | First value from the Hub |
|---|---|---|
| **Sweden** (pilot) | Delivery and order handling | Reliable delivery dates |
| **Norway** (round 2) | Store operations | Store Assistant standardizes the experience at the counter |
| **Denmark** (third phase) | Manual processes | Automated data standardization and less manual reconciliation |

### 10.3. Timeline

Phase 0 platform and data cleanup → Phase 1 Sweden (12 weeks) → Phase 2 Norway → Phase 3 Denmark → expand Phase 2 capabilities (ordering, forecasting, B2B portal).

### 10.4. Deployment constraints

- **Peak construction season** (assumed spring to summer): avoid go-live and training during this period, set a freeze period for changes.
- **Source data quality:** requires data cleaning in Phase 0.
- **Performance and latency** when synchronizing near real-time.
- **Employee acceptance:** use champions at each store.

---

## 11. Risks and mitigation

| Risks | Mitigation |
|---|---|
| Data ownership dispute between countries | Data ownership by region, data governance council |
| Scope creep into an ERP replacement project | Signed-off out-of-scope list and go/no-go gates |
| Employees not using | Design with store employees, champion, track usage ratio |
| Supplier dependency | Open API, layered architecture |
| Poor source data | Data cleanup phase; confidence scores **expose** problems instead of concealing them |
| Lack of historical data for ML training | Kickstart with rules, switch to ML when sufficient data is available |

---

## 12. Main Assumptions

1. Each country has at least one ERP and a warehouse system with API or data export mechanism.
2. Approximately 300 stores (the description refers to 'hundreds').
3. Sweden has a delivery issue as per the example in the proposal.
4. The company accepts EU-based cloud infrastructure.
5. Baseline numbers, KPIs, and ROI are illustrative and confirmed by week 1.
6. The construction industry peak season is spring to summer.

---

## 13. Questions judges may ask and suggested answers

| Question | Response |
|---|---|
| Why choose fragmentation over more practical issues like delivery? | Fragmentation is the root and common cause for all three countries; delivery and manual processes require reliable data first. There is a scoring matrix and acknowledgment of trade-offs. |
| Is this not a multi-year ERP consolidation project? | No. Hub runs on the old system, read-only, 12-week scope, with a stop criteria. |
| Where will training data for the confidence model come from? | Begin with rules. From week 7, use historical inventory adjustments and counts from the ERP; staff feedback adds labels. |
| Why not use AI generation for everything? | Each function uses the right technique: delivery date calculation requires rules and ML, while attribute mapping or natural language search is better suited for AI generation. |
| How do you know the MVP is successful? | KPI baseline measured at week 1, control store, three clear go/no-go criteria. |
| What differs between the three countries? | Shared core; adapters, data standards, shipping rules, training are specific; each country has a different 'first win'. |
| Costs and ROI? | State an 8-person team estimate over 12 weeks, compared to illustrated benefits; confirm with pilot data. |

---

## 14. Appendix: 10-slide structure

| # | Slide | Role as per the proposal |
|---|---|---|
| 1 | Executive summary | Overview |
| 2 | Issues and root causes | Identify |
| 3 | Why prioritize this issue | Prioritise |
| 4 | Solution architecture | Solve |
| 5 | Core feature: Reliable promise | Solve |
| 6 | Where AI is used, where it is not used | AI |
| 7 | MVP scope, roadmap, stop criteria | Solve |
| 8 | Business impact | Business impact |
| 9 | Scale out | Scale |
| 10 | Risk, assumption, decision proposal | Conclusion |

**Scoring criteria comparison:**

| Criteria | Slide compliance |
|---|---|
| Problem Understanding | 2 |
| Prioritisation & Critical Thinking | 3, 6, 10 |
| Business Impact | 8 |
| Feasible solution | 4, 7, 9 |
| Structured thinking & Innovation | 5, 6, and the overall narrative |
