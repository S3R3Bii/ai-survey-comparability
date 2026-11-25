# Survey coverage and identification

## What each observation represents

Eurostat table `isoc_eb_ai` supplies weighted percentages of enterprises reporting that they use particular technologies. Filters specify the EU27, annual frequency, 2024 and 2025, percentage of enterprises (`PC_ENT`), economic activities `C10-S951_X_K`, and size groups `GE10`, `10-49`, `50-249` and `GE250`. The survey covers selected non-financial activities with at least ten persons employed. The all-enterprise estimate comes directly from the source. It includes the three size classes, so the four rows are not independent samples. These are repeated cross-sections rather than a panel tracking the same firms. [Survey metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/isoc_e_esms.htm) · [Official statistical table](https://doi.org/10.2908/ISOC_EB_AI)

The frozen response contains 84 reported cells. In 2024 the media-generation item was absent for all four size definitions. Its absence is structural. The query and data are versioned, including the original dimension ordering and labels. Retrieved November 25, 2026. SHA-256: `eb0f28c433d3f9ed1dc0639e19bc0acd82979491e09220f8e2400b2fee657371`. The source reports its update timestamp in the JSON. Eurostat flags a 2025 country-series break for the Netherlands. The EU result inherits composition and survey effects that a common list of items cannot remove. [Snapshot](data/eurostat.json) · [Query](fetch_data.py) · [Eurostat analysis and break note](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Use_of_artificial_intelligence_in_enterprises)

## The basket and the missing information

The comparable basket contains text mining, speech recognition, image recognition, machine learning for data analysis, workflow automation or decision support, and autonomous physical movement. Eurostat identifies two questionnaire changes. We exclude language generation from the common basket in both years because the 2025 version explicitly mentions programming code. We also exclude generation of pictures, video or audio, first asked about in 2025. An unchanged category name alone cannot establish identical response behavior. [Eurostat report, pp. 12–13](https://ec.europa.eu/eurostat/documents/7870049/23260410/KS-01-26-009-EN-N.pdf)

There are 128 possible combinations of yes answers to seven items in 2024 and 256 combinations to eight in 2025. An enterprise using none of the listed items has zero positive flags. Here this group is the complement of reported positive use and can include enterprises without a positive report. It is not reconstructed from a separate “no AI” series.

For each year and size group, assign nonnegative percentage mass to each pattern and require all masses to sum to 100. For every item require the total mass of patterns reporting it to fall within 0.005 percentage points of the published percentage. Apply the same constraint to the shares using at least one, at least two and at least three listed technologies. Minimize, then maximize, the mass reporting any of the six common items. The interval uses a closed rounding tolerance. Its endpoints refer to the rounding convention used here.

## Reading the endpoints

The lowest possible change subtracts the highest feasible 2024 common-item share from the lowest feasible 2025 share. Reverse the choices for the highest possible change. This permits the pattern of overlapping use to vary between years. Each size group is analyzed separately with that group's published percentages. No cross-size weighting or restrictions from unpublished respondent-level records are imposed.

Across all enterprises the annual bounds are **8.060% to 13.485%** in 2024 and **11.745% to 19.955%** in 2025. Increasing shares on individual questions can coexist with fewer distinct firms in the union if use becomes more concentrated in firms already using other tools. The lower endpoint illustrates that possibility. It is not an estimate that common-item use fell.

Removing the two multi-use counts is an information sensitivity check. For large firms the maximum common-item increase expands from 25.840 to 30.515 points. In the EU aggregate the two count margins do not tighten the range. Within the figures used here, the missing cross-tab has direct value. [Full and reduced-constraint results](results/changes.csv)

## Verification and limits

The optimizer uses SciPy HiGHS. Each endpoint saves one sparse feasible distribution and the coefficients of a dual bound. A separate standard-library checker decodes the JSON-stat table by enumerating its dimension coordinates, reconstructs every observation and constraint, checks nonnegativity and total mass, tests the dual inequality for every pattern, and shows the two objective values agree within 0.000002 percentage points. Different optimal distributions can yield identical endpoints. The saved distributions are possible response mixes, never actual respondent records. [Certificates](results/certificates.json) · [Independent check](verify.py)

These bounds quantify missing overlap in rounded survey estimates. They do not model sampling error, national nonresponse, changes in enterprise composition, question-order effects, or changes in how respondents understand AI. No causal attribution to the wording change follows. To update against the live API, run `python fetch_data.py`. It stops if upstream bytes have changed so that a revised series can be reviewed explicitly. [Design](DESIGN.md)
