# Promise Hub — Product Description

**Status:** Proposed retail product, supported by a local Promise Engine proof of concept (PoC)

**Intended organization:** Company A, a building materials retailer operating in Denmark, Norway, and Sweden

**Primary user:** Store staff handling customer requests for a specific quantity and pickup date

## Product overview

Promise Hub is a proposed shared service for answering a practical retail question: can a requested quantity of a product be supplied to a chosen store by a particular date, and how dependable is that answer? It would bring product, inventory, and route information from existing country systems into a common view. Its central component, the Promise Engine, evaluates eligible supply sources before recommending whether staff can make a commitment, should verify the information, or should decline the requested date or quantity.

The product is intended to support store conversations, particularly with contractors whose work depends on materials being available when expected. A store employee should be able to identify a product, enter the quantity and pickup store, and receive a decision with the selected source, available-to-promise quantity, earliest feasible date, and reasons for the decision. Inventory uncertainty is visible so staff can act on it instead of treating every stock figure as equally dependable.

This repository contains a **local, synthetic-data PoC** of the decision engine, a command-line interface, and a Streamlit demonstration. It does not connect to Company A's operational systems or make real customer commitments. The wider product and pilot described below are proposals, not deployed capabilities.

## Problem and objectives

Company A's country and regional operations use different systems and procedures. Product and stock records can be inconsistent, updated at different times, or interpreted differently by staff. When a customer asks for a specific quantity on a specific date, an apparent “in stock” value may still be unusable: units may be reserved, the record may be stale, or the supply route may be too slow. Employees then contact stores or distribution centers to confirm availability, delaying the answer and creating inconsistent commitments.

Promise Hub aims to provide a common decision process across countries while allowing local systems and fulfillment rules to differ. The initial outcome is a faster, more explainable pickup decision at the counter. The objectives are to:

- Show staff which eligible source could supply the request and when.
- Distinguish usable stock from raw on-hand stock by considering reservations, allocations, and uncertainty.
- Apply consistent stock and date checks before making a probability-based recommendation.
- Identify requests that require manual checking and explain what needs attention.
- Measure decision quality and operational outcomes before expanding beyond a pilot.

## Users and use cases

| User | Need | Intended support |
|---|---|---|
| Counter or sales employee | Answer a customer request for a product, quantity, pickup store, and date during a conversation. | Enter the request and see a decision with supporting details. |
| Store manager | Understand recurring inventory discrepancies and how often staff need to verify stock. | Proposed discrepancy reporting and pilot performance views. |
| Inventory or fulfillment coordinator | Identify whether a store or distribution center can supply the request. | See the selected source, available-to-promise quantity, route feasibility, and reason codes. |
| Product and data team | Improve product mapping, data freshness, and decision rules. | Proposed data quality measures and review of actual outcomes. |

The initial workflow is **store pickup**. A store may fulfill a request from its own stock, or a distribution center may supply that store over an eligible route. Customer-address delivery, split fulfillment, payment, reservation, and order creation are outside the current PoC.

### Typical staff workflow

1. Select the product, requested quantity, pickup store, and desired pickup date.
2. The engine finds eligible single-source routes and the latest inventory snapshot available at the request time for each source.
3. It excludes sources with stale stock data, too little available stock, or an earliest arrival after the requested date.
4. It assesses inventory reliability and estimates fulfillment and on-time performance for the remaining sources.
5. It selects a source and returns **PROMISE**, **VERIFY**, or **REJECT**, with dates, quantity, measures, and reasons.
6. If the result is **VERIFY**, staff check the underlying stock or route information before making a commitment. The PoC does not record that verification or automatically revise its decision.

The result is decision support, not a reservation. A production workflow would need an explicit handoff to order and inventory systems before a commitment could be secured.

## Functional capabilities

| Capability | Intended product behavior | Current PoC status |
|---|---|---|
| Product and location selection | Use consistent product and location identifiers across channels and countries. | Fixed synthetic catalog of 30 products, 10 pickup stores, and three distribution centers. |
| Inventory view | Combine source records and expose their freshness and reliability. | Reads local snapshots and calculates inventory confidence; no live feeds. |
| Available-to-promise (ATP) | Show quantity that can be offered after existing commitments and a safety buffer. | Calculates ATP for each candidate source; inbound stock is excluded. |
| Pickup-date evaluation | Check whether an eligible route can reach the pickup store by the requested date. | Uses route cutoffs, processing days, and transit business days for store pickup. |
| Promise decision | Recommend a commitment, verification, or rejection with reasons. | Implements PROMISE, VERIFY, and REJECT in Rules and ML modes. |
| Staff experience | Make the answer quick to read and explain at the counter. | Streamlit tabs show sample scenarios and permit manual request evaluation. |
| Feedback and monitoring | Record checks, actual picks, arrivals, and decision outcomes. | Synthetic historical outcomes are available for exploration; no live feedback or decision log. |
| Operational integration | Read existing ERP, POS, and warehouse systems through country adapters. | Proposed only; the PoC reads local files. |

### Decision meanings

- **PROMISE:** The selected source passes the hard feasibility checks and the current confidence and success thresholds. The result includes the requested date as the promised pickup date.
- **VERIFY:** A source is feasible, but the evidence does not meet the threshold for an automatic promise. Staff should confirm relevant stock or route information before committing.
- **REJECT:** No eligible single source can meet the request, or the confidence or success measure is below the rejection threshold. No promised pickup date is returned.

These labels describe a recommendation. They do not indicate that an order was placed, stock was reserved, or a customer was notified.

## Promise Engine decision process

A request contains a product ID, positive integer quantity, pickup location, desired date, delivery type, and request time. The PoC accepts a known product and location, the supported store-pickup type, and a date on or after the request date. It evaluates eligible sources independently, then selects one result.

### Inventory reliability and available stock

Inventory confidence describes how closely a stock record is expected to match an actual count. It is distinct from the chance of filling the entire requested order. In Rules mode, the PoC starts with a confidence score of 1.00 and reduces it for conditions including an old stock count, pending transactions, historical discrepancies, and high recent sales velocity. A stock snapshot more than 24 hours old is excluded even if its score would otherwise be high. In ML mode, an inventory model supplies the confidence estimate, but the same freshness exclusion applies.

Both modes calculate a conservative safety buffer and ATP:

    safety_buffer = ceil(on_hand × (1 − inventory_confidence) × 0.5)
    ATP = max(0, on_hand − reserved − allocated − safety_buffer)

The source is excluded when ATP is below the requested quantity. Expected inbound units are not counted as available. A favorable model prediction cannot override a stock shortage.

### Date and fulfillment assessment

For each candidate route, the engine calculates the earliest pickup date from the request time, route cutoff, processing time, and transit time. The current calendar treats Monday through Friday as business days and does not account for public holidays. A source is excluded if its earliest date is later than the desired date.

After the stock and date checks, the engine produces two further measures: whether the full quantity can be picked and whether a fully picked request arrives by the requested date. Rules mode uses fixed illustrative values based on stock margin and date margin. ML mode uses separate logistic regression classifiers trained on synthetic historical picks and deliveries. The engine multiplies the fulfillment and on-time outputs to create an illustrative combined success measure.

These outputs have **not** been calibrated or validated against real operational outcomes. The delivery model is trained only on orders picked in full, so its estimate is conditional on a full pick. The combined measure must not be interpreted as a verified probability that a real customer promise will succeed.

### Decision thresholds and source choice

| Condition after stock and date checks | Decision |
|---|---|
| Inventory confidence below 0.65, or combined success below 0.85 | REJECT |
| Inventory confidence at least 0.85 **and** combined success at least 0.95 | PROMISE |
| Remaining feasible cases | VERIFY |

If no source passes stock, freshness, and date checks, the engine returns REJECT with a no-feasible-single-source reason. When multiple candidates remain, it prioritizes a PROMISE result over VERIFY and REJECT, then compares the combined measure, inventory confidence, earliest date, and source ID. These threshold values are PoC parameters; a real deployment requires validation and an approved operating policy.

## Current proof of concept

The working PoC runs on a developer machine using local synthetic JSON files. A fixed sample reference time makes demonstrations repeatable. The bundled seven scenarios cover distribution-center supply, store stock, insufficient stock, an infeasible date, a narrow stock margin, low inventory confidence, and stale inventory.

| Streamlit tab | Purpose |
|---|---|
| **Sample scenarios** | Review bundled requests and their Rules or ML decisions. |
| **Evaluate a request** | Choose a product, quantity, pickup store, date, and mode; evaluate at the fixed reference time. |
| **ML training** | Train and save three local models, then inspect synthetic-data validation and test summaries. |
| **Data analytics** | Explore label balance and outcomes by product and source location. |

The command-line interface can run the sample scenarios or evaluate a supplied request. In CLI ML mode, models are retrained on each invocation. The web interface instead requires a previously trained, compatible local model bundle. Neither interface uploads data, sends requests to operational services, reserves stock, or records a real fulfillment outcome.

The PoC demonstrates the decision structure and the difference between fixed rules and learned estimates. Its synthetic labels reflect assumptions in the data generator, so apparent model accuracy and business rates cannot establish production performance. Implementation details, feature definitions, and a worked example are in [Data, features, and models](../data-features-models.md); setup instructions are in the [README](../../README.md).

## Proposed operating architecture

The intended production product would place a shared decision service over existing country systems. Exact interfaces and infrastructure would be chosen after discovering the retailer's available data and operating constraints.

| Layer | Proposed responsibility |
|---|---|
| Staff and channel experience | Store-facing request form and decision display; later, approved status views for other channels. |
| Promise service | Validate requests, calculate ATP and date feasibility, apply policy, and return traceable reasons. |
| Shared data model | Map product, location, inventory, route, and outcome records to consistent definitions. |
| Country adapters | Read local ERP, POS, warehouse, and transport data without requiring identical implementations. |
| Governance and measurement | Monitor data freshness, actual outcomes, staff verification, and model performance. |

The initial integration concept is read-only. It avoids changing the existing ERP or order process while source data and decision quality are being assessed. A production promise would eventually require a controlled reservation or order handoff, audit records, access controls, and reconciliation with source systems. Those are design requirements, not current PoC features.

Product mapping would need to respect local identifiers and catalog standards such as NOBB, FINFO, and Byggebasen where applicable. The shared core should use common definitions; country adapters and configuration should handle local catalog mappings, language, units, routes, and operating rules. Specific standards and deployment obligations require review with Company A.

## Proposed pilot and rollout

A proposed first pilot focuses on counter staff handling store-pickup requests. Sweden is a candidate because delivery and order handling were identified as a prominent concern in the challenge brief. The planning assumption is approximately 15 stores and one distribution center over 12 weeks. Those numbers are illustrative and depend on usable source data and pilot partners.

| Stage | Proposed work | Exit evidence |
|---|---|---|
| Discovery and baseline | Interview staff, inspect source data, define priority products and routes, and measure current lookup time and promise outcomes. | Agreed scope, baseline, data access, and decision policy. |
| Data foundation | Map product and location IDs, ingest selected inventory and route data, and assess freshness and quality. | Traceable inputs for pilot products and sources. |
| Rules and staff workflow | Deploy the rules-based decision path and store-facing view; test verification procedures with staff. | Staff can complete the scoped request flow and understand reasons. |
| Pilot and evaluation | Observe usage, actual picks, and arrival outcomes; compare with baseline and suitable comparison stores. | Evidence on reliability, adoption, and operational effort. |
| Expansion decision | Review data quality, errors, cost, and feedback before adding locations or ML. | Explicit decision to improve, extend, or stop the pilot. |

ML is optional for pilot completion. It should be introduced only if historical counts, picks, and arrivals have reliable timestamps and labels, and if the model improves decisions on held-out operational data. Later releases could add discrepancy reporting, feedback capture, additional fulfillment types, more countries, and other customer channels. These remain proposed capabilities.

## Success measures

Pilot success must be assessed against a measured baseline, not synthetic PoC data.

| Measure | What it shows | How to evaluate |
|---|---|---|
| Promise accuracy | Share of commitments fulfilled in full by the agreed date. | Link recorded decisions to actual pick and arrival outcomes. |
| Inventory accuracy and freshness | Whether shown stock is dependable at decision time. | Compare snapshots with physical counts and record update age. |
| Manual verification rate | How often staff need to confirm data before responding. | Track VERIFY outcomes and completed checks. |
| Time to answer | Effort needed to respond to a customer request. | Compare representative staff tasks before and during the pilot. |
| Staff adoption | Whether the workflow is practical in stores. | Measure eligible requests evaluated and active use by pilot staff. |
| Model calibration, if ML is used | Whether reported probability bands match observed frequencies. | Evaluate held-out real outcomes and analyze errors by product, source, and route. |

Targets of at least 92% inventory accuracy, at least 60% weekly use by counter staff, and a five-percentage-point improvement in on-time promise accuracy appeared in the initial concept. They are **proposed pilot targets**, not observed results or approved service levels. The pilot team should confirm definitions, baselines, sample sizes, and thresholds with Company A before using them as rollout gates.

## Dependencies and limitations

| Area | Implication |
|---|---|
| Source data quality | Missing, stale, or inconsistent records may force verification or rejection; reliable source timestamps are essential. |
| System access and ownership | Country teams must provide access, field definitions, and named owners for product, inventory, and route data. |
| Commitment process | A recommendation does not reserve units; operational integration is needed before a production commitment can be secured. |
| Model readiness | Synthetic results do not prove performance on real orders; rules remain the fallback until models are validated and monitored. |
| Local variation | Catalog identifiers, routes, working calendars, language, and store procedures may vary by country. |
| Pilot adoption | Staff need understandable reasons and a practical way to check doubtful stock. |

The current PoC supports one source per request, store pickup, weekday-based routing, and a fixed sample time in the web form. It does not support split fulfillment, public holidays, customer delivery, order writes, live data, automatic feedback capture, or calibrated production probabilities. Pilot requirements should determine which of these limits to address first.

## Related documentation

- [Technical design and implementation specification](technical-specification.md) describes the broader Promise Engine concept.
- [Data, features, and models](../data-features-models.md) defines implemented PoC behavior and limitations.
- [Synthetic data generation](../synthetic-data-generation.md) explains the local sample records.
- [README](../../README.md) provides installation, run commands, and the interface overview.
