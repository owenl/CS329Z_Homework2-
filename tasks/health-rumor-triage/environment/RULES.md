# Verdict rules

Every claim in `claims.csv` is about exactly one evidence card in `evidence/`.
Judge each claim **only against that card**, not against outside knowledge.

Give each claim exactly one of these three verdicts:

- **SUPPORTED**: everything the claim asserts is stated in, or directly follows from, the card.
  It may say less than the card, or use weaker wording, but never more.
- **CONTRADICTED**: the card explicitly says the opposite of something the claim asserts
  (for example, the card says X does not reduce Y and the claim says X reduces Y, or the card
  says something is *not* the only cause and the claim says it *is* the only cause).
- **OVERSTATED**: the claim agrees with the direction of the card, the card does not
  explicitly deny it, but the claim goes beyond the card in at least one of these ways:
  1. **Strength**: a stronger effect than the card supports (e.g. "reduces" becomes "cures",
     "eliminates", or "completely prevents"; an *association* becomes a direct *cause*).
  2. **Population**: it applies the finding to a broader or different group than the card names
     (e.g. the card is about children or about patients with a condition, the claim is about
     adults or about everyone).
  3. **Number**: a larger number or effect size than the card gives.
  4. **Mechanism**: it adds a cause or mechanism that the card does not mention.

If a claim both goes beyond the card and is explicitly denied by it, use **CONTRADICTED**.

Clarifications:

- A direction that the card clearly implies counts as the card's direction (for example, calling
  something "an exception" to "no reduction" means it does reduce the outcome).
- If the card says there is no difference or no change (for example "equals, not beats" or
  "does not change"), a claim that one option is better or produces more is **CONTRADICTED**.
- A larger number or stronger effect is **OVERSTATED**, not CONTRADICTED, unless the card gives
  an explicit upper limit that the claim exceeds or says there is no effect at all.
- If the claim takes a finding from the card and draws a stronger conclusion from it
  (for example, "X is linked to Y, so doing X will completely remove Y"), that is **OVERSTATED**.
- Close paraphrases and translations of the card's wording count as stated in the card.
