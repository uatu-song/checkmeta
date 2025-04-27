# 🎯 MetaZero v2 — Fairness & Parity Design Philosophy

## Why This Exists

**MetaZero** is a tactical simulation engine built around role asymmetry, narrative depth, and AI-driven combat. Because it blends stat-driven mechanics with cinematic, story-aware systems, maintaining **parity** (fairness and balance) requires active philosophy, testing protocols, and design guardrails.

This document outlines:
- What parity means in MetaZero
- Sources of potential bias
- Tools and methods to measure fairness
- Best practices to maintain healthy, narratively consistent balance

---

## ⚖️ What Parity Means in MetaZero

**Parity** is not the same as symmetry. In MetaZero:

- Some units (e.g., Sovereigns, Psi Operatives) are meant to feel disproportionately powerful.
- Fairness means: over time and across matchups, the simulation must avoid deterministic outcomes or role-favored win paths.

> "Fair doesn’t mean identical. Fair means that different choices have equal opportunity to succeed."

### Functional Definition:
- **Balanced Outcomes**: No team composition should statistically win more than 60% of matches over large samples without a narrative explanation.
- **Predictable Impact**: Traits, roles, and formations should behave consistently within defined rule sets.
- **Narrative Allowances**: Story-driven imbalance (e.g., scripted FL survival) is valid but must be declared.

---

## 🧠 Sources of Bias

### Mechanical Bias
- Fixed actor order (before initiative shuffle)
- Deterministic trait triggers without randomness or gating
- Formation stacking without shared cooldown

### Statistical Bias
- Overpowered synergy chains (e.g., FL+VG+EN + morale stacking)
- Trait overloading (units with too many active/passive combos)
- Role absence (lack of FL/SV in one team)

### Narrative Bias
- Scripted outcomes (e.g., Pulse Lockdown always succeeds)
- Draft imbalance (if story justifies team quality divergence)
- Survival logic override (Phoenix moments)

---

## 🧪 Testing for Fairness

### Recommended Tests
- **Mirrored Match Runs**: Run 1,000 matches of A vs B, then B vs A using same units and logic.
- **Formation Trigger Count**: Track how often each formation is called successfully by FL.
- **Trait Activation Spread**: Ensure traits activate across roles, not just high-frequency positions (e.g., FL/PO).
- **Synergy Usage**: Count per-match synergy contributions per team.
- **KO Distribution**: Watch for lopsided kill rates by unit type.

### Metrics to Track
- Win rate per team across 1,000 mirrored matches
- Average survivors per team
- XP per unit (top quartile skew)
- Momentum transitions (which team enters crash more)

---

## 🧱 Engine-Level Safeguards

| Safeguard | Description |
|----------|-------------|
| Buffered Damage | All actions planned before execution to prevent first-strike bias |
| Randomized Initiative | Slight random variance avoids deterministic loops |
| Trait Cooldowns | Prevent over-spamming of effects |
| One SV Per Team | Role restriction for high-impact entities |
| FL Required | All matchups must include an FL per side |
| Formation Check | Only one formation per team per round |
| Momentum Gating | Some traits/strategies only activate in certain team states |

---

## 🧰 Tools Available

- `simulate_mirrored_match(teamA, teamB, N=1000)`
- `analyze_synergy_actions(log)`
- `evaluate_trait_distribution(trait_log)`
- `momentum_state_tracker(team_morale)`
- `XP_engine.compare(role)`

These utilities are either present or stubbed in `meta_zero/postmatch`, `state`, and `command` modules.

---

## 📜 When Bias is Allowed

There will be moments — like end-of-week story beats — where imbalance is necessary. Examples:

- **Phoenix Transport** scripted saves
- **Sovereign Erasure** (Week 4 finale)
- **AI Glitch Prevention** mechanics

These should be **declared in narrative logs**, and their effects isolated from engine parity metrics.

---

## ✅ Summary: Designing for Fairness

> Parity isn't just an outcome — it's a process of asking:
> - Was this match fair?
> - Was this outcome expected given roles, synergy, and stats?
> - Can the losing team win with slightly different inputs?

If the answer is consistently "yes," you have a healthy simulation. Keep tracking. Keep iterating. Keep it fair.

---

Let every punch, psychic wave, and formation call feel earned.
