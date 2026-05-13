# Judicata/Chrome Workflow for California Case-Citation Verification

> **Purpose:** This workflow helps a legal reviewer verify California case citations in a brief, memorandum, or draft by using Google Chrome to review the cited authority in Judicata and, when needed, official court or reporter sources. It is a quality-control workflow, not legal advice; final legal judgments should be made by a licensed attorney.

## Compliance boundaries

- Use only accounts, subscriptions, and documents that the reviewer is authorized to access. Do not bypass login, paywall, download, copy, or anti-automation controls.
- Treat client drafts, research history, and downloaded cases as confidential work product. Use a dedicated Chrome profile for the matter and avoid syncing confidential browser history to personal accounts.
- If the workflow is later automated, keep a human legal reviewer in the loop for every quotation, paraphrase, and holding assessment.
- California state-court citation format must be applied consistently. California Rules of Court, rule 1.200 permits either the California Style Manual or The Bluebook for filed California court documents, at the filing party's option, but the selected style should be used consistently.
- Confirm citability before relying on any California appellate decision. California Rules of Court, rule 8.1115 restricts citation to unpublished California Court of Appeal and superior court appellate-division opinions except for limited rule-based exceptions, and review-granted or depublished status must be checked before final filing.

## Reviewer setup in Google Chrome

1. Create a matter-specific Chrome profile named `Client-Matter Citation Check`.
2. Sign in to Judicata using the firm's authorized account and confirm access to California case-law materials.
3. Add Chrome bookmarks for:
   - Judicata search and history pages.
   - [California Rules of Court, rule 1.200](https://courts.ca.gov/cms/rules/index/one/rule1_200).
   - [California Rules of Court, rule 8.1115](https://courts.ca.gov/cms/rules/index/eight/rule8_1115).
   - The firm's California Style Manual or citation-style reference.
   - Any official court docket, slip-opinion, or reporter source used by the firm.
4. Configure Chrome downloads to ask where each file should be saved, then save case PDFs or printouts to the matter's secure research folder.
5. Open the draft document, the citation review log, and Judicata in separate windows or split-screen panes.

## Inputs and outputs

### Inputs

- Draft brief, memorandum, declaration, or research product.
- Citation review log from `templates/citation-review-log.csv`.
- Matter-specific citation-style instruction, if the court or supervising attorney requires a specific variant.
- Authorized Judicata access in Chrome.

### Outputs

- Completed citation review log.
- Marked-up draft with correction comments.
- Saved case authority files or permanent links, where permitted.
- Escalation list for attorney review.

## End-to-end verification workflow

### 1. Extract every case citation from the draft

For each citation, capture the following in the review log:

- Exact citation as written in the draft.
- Draft page, line, paragraph, or footnote location.
- Case name.
- Reporter volume, reporter abbreviation, first page, court, and year.
- Pinpoint page, footnote, section, or paragraph.
- Whether the citation supports a direct quotation, a paraphrase, a procedural statement, or a parenthetical.
- The proposition the citation is intended to support.

Flag immediately if the draft citation is missing a case name, reporter, year, court, or pinpoint needed to support a specific proposition.

### 2. Locate and authenticate the authority in Judicata

1. Search Judicata by the reporter citation first, not by party name, to reduce false matches.
2. Confirm that the retrieved case matches all of the following:
   - Case name.
   - Court.
   - Decision date or year.
   - Reporter volume and first page.
   - Parallel reporter citation, if used in the draft.
3. Record the Judicata URL, document identifier, or research-history reference in the log.
4. Check the case status, treatment, subsequent history, publication status, and whether the decision is review-granted, depublished, superseded, vacated, or otherwise restricted.
5. If Judicata shows an adverse treatment, publication issue, or ambiguous status, mark the item `Escalate` and add a short note describing the issue.

### 3. Verify California citability and citation form

For California state cases, confirm:

- The case is published or otherwise citable under the applicable California Rules of Court.
- Any unpublished, depublished, review-granted, transferred, or superseded decision is cited only if an exception applies and the required notation is included.
- The citation style is internally consistent with the selected California Style Manual or Bluebook approach allowed by rule 1.200.
- The citation includes the correct official reporter reference when required by the selected style.
- The pinpoint citation points to the page or other locator where the cited language or proposition actually appears.
- Subsequent history, review status, or explanatory parentheticals are included when needed to avoid misleading the court.

### 4. Verify pinpoint citations

1. Navigate to the pinpoint page or locator in Judicata.
2. Use Chrome's page/PDF search only as a starting point; manually read the surrounding paragraph, heading, and nearby footnotes.
3. Confirm that the pinpoint contains the quoted language or supports the stated proposition.
4. If the proposition is supported elsewhere, replace the pinpoint with the correct page or locator.
5. If the case supports the proposition only after reading multiple pages, cite the full range rather than a single page.
6. If the cited page merely describes the parties' arguments, facts, dicta, or procedural history rather than the court's holding, flag the citation for attorney review.

### 5. Verify quotations exactly

For every direct quote:

1. Copy the quoted sentence or clause from the draft into the log.
2. Compare it word-for-word against the Judicata text at the pinpoint.
3. Confirm spelling, punctuation, capitalization, ellipses, bracketed alterations, emphasis, and internal quotation marks.
4. Confirm that omitted language does not materially change the meaning.
5. Confirm that any added emphasis is identified and any original emphasis is preserved or noted according to the governing style.
6. Read at least the paragraph before and after the quoted material to ensure the quote is not misleading in context.
7. Mark the result as:
   - `Pass` if exact and contextually fair.
   - `Correction needed` if text, citation, or formatting must be changed.
   - `Escalate` if the quote appears accurate but its legal use is debatable.

### 6. Verify paraphrases and holdings

For every paraphrase or parenthetical:

1. Identify whether the draft is describing the holding, rule, reasoning, facts, procedural posture, standard of review, dicta, or a party's argument.
2. Read the cited passage and surrounding section in Judicata.
3. Check whether the draft overstates, understates, generalizes, or shifts the court's reasoning.
4. Confirm that the case's procedural posture and governing law match the proposition in the draft.
5. Confirm that later treatment has not narrowed, criticized, distinguished, or overruled the proposition.
6. Rewrite the paraphrase if it fails any of these tests:
   - It attributes a broad rule to a narrow holding.
   - It treats dicta or party argument as the court's holding.
   - It omits a material limitation, exception, or factual condition.
   - It cites a case applying a different statute, standard, or procedural posture without explanation.
   - It ignores negative or limiting subsequent history.

### 7. Resolve discrepancies

Use the following decision rules:

- **Typographical citation error:** Correct the citation and record the correction.
- **Wrong pinpoint, right case:** Update the pinpoint and record the verified page or locator.
- **Right quote, wrong case or page:** Replace the citation or add the correct supporting authority.
- **Quote inaccurate:** Correct the quotation, add brackets/ellipses if appropriate, or convert it to a fair paraphrase.
- **Paraphrase overstated:** Narrow the proposition and cite the precise holding.
- **Authority not citable or bad law:** Escalate to the supervising attorney and suggest substitute authority if found.
- **Judicata and another source conflict:** Preserve screenshots or PDFs if permitted, record both sources, and escalate before filing.

### 8. Final quality-control pass

Before the document is finalized:

1. Sort the review log by `Status` and resolve every `Correction needed` item.
2. Confirm every `Escalate` item has an attorney decision recorded.
3. Re-run a document search for `Cal.`, `Cal.App.`, `P.`, `U.S.`, `F.`, `WL`, `LEXIS`, `supra`, `id.`, and quotation marks to catch missed citations.
4. Confirm short-form citations, `supra`, and `id.` references point to the correct authority and pinpoint.
5. Confirm the table of authorities, if any, matches corrected citations.
6. Save the final review log with the same version number as the reviewed draft.

## Status labels for the review log

- `Not started` — extracted but not reviewed.
- `In progress` — located in Judicata but not fully checked.
- `Pass` — citation, pinpoint, quotation/paraphrase, citability, and style verified.
- `Correction needed` — reviewer found a fix that can be made without legal judgment.
- `Escalate` — attorney judgment required.
- `Resolved` — correction or attorney decision completed and incorporated.

## Recommended evidence to preserve

When firm policy and the database license permit preservation, keep:

- A PDF or printout of the cited page range.
- A screenshot showing the case name, citation, and treatment/status flag.
- A screenshot or saved page showing the pinpoint passage.
- Notes explaining any attorney decision on a disputed paraphrase, quote, or citability issue.

## Authoritative reference links

- [California Rules of Court, rule 1.200 — Format of citations](https://courts.ca.gov/cms/rules/index/one/rule1_200).
- [California Rules of Court, rule 8.1115 — Citation of opinions](https://courts.ca.gov/cms/rules/index/eight/rule8_1115).
- Firm copy or library access to the current California Style Manual.

## Reviewer cautions

- Do not rely on a single search-result snippet for a legal proposition.
- Do not assume a quotation is accurate because the citation is accurate.
- Do not assume a paraphrase is fair because the case contains similar words.
- Do not cite unpublished California opinions unless a rule-based exception applies and the attorney approves.
- Do not ignore negative treatment simply because the cited sentence still appears in the case.
- Do not make legal-strategy decisions; escalate them.
