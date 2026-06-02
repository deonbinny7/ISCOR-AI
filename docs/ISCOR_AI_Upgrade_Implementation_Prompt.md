# ISCOR AI — Upgrade Implementation Prompt (LLM activation + feature depth)

Paste this into your coding agent. It fixes two distinct problems: (1) the LLM layer isn't actually generating anything right now, and (2) even once it is, the product only shows a fraction of what the pipeline can do. Do Part A completely before touching Part B — there's no point enriching a UI that's still displaying template text as if it were AI-generated.

---

## Context to give the agent

```
ISCOR AI's backend pipeline (normalize -> SHAP -> risk gate -> report) works
correctly, but the LLM layer is currently inactive by default: service.py
only calls the real LLM if ISCOR_USE_LLM=1, otherwise it silently falls back
to _deterministic_report(), a templated text generator. The user has been
running the app without knowing this, so everything they've seen so far is
template text, not LLM output. Fix that first, then add the missing feature
depth so the product reflects the full pipeline, not just the form-to-card
happy path.
```

---

# Part A — Actually turn the LLM on

## A1. Make the LLM path real and verifiable
1. Set `ISCOR_USE_LLM=1` in the local `.env` and confirm an actual API key (OpenAI, or an Ollama endpoint for an open-weight model) is configured and reachable.
2. In `service.py`, add explicit logging at the point where the branch decision is made: log which path was taken (`"llm"` or `"deterministic_fallback"`) and, if fallback, *why* (exception message, missing key, timeout, etc.) — not just silently swallowed.
3. Add a startup check that warns loudly (not a buried log line) if `ISCOR_USE_LLM=1` but no valid API key/endpoint is reachable, so this specific failure mode can never again go unnoticed.

**Acceptance criteria:** run one screening with the flag on and a valid key — confirm in the logs it actually took the `"llm"` path, and that the generated explanation text is demonstrably not from the deterministic template (different wording each run, not the same fixed sentence structure).

## A2. Surface generation source in the UI (accountability, not just correctness)
Add a small, honest label on the report card: "AI-generated" vs "Standard summary" depending on which path actually ran. This matters for two reasons: it stops this exact confusion from happening again, and — more importantly for your defense — it's a genuinely good design decision to be transparent about when the system is and isn't using the LLM.

**Acceptance criteria:** toggle `ISCOR_USE_LLM` off and on, confirm the UI label changes to match reality each time.

## A3. Split the single generation into the three constrained calls from the original plan
Right now (per the reviewed flow) it sounds like there's one LLM call producing `explanation` + `wellness_suggestions` together. Split into three separate constrained generations, each with its own tightly scoped prompt:
1. **Explanation** — plain-language account of the top SHAP factors only.
2. **Wellness suggestions** — lifestyle-level only, explicitly forbidden from medication/clinical content.
3. **Weekly micro-plan** — a simple 7-day lifestyle plan (this exists in the original plan's report spec, Section 8.5, but isn't implemented yet).

Each call still only receives the structured SHAP JSON contract, never raw questionnaire answers.

**Acceptance criteria:** three distinct fields returned from the backend (`explanation`, `wellness_suggestions`, `weekly_plan`), each independently regenerable, each visibly different in wording from run to run when the model is actually being called.

---

# Part B — Add the feature depth that's currently missing

## B1. Trend view across screening history
The DB already stores multiple screenings per user (`fetch_history()` exists). Nothing currently visualizes them together.
- Add a simple line/area chart: risk probability over time across past screenings.
- Add a short LLM-generated one-line trend summary ("your stress-related risk factors have been trending down over your last 3 screenings") — same constrained-input pattern: feed it only the sequence of past risk labels/top factors, never raw answers.

**Acceptance criteria:** a user with 3+ saved screenings sees an actual trend chart, not just a flat history list.

## B2. Real multi-turn chat surfaced properly
The `/chat` endpoint exists and is wired to the LLM, but confirm it's actually visible and usable as a real conversation thread in the UI (not a single input box that disappears after one question) — persist and display the full `ConversationHistory` for a loaded report, with the crisis-mode block clearly shown (not just silently refusing) when `crisis_mode=True`.

**Acceptance criteria:** ask 3 follow-up questions in a row on a loaded report and see all of them plus their answers rendered as a thread, not just the latest exchange.

## B3. Richer SHAP visualization
Replace (or upgrade) the current factor display with a proper horizontal bar chart: bars colored by direction (increases vs decreases risk), sorted by magnitude, with the SHAP value shown numerically in the IBM Plex Mono styling that's already in your CSS token system. If a charting library isn't already in the Streamlit app, `st.plotly_chart` or a simple custom component both work well here.

**Acceptance criteria:** the top-factors section visually communicates both direction and relative magnitude at a glance, not just a text list.

## B4. Build out the landing/trust content, not just the form
Right now the app is essentially "form → result." Add lightweight but real page structure (Streamlit's multipage support or `st.tabs`/sidebar navigation is enough — this doesn't need to be the full React rebuild):
- A short landing/intro section using the copy direction and visual tokens already established (dawn/lavender/cloudlight palette, Fraunces/Inter/IBM Plex Mono) — explain in 2–3 sentences what the tool is and isn't before the form.
- A "How it works" section reflecting the real 4-stage pipeline (Screen → Predict → Explain → Guide).
- A short trust/privacy section (what's stored, what's encrypted, the escalation path) — this can be short, but it needs to exist somewhere visible, not just in your report document.

**Acceptance criteria:** a first-time visitor sees context before the form, not just a bare form as the entire homepage.

## B5. (Optional, only if time allows) Light RAG grounding for wellness suggestions
Ground the wellness-suggestion generations in a small curated set of vetted psychoeducation snippets (sleep hygiene, stress management basics) rather than relying purely on the LLM's parametric knowledge — retrieve the most relevant snippet(s) based on the top SHAP factors and include them in the prompt context. This is explicitly listed as future work in the original plan; only take this on once Parts A and B1–B4 are solid.

---

## Suggested order of execution

```
A1 (turn LLM on for real) → A2 (surface generation source) → A3 (split into 3 calls)
→ B3 (SHAP visualization) → B1 (trend view) → B2 (chat thread) → B4 (landing content)
→ B5 (optional RAG grounding, only if time allows)
```

A comes first, full stop — every part of B will look and feel different once the LLM is actually generating text, so building B on top of the current template output would mean redoing evaluation work later.

## Definition of done

You should be able to hand someone a screening result and have them independently notice: the explanation reads differently every time they regenerate it, there's a visible trend across repeat screenings, they can hold an actual back-and-forth conversation about their result, and the page they land on before ever filling out the form actually tells them what ISCOR AI is. If any of those four things isn't true yet, the upgrade isn't done.
