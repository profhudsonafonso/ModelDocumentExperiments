# Methodological analysis report — sf0.25

Phase analyzed: **cold**.

## 1. How to read this analysis

The analysis follows the framework logic:
1. prioritize performance on **primary queries**;
2. measure regression on **secondary affected** and **control** queries;
3. compare not only average latency, but also **p95**, because p95 represents the more critical tail behavior;
4. inspect which configuration variables are most associated with better or worse trade-offs.

## 2. Best candidates by family

### associative_family

- **watchitem_g4**: primary p95 - vs baseline, secondary p95 -, control p95 -, class = **Insufficient data**.
- **watchitem_g5**: primary p95 - vs baseline, secondary p95 -, control p95 -, class = **Insufficient data**.
- **watchitem_g6**: primary p95 - vs baseline, secondary p95 -, control p95 -, class = **Insufficient data**.

### containment_family

- **series_g7**: primary p95 +0.0% vs baseline, secondary p95 +0.0%, control p95 +0.0%, class = **Neutral candidate**.
- **series_g9**: primary p95 +416.5% vs baseline, secondary p95 -45.7%, control p95 -31.9%, class = **Neutral candidate**.
- **series_g8**: primary p95 +523.3% vs baseline, secondary p95 -43.5%, control p95 -25.2%, class = **Neutral candidate**.

### root_local_family

- **watchitem_g3**: primary p95 -13.5% vs baseline, secondary p95 -, control p95 -, class = **Mild favorable trade-off**.
- **watchitem_g2**: primary p95 -13.5% vs baseline, secondary p95 -, control p95 -73.5%, class = **Mild favorable trade-off**.
- **watchitem_g0**: primary p95 +0.0% vs baseline, secondary p95 -, control p95 +0.0%, class = **Neutral candidate**.

## 3. Strongest primary gains

- **watchitem_g3** (root_local_family): primary p95 -13.5%; secondary p95 -; control p95 -.
- **watchitem_g2** (root_local_family): primary p95 -13.5%; secondary p95 -; control p95 -73.5%.
- **watchitem_g0** (root_local_family): primary p95 +0.0%; secondary p95 -; control p95 +0.0%.
- **series_g7** (containment_family): primary p95 +0.0%; secondary p95 +0.0%; control p95 +0.0%.
- **series_g9** (containment_family): primary p95 +416.5%; secondary p95 -45.7%; control p95 -31.9%.

## 4. Configurations with larger regressions

- **series_g7** (containment_family): secondary p95 +0.0%; primary p95 +0.0%; control p95 +0.0%.
- **series_g8** (containment_family): secondary p95 -43.5%; primary p95 +523.3%; control p95 -25.2%.
- **series_g9** (containment_family): secondary p95 -45.7%; primary p95 +416.5%; control p95 -31.9%.
- **watchitem_g4** (associative_family): secondary p95 -; primary p95 -; control p95 -.
- **watchitem_g5** (associative_family): secondary p95 -; primary p95 -; control p95 -.

## 5. Configuration-variable impact

### activated_class

- **G3**: avg trade-off score 13.51, avg primary p95 -13.5%, avg secondary p95 -, avg control p95 -.
- **G2**: avg trade-off score 13.45, avg primary p95 -13.5%, avg secondary p95 -, avg control p95 -73.5%.
- **G0**: avg trade-off score 0.00, avg primary p95 +0.0%, avg secondary p95 -, avg control p95 +0.0%.

### benchmark_family

- **root_local_family**: avg trade-off score 8.99, avg primary p95 -9.0%, avg secondary p95 -, avg control p95 -36.7%.
- **containment_family**: avg trade-off score -313.28, avg primary p95 +313.3%, avg secondary p95 -29.7%, avg control p95 -19.0%.
- **associative_family**: avg trade-off score nan, avg primary p95 -, avg secondary p95 -, avg control p95 -.

### embedding_variant

- **structural_component**: avg trade-off score 13.51, avg primary p95 -13.5%, avg secondary p95 -, avg control p95 -.
- **shared_descriptor**: avg trade-off score 13.45, avg primary p95 -13.5%, avg secondary p95 -, avg control p95 -73.5%.
- **baseline_document**: avg trade-off score 0.00, avg primary p95 +0.0%, avg secondary p95 -, avg control p95 +0.0%.

### selected_root

- **WatchItem**: avg trade-off score 8.99, avg primary p95 -9.0%, avg secondary p95 -, avg control p95 -36.7%.
- **Series**: avg trade-off score -313.28, avg primary p95 +313.3%, avg secondary p95 -29.7%, avg control p95 -19.0%.

## 6. Optional query-methodology variable impact

### D_value

- **2**: avg query p95 delta vs query baseline -24.0%, median -50.5%, n = 24.
- **1**: avg query p95 delta vs query baseline +107.4%, median -2.0%, n = 32.
- **0**: avg query p95 delta vs query baseline -, median -, n = 24.

### Rc

- **4**: avg query p95 delta vs query baseline -39.5%, median -44.0%, n = 24.
- **2**: avg query p95 delta vs query baseline -2.6%, median +14.1%, n = 24.
- **1**: avg query p95 delta vs query baseline +469.9%, median +469.9%, n = 8.

### document_candidate_assessment

- **Document candidate with stronger trade-offs**: avg query p95 delta vs query baseline -19.8%, median -30.2%, n = 48.
- **Strong document candidate**: avg query p95 delta vs query baseline +469.9%, median +469.9%, n = 8.
- **Structurally neutral for document**: avg query p95 delta vs query baseline -, median -, n = 24.

### query_sharedness_class

- **High sharedness**: avg query p95 delta vs query baseline -19.8%, median -30.2%, n = 48.
- **Low sharedness**: avg query p95 delta vs query baseline +469.9%, median +469.9%, n = 8.
- **Not applicable**: avg query p95 delta vs query baseline -, median -, n = 24.

### query_type

- **select**: avg query p95 delta vs query baseline +36.6%, median -33.3%, n = 64.
- **insert**: avg query p95 delta vs query baseline +43.3%, median +43.3%, n = 8.
- **update**: avg query p95 delta vs query baseline -, median -, n = 8.

### query_volatility_class

- **Low volatility exposure**: avg query p95 delta vs query baseline -19.8%, median -30.2%, n = 72.
- **No volatility exposure**: avg query p95 delta vs query baseline +469.9%, median +469.9%, n = 8.

### selected_DeltaR_ratio

- **1.0**: avg query p95 delta vs query baseline +37.8%, median -27.4%, n = 56.

### selected_document_depth

- **2.0**: avg query p95 delta vs query baseline -24.0%, median -50.5%, n = 24.
- **1.0**: avg query p95 delta vs query baseline +107.4%, median -2.0%, n = 32.

### selected_structural_coverage

- **Full absorption**: avg query p95 delta vs query baseline +37.8%, median -27.4%, n = 56.
- **No structural traversal**: avg query p95 delta vs query baseline -, median -, n = 24.

## 7. Recommended reading of the sf results

A configuration should be considered strong when:
- it reduces **primary p95** substantially;
- it does not produce large regressions in **secondary affected** queries;
- control queries stay relatively stable;
- the result is coherent with the methodological variables (depth, structural absorption, volatility, sharedness).

A practical selection rule is:
- first rank by **primary p95 improvement**;
- then eliminate configurations with excessive secondary/control regression;
- finally compare the survivors by family and implementation complexity.
