# Loop 22 — Metric Definitions & Invariant Accounting Ledger

**Mathematical Formulations and Verification Ledger for DocuReady Evaluation**

---

## 1. Metric Definitions

Let $N$ be the total number of eligible critical fields evaluated across the benchmark corpus.
Every field must be classified into exactly one mutually exclusive outcome:
- $V_{\text{exact}}$: Verified Claim, Spatially Exact Match
- $V_{\text{false}}$: Verified Claim, Spatial Mismatch or Spurious Value
- $A$: Abstained Field (Transparently withheld from verification)

From these base counts, we derive:
1. **Total Verified Claims ($V$):**
   $$V = V_{\text{exact}} + V_{\text{false}}$$

2. **Total Evaluated Claims ($N$):**
   $$N = V + A = V_{\text{exact}} + V_{\text{false}} + A$$

3. **Verification Coverage Rate ($\text{Cov}$):**
   $$\text{Cov} = \frac{V}{N}$$

4. **Abstention Rate ($\text{AR}$):**
   $$\text{AR} = \frac{A}{N}$$

5. **Critical Field Precision ($\text{CFP}$):**
   $$\text{CFP} = \frac{V_{\text{exact}}}{V}$$

6. **False Verification Rate ($\text{FVR}$):**
   $$\text{FVR} = \frac{V_{\text{false}}}{V}$$

7. **Spatial Exact Match Rate ($\text{SEM}$):**
   $$\text{SEM} = \frac{V_{\text{exact}} + A_{\text{empty\_correct}}}{N}$$

---

## 2. Mathematical Invariants & Verification Ledger

The evaluation pipeline strictly enforces three non-negotiable closed accounting invariants:

### Invariant 1: Exhaustive Partition
$$V + A \equiv N \quad \iff \quad 70 + 25 = 95 \quad (100.00\%)$$

### Invariant 2: Coverage vs Abstention Complementarity
$$\text{Cov} + \text{AR} \equiv 1.0000 \quad \iff \quad 0.7368 + 0.2632 = 1.0000$$

### Invariant 3: Precision vs False Verification Complementarity
$$\text{CFP} + \text{FVR} \equiv 1.0000 \quad \iff \quad 0.9571 + 0.0429 = 1.0000$$

No field is counted multiple times. No unextracted field is counted as verified. No denominator changes between cohorts.
