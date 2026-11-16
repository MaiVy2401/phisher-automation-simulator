# PRD: PhishER Automation Confidence Simulator

| | |
|---|---|
| **Author** | Mai Vy Nguyen |
| **Status** | Prototype (synthetic data) |
| **Version** | 0.2, November 2026 |
| **Built with** | Python, Streamlit, Claude Code; optional Claude API for explanations |

> Personal prototype, not a KnowBe4 product. All data is synthetic (fictional company "Acme Dental").

---

## 1. Project information

A "what-if" simulator for PhishER that replays an organization's own past reported emails under any automation threshold setting. It shows the admin time saved next to the exact mistakes that would have happened, and recommends a setting for a chosen risk appetite.

**One line:** a test track that lets admins see how PhishER automation would have performed on *their* emails before they turn it on.

## 2. Objectives / goals

1. Increase the share of PhishER customers who turn on PhishML-based automation.
2. Cut admin time on the reported-email queue for customers who adopt it.
3. Keep safety: the recommended setting lets **zero threats through** on the customer's own history.
4. Make automation decisions explainable to the admin and their boss.

## 3. Assumptions & constraints

- PhishER keeps history of each report's PhishML label, confidence, and the admin's final disposition (to confirm with the PhishER team).
- **Key hypothesis to validate first:** many admins leave automation off or set very strict thresholds because they don't trust them. Validate with product analytics (% of customers with automation on) and churned-customer reasons.
- About 3 admin minutes per manual review (assumption; replace with real time-on-task data).
- Past performance doesn't guarantee future results. Attackers change, so the simulation should be re-run monthly.
- Needs enough history (for example, 100+ reports) for results to be meaningful.

## 4. Background & strategic fit

**Customer evidence.** On SDR discovery calls, former PhishER customers said reviewing reported emails took too much admin time, and that legitimate emails were misclassified.

**What already exists.** PhishER already provides:
- PhishML tags (Clean / Spam / Threat) with confidence levels
- Admin-chosen confidence thresholds
- Rule-based auto-actions
- PhishML Insights (explains up to three factors behind each decision)
- Automatic notifications to the person who reported the email
- PhishRIP and PhishFlip

Defend separately offers graymail sorting and abuse-mailbox automation.

**The gap.** The features exist, but the admin can't easily see what a threshold would do before trusting it. Picking a number feels risky, so automation stays low and admins keep reviewing by hand. That matches the "takes too much time" complaint.

**Why KnowBe4.** KnowBe4 uniquely owns the labeled history (the ML's guess plus the admin's final decision) needed to answer "what would have happened?" This supports the HRM platform promise of less admin work, and it protects renewals.

## 5. Scope: user stories & requirements

| ID | User story | Priority |
|---|---|---|
| US1 | As an IT admin, I want to see how many of my past reports would have been automated at a setting, so I know the time I'd save. | Must |
| US2 | As an IT admin, I want to see every mistake the setting would have made, ranked by severity, so I can judge the risk myself. | Must |
| US3 | As an IT admin, I want separate thresholds for Clean, Spam and Threat, because the cost of being wrong differs by label. | Must |
| US4 | As an IT admin, I want a recommended setting for my risk appetite, so I don't have to guess. | Must |
| US5 | As an IT admin, I want a plain-English summary I can send my boss, so they approve turning automation on. | Should |
| US6 | As a PM, I want to know what % of customers adopt the recommended setting, so I can measure impact. | Must |

## 6. Product features

| Feature | Description | Goal |
|---|---|---|
| What-if sliders | Per-label thresholds with live results on the customer's own history | Make the trade-off visible |
| Mistake list | Every automated error, ranked: threat let through ≫ real email removed ≫ clean/spam mix-up | Trust through transparency |
| Trade-off curve | % automated and mistakes across thresholds | Show there's no free lunch |
| Recommend | Grid search (1,331 combinations) for the most automation within a risk budget: Cautious / Balanced / Maximum savings | Remove guesswork |
| Cost view | Admin hours and dollars saved per month | Turn the trade-off into a business case |
| Claude explanation | Plain-English summary for the admin and their boss, using only computed numbers | Get approval faster |

### Risk budgets

| Risk level | Threats let through allowed | Real emails removed allowed |
|---|---|---|
| Cautious | 0 | ≤ 0.5% of reports |
| Balanced | 0 | ≤ 2% of reports |
| Maximum savings | ≤ 1 | ≤ 5% of reports |

### Illustrative results (synthetic data: 400 reports, 1 month, 3 min/review)

| Setting | Automated | Admin hours saved/month | Threats let through | Real emails removed |
|---|---|---|---|---|
| Nervous default (Clean 95%, Spam 90%, Threat 80%) | 22% | 4.5 | 0 | 6 |
| Cautious | 34% | 6.8 | 0 | 2 |
| Balanced | 38% | 7.7 | 0 | 8 |
| Maximum savings | 67% | 13.4 | 1 | 15 |

These numbers illustrate the trade-off; they are not real results.

## 7. Release criteria

- **Correctness:** simulator counts match a manual check on a sample of 50 reports.
- **Safety:** recommendations never exceed the chosen risk budget on the customer's history.
- **Usability:** 3–5 admins can explain what a setting would do after 2 minutes with the tool.
- **Performance:** recommendation runs in under 10 seconds on 5,000 reports.
- **Honesty:** the tool clearly states results are based on past data.

## 8. Success metrics (KPIs)

| Metric | Type | Target |
|---|---|---|
| % of PhishER customers with automation on | North Star (adoption) | Up vs. baseline within 2 quarters |
| Admin hours on the queue per month (adopters) | Outcome | Down 30%+ |
| Threats let through by automation | Guardrail | 0 |
| Real emails wrongly removed | Guardrail | Within the chosen budget |
| Admin override rate after turning automation on | Quality | < 5% |
| Churn of PhishER accounts citing "too much time" | Business, lagging | Down over 2 renewal cycles |

## 9. Exclusions (non-goals for v1)

- No new classifier: this evaluates PhishML, it doesn't replace it.
- No automatic change to live settings: the admin applies the recommendation themselves.
- No Defend integration in v1 (v2 idea: one simulator across PhishER and Defend).
- No real customer data in the prototype.

## 10. Risks & open questions

- **Is the hypothesis true?** If most customers already use automation, the problem lies elsewhere (for example, product confusion between PhishER and Defend).
- **Over-trust:** admins may treat past results as a guarantee. Mitigate with clear messaging and monthly re-runs.
- **Small histories** can give misleading results. Mitigate with a minimum-history requirement.
- **Label wording matters:** "Aggressive" was renamed "Maximum savings" because security admins avoid options that sound reckless. Test wording with real admins.

## 11. Next steps

1. Pull adoption data: what % of PhishER customers have PhishML auto-actions on, and at what thresholds?
2. Compare against churned accounts that cited "too much time."
3. If adoption is low, test the simulator with 3–5 admins and measure whether they turn automation on.
