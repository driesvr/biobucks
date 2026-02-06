---
name: biobucks
description: Generate comprehensive DCF (Discounted Cash Flow) valuations for biotech assets with AI-powered market research. Use when the user wants to value a biotech asset, create a DCF model, analyze drug development economics, or assess therapeutic area market potential. Triggers include mentions of valuation, DCF, biotech asset analysis, drug pricing, market research, clinical trial costs, or NPV/IRR calculations.
allowed-tools: WebSearch, WebFetch, Read
---

# Biotech DCF Valuation Skill

This skill generates comprehensive Discounted Cash Flow (DCF) valuations for biotech assets by researching current market data, pricing, clinical trial costs, and development timelines using web search, then structuring all parameters needed for financial modeling.

## Reference Data

This skill includes a curated reference dataset with clinical phase transition probabilities and trial costs:

**File**: `clinical_trial_reference_data.json` (in the same directory as this SKILL.md)

**Contents**:
- Phase transition probabilities by therapeutic area (12 areas) from BIO/QLS Advisors (2011-2020)
- Clinical trial costs by phase and therapeutic area from ASPE/HHS
- Per-patient costs by therapeutic area and modality
- Indication-specific data for high-value indications (Alzheimer's, breast cancer, NSCLC, T2D, RA, MS, etc.)
- Adjustment factors for biomarkers, orphan drugs, breakthrough designations, etc.

**Usage**: Load this file at the start of each valuation to get baseline values. Then search for more specific/recent data to refine the estimates. The reference data provides well-sourced defaults; web search should be used to find indication-specific or more current information.

## Instructions

When a user requests a biotech valuation, follow these steps systematically:

### Step 1: Gather Asset Information

Collect the following details about the asset (ask if not provided):
- **Asset name**: Drug/therapy name or target indication
- **Therapeutic area**: Disease category (oncology, rare disease, CNS, etc.)
- **Mechanism of action**: How the drug works (e.g., "anti-PD-1 antibody", "CRISPR gene therapy")
- **Modality**: Drug type (small molecule, antibody, gene therapy, cell therapy, etc.)
- **Current development stage**: The asset's position in development. Use these options:
  - **"Phase I Ready"**: Ready to start Phase I trials
  - **"Phase II Ready"**: Phase I complete, ready to start Phase II trials
  - **"Phase III Ready"**: Phase II complete, ready to start Phase III trials
  - **"Registration Ready"**: Phase III complete, ready for regulatory submission
  - **"Approved"**: Regulatory approval obtained
- **Biomarker status**: Ask the user about biomarker-driven patient selection

**IMPORTANT**: When the user says "Phase I" or selects "Phase I Ready", this means the asset is AT THE BEGINNING of Phase I (i.e., Phase I has not started yet, but is about to). Therefore, you must include Phase I costs and timelines in your valuation.

### Step 1.5: Ask About Biomarkers

**CRITICAL**: Before proceeding with research, ask the user about biomarker status for patient selection. This significantly impacts success probability estimates.

Ask: "Does this clinical program use biomarkers for patient selection or stratification?"

Explain why this matters: According to BIO/QLS Advisors (2021) analysis of 12,728 clinical phase transitions (2011-2020), biomarker-driven patient selection improves overall likelihood of approval from 7.6% to 15.9% (**2.09x improvement**). However, this improvement is **phase-specific and non-uniform**:

**Phase-specific biomarker effects:**
- **Phase I→II**: 52.0% → 52.4% (1.01x multiplier — essentially no difference)
- **Phase II→III**: 28.3% → 46.3% (1.64x multiplier — largest benefit)
- **Phase III→Approval**: 57.1% → 68.2% (1.19x multiplier)

**Key insight**: Biomarker benefit is overwhelmingly concentrated in Phase II (1.64x), with meaningful Phase III benefit (1.19x), and negligible Phase I impact.

**Important limitation**: Biomarker-stratified programs are heavily skewed toward oncology. Generalizability to other therapeutic areas is uncertain.

Biomarker options to present:
- **Yes - Validated biomarker**: A well-established biomarker with regulatory acceptance (e.g., HER2 for breast cancer, PD-L1 for immunotherapy, EGFR mutations in NSCLC). Apply full phase-specific multipliers: 1.01x (Phase I→II), 1.64x (Phase II→III), 1.19x (Phase III→Approval).
- **Yes - Exploratory biomarker**: Using a biomarker for enrichment but not yet fully validated. Apply 50-75% of the full multiplier effect: ~1.01x (Phase I→II), ~1.32-1.48x (Phase II→III), ~1.10-1.14x (Phase III→Approval).
- **No - No biomarker selection**: Broad patient population without biomarker stratification. Use baseline success rates (no adjustment).
- **Unknown/TBD**: Biomarker strategy not yet determined. Use baseline rates but note this as an opportunity for improvement.

Record the biomarker status in the output JSON and apply the appropriate phase-specific adjustment factors to probability of success calculations.

### Step 2: Research Market Parameters

Use WebSearch extensively to find current, authoritative data for each parameter. **Geographic scope: United States market only.** For each parameter, cite:
- **Value** with units
- **Source** (organization/publication name and specific report/document title)
- **Source URL** (CRITICAL: Must be a direct, specific link to the exact report, PDF, data table, or page containing the data - NOT just a homepage or general site URL. Examples: link to specific PDF report, direct link to data table page, specific press release URL, exact statistics page)
- **Explanation** (1-2 sentences justifying the value)
- **Confidence level** (High/Medium/Low based on source quality and recency)

**URL Requirements:**
- ✓ GOOD: https://www.fda.gov/media/123456/download (specific PDF)
- ✓ GOOD: https://seer.cancer.gov/statfacts/html/lungb.html (specific data page)
- ✓ GOOD: https://investor.company.com/news-releases/2024/press-release.pdf (specific press release)
- ✗ BAD: https://www.fda.gov (just homepage)
- ✗ BAD: https://www.cancer.org (general site)
- Use WebFetch to verify the URL actually contains the cited data

Research these market parameters:

1. **Total Addressable Market (TAM)**
   - **CRITICAL**: TAM must reflect the *treatment-eligible* population, NOT the total disease prevalence
   - **Narrow the population down by these factors**:
     a. **Disease stage**: Identify which stages the therapy targets (e.g., early-stage, locally advanced, metastatic). Patients with late-stage/terminal disease may not be treatment candidates. Search "[indication] stage distribution", "[indication] metastatic vs early stage proportion"
     b. **Molecular/genetic subtype**: For targeted therapies, only patients with the specific driver mutation or biomarker are eligible. Search "[indication] [mutation] prevalence" (e.g., "NSCLC EGFR mutation prevalence", "breast cancer HER2-positive percentage")
     c. **Treatment access/uptake**: Not all eligible patients receive treatment (geographic access, patient choice, diagnosis rates). Search "[indication] treatment rate", "[indication] diagnosis rate". **However**, for indications with no efficacious treatment or significant unmet need, a novel mechanism or superior drug may *increase* treatment uptake beyond historical rates—patients who previously declined ineffective options may now seek treatment. Factor this into estimates for first-in-class or breakthrough therapies in underserved indications.
   - **IMPORTANT: Calculate refined TAM**: TAM = Total prevalence × stage-eligible % × biomarker-positive (if applicable) % × treatment uptake %. You must calculate it, not guess a number
   - **Example**: NSCLC with EGFR inhibitor: 230,000 NSCLC cases × 70% advanced/metastatic × 15% EGFR+ × 85% uptake = ~20,500 patients (NOT 230,000)
   - Search: "[indication] prevalence [current year]", "[indication] incidence rate", "[indication] [biomarker] positive rate", "[indication] stage at diagnosis distribution"
   - Look for: WHO data, CDC reports, SEER database, patient advocacy organizations, epidemiology studies, genomic profiling studies
   - Express as: Number of treatment-eligible patients with calculation breakdown (e.g., "20,500 patients annually in US: 230,000 NSCLC × 70% advanced × 15% EGFR+ × 85% uptake")

2. **Peak Market Share**
   - **CRITICAL**: Conduct a competitive landscape analysis before estimating market share
   - **Competitive Landscape Analysis Steps**:
     a. **Identify approved competitors**: Search "[indication] approved drugs [current year]", "[indication] standard of care"
        - List all currently approved drugs for this indication
        - Note their mechanism of action, efficacy, and market dominance
     b. **Identify pipeline competitors**: Search "[indication] pipeline", "[indication] clinical trials phase 3", "[therapeutic area] drugs in development"
        - List drugs in Phase III or later that will likely launch before or around the same time
        - Note their mechanisms, differentiation, and expected approval timeline
     c. **Assess differentiation**: Compare the asset's profile to competitors
        - Is this first-in-class, best-in-class, or me-too?
        - What clinical advantages exist (efficacy, safety, dosing convenience)?
        - Are there biomarker-selected populations with less competition?
     d. **Estimate competitive dynamics**: Consider how the market will be divided
        - Highly competitive markets (>5 similar drugs): 5-15% peak share
        - Moderately competitive markets (2-4 drugs): 15-30% peak share
        - First-in-class or dominant best-in-class: 30-60% peak share
        - Niche/orphan with limited competition: 40-80% peak share
   - **Document your analysis**: In the explanation field, summarize:
     - Number of approved competitors and their market shares
     - Number of pipeline competitors expected to launch
     - Asset's key differentiation factors
     - Rationale for the estimated peak share
   - Search: "[indication] competitive landscape", "[therapeutic area] market share", "first-in-class [mechanism] adoption"
   - Consider: Number of competitors, differentiation, unmet need, first/best-in-class status
   - Express as: Percentage (e.g., "15% peak market share")
   - **Example explanation**: "Estimated 18% peak share. Currently 4 approved drugs (Drug A: 35%, Drug B: 28%, Drug C: 22%, Drug D: 15%). Two pipeline competitors expected. This asset offers superior safety profile and oral dosing vs. current IV standards, supporting above-average new entrant share."

3. **Years to Peak Adoption**
   - Search: "[indication] drug adoption curve", "[therapeutic area] time to peak sales"
   - Consider: Disease severity, competition, patient switching barriers
   - Typical range: 3-7 years for competitive markets, 5-10 for slower adoption
   - Express as: Years (e.g., "5 years to peak")

4. **Pricing (Annual Cost Per Patient)**
   - Search: "[comparable drug] price [current year]", "[therapeutic area] drug pricing", "[modality] annual cost of therapy"
   - Look for: FDA press releases, pharma press releases, analyst reports, GoodRx, healthcare cost studies
   - Consider: Comparable therapies, value-based pricing, orphan vs. broad markets
   - Express as: USD per patient per year (e.g., "$150,000/patient/year")

5. **Loss of Exclusivity (LOE) Year**
   - Calculate: Approval year + regulatory exclusivity period
   - Typical exclusivity: Small molecule (~12 years patent), Biologics (12 years BPCIA), Orphan drugs (7 years)
   - Search: "[indication] orphan designation", "biologics exclusivity period"
   - Express as: Year from now (e.g., "Year 12" meaning 12 years after approval)

6. **Years to Decline Post-LOE**
   - Search: "generic erosion timeline", "market share decline after patent expiry", "branded drug sales post-LOE"
   - Consider: Time for generic competition to fully erode branded market share
   - Typical range: 3-5 years for most drugs, faster for highly competitive markets
   - Express as: Years (e.g., "5 years" for decline period after LOE)

7. **Terminal Market Share**
   - Search: "branded drug market share with generics", "post-patent market retention", "terminal market share pharmaceuticals"
   - Consider: Residual branded share after generic competition stabilizes
   - Typical range: 10-30% for brands with strong loyalty, lower for commoditized drugs
   - Express as: Percentage (e.g., "20%" of original peak share retained long-term)

### Step 3: Research Development Timeline

Research phase-specific parameters for each remaining phase. **IMPORTANT**: Research the duration of EACH phase individually, not just total years to approval.

**For the CURRENT phase and all future phases**, research:

8. **Phase I Duration**
   - Search: "Phase 1 clinical trial duration [therapeutic area]", "Phase I timeline [indication]"
   - Consider: First-in-human safety studies, dose escalation complexity
   - Typical range: 1-2 years (6-18 months for most drugs)
   - Express as: Years (e.g., "1.5 years")
   - Include if current stage is "Phase I Ready"
   - Skip if current stage is "Phase II Ready" or later

9. **Phase II Duration**
   - Search: "Phase 2 clinical trial duration [therapeutic area]", "Phase II proof-of-concept timeline"
   - Consider: Patient enrollment, endpoint complexity, adaptive designs
   - Typical range: 2-3 years for most indications
   - Express as: Years (e.g., "2.5 years")
   - Include if current stage is "Phase I Ready" or "Phase II Ready"
   - Skip if current stage is "Phase III Ready" or later

10. **Phase III Duration**
    - Search: "Phase 3 clinical trial duration [therapeutic area]", "Phase III pivotal trial timeline"
    - Consider: Large patient populations, long follow-up periods, multiple sites
    - Typical range: 2-4 years (oncology often 3-5 years, rare disease may be shorter)
    - Express as: Years (e.g., "3.5 years")
    - Include if current stage is "Phase I Ready", "Phase II Ready", or "Phase III Ready"
    - Skip if current stage is "Registration Ready" or "Approved"

11. **Approval/Regulatory Duration**
    - Search: "FDA NDA review timeline", "regulatory approval timeline [country]"
    - Consider: Standard review (10 months) vs Priority review (6 months), additional back-and-forth
    - Typical range: 1-2 years including preparation and review
    - Express as: Years (e.g., "1.5 years")
    - Include unless current stage is "Approved"

### Step 4: Research Clinical Trial Costs and Probability of Success

**FIRST**: Load the reference data file `clinical_trial_reference_data.json` to get baseline values for the therapeutic area and indication. Use the Read tool to access the file at the same path as this SKILL.md. If the file is not accessible, continue with web search using the sources mentioned in the reference data metadata (BIO/QLS Advisors, ASPE/HHS) as baseline sources.

The reference data contains:
- `phase_transition_probabilities.by_therapeutic_area` - baseline PoS by therapeutic area
- `phase_transition_probabilities.by_modality_detailed` - PoS adjustments by drug type
- `clinical_trial_costs.per_patient_costs_by_therapeutic_area` - cost benchmarks
- `clinical_trial_costs.by_modality_cost_multipliers` - cost multipliers by drug modality
- `indication_specific_data` - detailed data for specific indications (Alzheimer's, breast cancer, NSCLC, T2D, etc.)
- `adjustments_and_factors` - multipliers for biomarkers, orphan drugs, breakthrough designations

**THEN**: Search for more specific or recent data to refine the baseline estimates.

12. **Clinical Trial Costs by Phase**
   - **Start with reference data**: Look up costs for the therapeutic area in `clinical_trial_costs.per_patient_costs_by_therapeutic_area` and `clinical_trial_costs.average_costs_by_phase`
   - **Search for specifics**: "clinical trial cost [therapeutic area] [current year]", "[modality] trial costs", "cost per patient [indication] trial"
   - Look for: Tufts CSDD reports, Pharma Intelligence, Evaluate Pharma, recent biotech financial disclosures
   - Consider: Patient enrollment numbers, trial duration, endpoint complexity, rare vs. common disease
   - **Apply modality adjustments**: Cell therapy and gene therapy trials cost significantly more (see `clinical_trial_costs.by_modality_cost_multipliers` in reference data)
   - **IMPORTANT**: Research costs for the CURRENT phase AND all future phases. Remember that "Phase I Ready" means at the BEGINNING of Phase I:
     - If current stage is "Phase I Ready", research Phase I, Phase II, Phase III, and Approval costs
     - If current stage is "Phase II Ready", research Phase II, Phase III, and Approval costs
     - If current stage is "Phase III Ready", research Phase III and Approval costs
     - If current stage is "Registration Ready", only research Approval costs
     - If current stage is "Approved", skip all clinical trial costs
   - Express as: Total USD per phase
     - Phase I: $1M - $5M (20-100 patients) - higher for cell/gene therapy
     - Phase II: $7M - $20M (100-300 patients)
     - Phase III: $20M - $100M+ (300-3,000 patients) - oncology often exceeds $40M
     - Approval costs (regulatory filing): $1M - $5M

13. **Probability of Success (PoS) by Phase**
   - **Start with reference data**: Look up baseline PoS in `phase_transition_probabilities.by_therapeutic_area.[area]`
   - **Check for indication-specific data**: Look in `indication_specific_data` for the specific indication if available
   - **Apply biomarker adjustment (phase-specific)**: If the user confirmed biomarker-driven selection (from Step 1.5), apply **phase-specific multipliers** from `biomarker_impact.phase_specific_multipliers`:
     - **Phase I→II**: Multiply baseline PoS by 1.01 (for validated biomarkers) or ~1.01 (for exploratory biomarkers) — essentially no adjustment
     - **Phase II→III**: Multiply baseline PoS by 1.64 (for validated biomarkers) or 1.32-1.48 (for exploratory biomarkers) — largest benefit
     - **Phase III→Approval**: Multiply baseline PoS by 1.19 (for validated biomarkers) or 1.10-1.14 (for exploratory biomarkers)
     - **IMPORTANT**: Do NOT apply a uniform 2.09x multiplier to all phases. The biomarker benefit varies by phase and is overwhelmingly concentrated in Phase II.
     - **Example calculation**: If baseline oncology Phase II→III is 24.6%, with validated biomarker it becomes 24.6% × 1.64 = 40.3%
     - **Cap at 100%**: Ensure no phase PoS exceeds 100% after adjustment (use min(adjusted_value, 100%))
   - **Apply other adjustments**: Check `adjustments_and_factors` for orphan drug, breakthrough designation, first-in-class, or validated target multipliers
   - **Search for specifics**: "phase [X] success rate [therapeutic area]", "clinical trial success rates [indication]", "FDA approval probability"
   - Look for: BIO/Biomedtracker reports, FDA statistics, recent industry analyses
   - Consider: have molecules with the same target already completed trials, or have molecules in the same general pathway completed trials
   - **CRITICAL**: PoS represents the probability of SUCCESSFULLY COMPLETING each phase. Research PoS for the CURRENT phase AND all future phases:
     - If current stage is "Phase I Ready", research Phase I, Phase II, Phase III, and Approval PoS
     - If current stage is "Phase II Ready", research Phase II, Phase III, and Approval PoS
     - If current stage is "Phase III Ready", research Phase III and Approval PoS
     - If current stage is "Registration Ready", research Approval PoS only
     - If current stage is "Approved", skip all PoS parameters (already 100% successful)
   - Reference baseline ranges (from BIO/QLS Advisors 2021, all indications 2011-2020):
     - Phase I→II: 52.0%
     - Phase II→III: 28.9% (varies widely: oncology ~24.6%, hematology ~48.1%)
     - Phase III→Approval: 57.8% (oncology ~47.7%, hematology ~76.8%)
     - Overall LOA from Phase I: 7.9% (oncology 5.3%, hematology 23.9%)
   - **Important**: Cumulative risk adjustment = product of current + all future phase PoS values
   - Express as: Percentage per phase
   - **Cite both sources**: Reference the baseline from reference data AND any indication-specific data from web search

### Step 5: Research Financial Parameters

14. **Cost of Goods Sold (COGS)**
   - Search: "[modality] manufacturing cost", "COGS as percent of revenue [therapeutic area]"
   - Focus on US market costs and suppliers
   - Typical ranges:
     - Small molecule: 10-20% of revenue
     - Antibody/biologic: 15-25% of revenue
     - Gene/cell therapy: 25-40% of revenue
   - Express as: Percentage of revenue (e.g., "20% COGS")

15. **Operating Expenses (OpEx)**
    - Search: "biotech SG&A expenses US", "pharma operating margin [therapeutic area] United States"
    - Includes: Sales & marketing, general & administrative
    - Typical: 30-50% of revenue (higher for commercial-stage, lower for rare disease/orphan)
    - Express as: Percentage of revenue (e.g., "40% OpEx")

16. **Tax Rate**
    - Search: "US corporate tax rate [current year]", "biotech effective tax rate United States"
    - US federal: 21%, consider state taxes (average 5-7%)
    - Typical effective rate: 25-30%
    - Express as: Percentage (e.g., "28% tax rate")

17. **Discount Rate (WACC)**
    - Search: "biotech WACC [current year] United States", "pharma weighted average cost of capital US"
    - Use a standard discount rate that does NOT account for development phase risk
    - Typical range: 8-12% (standard corporate WACC for US biotech/pharma)
    - Express as: Percentage (e.g., "10% WACC")

### Step 6: Format Output as Structured JSON

Once all research is complete, output the DCF parameters in this **exact** JSON format:

```json
{
  "assetOverview": {
    "assetName": "string",
    "therapeuticArea": "string",
    "mechanismOfAction": "string",
    "modality": "string",
    "currentDevelopmentStage": "Phase I Ready | Phase II Ready | Phase III Ready | Registration Ready | Approved",
    "biomarkerStatus": {
      "hasBiomarker": "boolean",
      "biomarkerType": "validated | exploratory | none | unknown",
      "biomarkerDescription": "string (e.g., 'HER2+ patient selection', 'PD-L1 expression ≥50%')",
      "phaseSpecificMultipliers": {
        "phase_1_to_2": "number - Use 1.01 (validated), ~1.01 (exploratory), or 1.0 (none/unknown)",
        "phase_2_to_3": "number - Use 1.64 (validated), 1.32-1.48 (exploratory), or 1.0 (none/unknown)",
        "phase_3_to_approval": "number - Use 1.19 (validated), 1.10-1.14 (exploratory), or 1.0 (none/unknown)"
      },
      "overallLOAImprovement": "number - Overall improvement factor: 2.09 (validated), ~1.5-1.8 (exploratory), or 1.0 (none/unknown)",
      "notes": "string - Explain biomarker strategy and phase-specific impact on PoS. Note that biomarker benefit is overwhelmingly concentrated in Phase II (1.64x), with meaningful Phase III benefit (1.19x) and negligible Phase I impact."
    }
  },
  "marketParameters": {
    "totalAddressableMarket": {
      "value": 0,
      "unit": "patients",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "peakMarketShare": {
      "value": 0,
      "unit": "%",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "yearsToPeakAdoption": {
      "value": 0,
      "unit": "years",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "annualPricing": {
      "value": 0,
      "unit": "USD per patient per year",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "lossOfExclusivity": {
      "value": 0,
      "unit": "years from approval",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "yearsToDeclinePostLOE": {
      "value": 0,
      "unit": "years",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "terminalMarketShare": {
      "value": 0,
      "unit": "%",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    }
  },
  "developmentTimeline": {
    "phaseIDuration": {
      "value": 0,
      "unit": "years",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "phaseIIDuration": {
      "value": 0,
      "unit": "years",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "phaseIIIDuration": {
      "value": 0,
      "unit": "years",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "approvalDuration": {
      "value": 0,
      "unit": "years",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    }
  },
  "clinicalTrialCosts": {
    "phaseI": {
      "value": 0,
      "unit": "USD millions",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "phaseII": {
      "value": 0,
      "unit": "USD millions",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "phaseIII": {
      "value": 0,
      "unit": "USD millions",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "approval": {
      "value": 0,
      "unit": "USD millions",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    }
  },
  "probabilityOfSuccess": {
    "phaseI": {
      "value": 0,
      "unit": "%",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "phaseII": {
      "value": 0,
      "unit": "%",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "phaseIII": {
      "value": 0,
      "unit": "%",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "approval": {
      "value": 0,
      "unit": "%",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "cumulativeRiskAdjustment": {
      "value": 0,
      "unit": "%",
      "calculation": "string (e.g., 'Phase II PoS × Phase III PoS × Approval PoS = 35% × 55% × 90% = 17.3%')"
    },
    "biomarkerAdjustmentApplied": {
      "applied": "boolean",
      "phaseSpecificMultipliers": {
        "phase_1_to_2": "number - Actual multiplier applied (1.01 for validated, ~1.01 for exploratory, 1.0 for none)",
        "phase_2_to_3": "number - Actual multiplier applied (1.64 for validated, 1.32-1.48 for exploratory, 1.0 for none)",
        "phase_3_to_approval": "number - Actual multiplier applied (1.19 for validated, 1.10-1.14 for exploratory, 1.0 for none)"
      },
      "notes": "string - Example: 'Validated HER2 biomarker - phase-specific multipliers applied: 1.01x (Phase I→II), 1.64x (Phase II→III), 1.19x (Phase III→Approval). Biomarker benefit concentrated in Phase II.'"
    },
    "referenceDataSource": {
      "baselineSource": "clinical_trial_reference_data.json",
      "therapeuticAreaUsed": "string (e.g., 'oncology', 'cns_neurology')",
      "indicationSpecificDataUsed": "string or null (e.g., 'breast_cancer', null if not available)"
    }
  },
  "financialParameters": {
    "costOfGoodsSold": {
      "value": 0,
      "unit": "% of revenue",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "operatingExpenses": {
      "value": 0,
      "unit": "% of revenue",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "taxRate": {
      "value": 0,
      "unit": "%",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    },
    "discountRate": {
      "value": 0,
      "unit": "%",
      "source": "string",
      "url": "string",
      "explanation": "string",
      "confidence": "High|Medium|Low"
    }
  },
  "metadata": {
    "generatedDate": "ISO 8601 date string",
    "currency": "USD",
     "notes": "All dollar values in USD and market scope is United States. Confidence levels: High (authoritative source from within 2 years), Medium (authoritative source 2-5 years old or recent indirect source), Low (estimated, extrapolated, or >5 years old). This research provides inputs for DCF modeling. Users should validate assumptions and adjust based on specific asset characteristics."
  }
}
```

**CRITICAL**: After generating the JSON, save it to a file in the `valuations/` directory with the format: `valuations/[asset-name]-[date].json`

Example filename: `valuations/pembrolizumab-nsclc-2026-01-12.json`

### Step 7: Guidance on Using the Output

After outputting the parameters, briefly explain:

1. **How to use these parameters**: "These parameters can be input into a DCF model to calculate NPV (Net Present Value) and IRR (Internal Rate of Return) for the asset."

2. **Key assumptions to review**: Highlight 2-3 parameters with Medium/Low confidence that users should scrutinize or refine.

3. **Sensitivity analysis suggestions**: Note which parameters typically have the highest impact on valuation (usually: pricing, market share, PoS, WACC).

### Step 8: Launch Visualization App

After saving the valuation file and providing guidance, automatically launch the interactive visualization web app:

1. **Launch the Python server**: Use the Bash tool to start the visualization server in the background:
   ```bash
   cd $(dirname $(find . -name "server.py" 2>/dev/null | head -1)) && python3 server.py 8000 &
   ```

2. **Inform the user**: Provide clear instructions on how to access the visualization:
   - The web app is now running at `http://localhost:8000`
   - The interface allows interactive DCF modeling with:
     - Automatic NPV/IRR calculations
     - Year-by-year cash flow projections
     - Interactive parameter adjustments
     - Visual charts and sensitivity analysis
   - To stop the server later, the user can use `Ctrl+C` or find and kill the process

3. **Important notes**:
   - The server runs in the background so the user can continue working
   - The app automatically loads all valuations from the `valuations/` directory
   - Changes made in the web interface can be saved back to the JSON files
   - The server uses only Python standard library (no dependencies required)

## Important Research Guidelines

- **Start with reference data**: Always load `clinical_trial_reference_data.json` first to get well-sourced baseline values for PoS and trial costs. The reference data includes sources from BIO/QLS Advisors (2011-2020) and ASPE/HHS.
- **Then search for specifics**: Web search should refine and update the baseline values with indication-specific, modality-specific, or more recent data.
- **Prioritize recent sources** (within last 2 years) for market data and pricing
- **Use authoritative sources**: FDA, EMA, WHO, CDC, patient advocacy groups, peer-reviewed journals, established pharma analytics firms (Evaluate Pharma, IQVIA, etc.)
- **CRITICAL - Specific URLs required**: Every source URL must link directly to the exact report, PDF, data page, or press release containing the cited data. Do NOT use homepage URLs or general site links. Use WebFetch to verify the URL contains the data before citing it.
- **Apply biomarker adjustments correctly**: If the asset has a validated biomarker strategy, apply phase-specific multipliers documented in the reference data (BIO/QLS Advisors 2021): 1.01x for Phase I→II, 1.64x for Phase II→III, 1.19x for Phase III→Approval. Do NOT apply a uniform 2.09x to all phases.
- **Be conservative with estimates**: When ranges exist, explain the rationale for your chosen value
- **Adjust for asset-specific factors**: Orphan drugs, first-in-class therapies, and breakthrough designations warrant different assumptions than crowded markets - see `adjustments_and_factors` in reference data
- **Show calculation work**: For derived values (like cumulative PoS), show the formula including any biomarker or other adjustments applied
- **If data is unavailable**: Clearly state "Data not found" and provide a reasoned estimate based on comparable assets, marking confidence as Low. Use reference data as fallback. If web search returns no relevant results for a specific parameter, state this explicitly and proceed with well-justified industry standards.

## Output Requirements

- **Format**: Use the exact structured JSON format shown above
- **File saving**: Save the JSON output to `valuations/[asset-name]-[date].json`
- **Completeness**: All 12 parameter categories must be researched and included
- **Citations**: Every parameter must have source, URL, explanation, and confidence
- **Clarity**: Write explanations in plain language accessible to non-experts
- **Professional tone**: This is a formal financial research output

## What NOT to Do

- Do not create new code for the web application (the visualization app already exists at server.py)
- Do not manually calculate NPV/IRR in the skill output (the web app does this automatically)
- Do not use placeholder values (e.g., "[insert value here]")
- Do not skip research steps—thorough web search is required for every parameter
- Do not combine parameters or skip any of the 12 categories
- Do not forget to launch the visualization server at the end (Step 8)

---

This skill is designed for Claude Code users who need rigorous, well-sourced DCF inputs for biotech valuation. The JSON output is automatically saved to the valuations/ directory and immediately accessible through the interactive web interface (launched automatically at Step 7). The visualization app provides:

- **Interactive DCF Modeling**: Real-time NPV/IRR calculations as you adjust parameters
- **Visual Analytics**: Charts showing revenue projections, cash flows, and sensitivity analysis
- **Parameter Tuning**: Edit any assumption and instantly see the valuation impact
- **Export Options**: Save updated valuations or export for use in Excel, Python, R, etc.
- **No Dependencies**: Pure Python standard library implementation

The web interface complements the research-driven JSON outputs, enabling stakeholders to explore scenarios and validate assumptions interactively.
