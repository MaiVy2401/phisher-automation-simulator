# 🎚️ PhishER Automation Confidence Simulator (prototype)

**Problem.** KnowBe4 PhishER + PhishML can already auto-handle user-reported emails, but only above confidence thresholds the admin picks. Picking a number feels risky, so many admins keep reviewing everything by hand. Customers then say "PhishER takes too much time." The feature exists, but the trust doesn't.

**What this does.** A "what-if" test track. It replays an admin's own past reported emails (ML label + confidence + the admin's final decision) under any threshold setting, and shows:
- how much work would have been automated, and admin hours saved
- the exact mistakes that would have happened, ranked by severity (threat let through ≫ real email removed ≫ clean/spam mix-up)

It also recommends the setting with the most automation for a chosen risk appetite (Cautious / Balanced / Maximum savings), and Claude can explain it in plain English for the admin and their boss.

> Personal prototype, not a KnowBe4 product. All data is synthetic (fictional "Acme Dental", 400 reported emails).

## Run it
```bash
pip install -r requirements.txt
streamlit run app.py
```
The simulator works with no API key. Add an Anthropic key in the sidebar (or `.streamlit/secrets.toml`) for the Claude explanation.

## Files
- `app.py`: simulation engine, recommendation search, UI
- `reported_history.csv`: 400 synthetic reported emails with `ml_label`, `ml_confidence`, `admin_final_label`
