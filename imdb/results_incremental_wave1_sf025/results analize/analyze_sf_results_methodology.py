#!/usr/bin/env python3
from __future__ import annotations

"""
Análise metodológica dos resultados do benchmark MongoDB para IMDb.

Objetivo
--------
Comparar os resultados do sf0.25 (ou outro sf) segundo a metodologia do framework:
1. ganho nas queries primárias;
2. custo nas queries secundárias afetadas e de controle;
3. estabilidade (avg / median / p95 / p99 / std);
4. impacto das variáveis principais da configuração;
5. impacto opcional das variáveis metodológicas por query
   (Rc, D, DeltaR, cobertura estrutural, volatilidade, sharedness etc).

Arquivos esperados
------------------
Obrigatórios:
- benchmark_aggregate_results.csv
- mongo_experiment_catalog.csv

Opcional, mas recomendado:
- document_variable_matrix.csv
  (ou export equivalente da matriz final de variáveis por query)

Saídas
------
O script gera:
- merged_experiment_results.csv
- experiment_tradeoff_summary.csv
- query_level_deltas_vs_baseline.csv
- config_variable_impact.csv
- optional_query_variable_impact.csv (se query matrix for fornecida)
- sf_analysis_report.md
"""

import argparse
import ast
import json
import math
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
import pandas as pd


# =========================================================
# Helpers
# =========================================================

def parse_listlike_cell(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    if isinstance(value, float) and math.isnan(value):
        return []
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            obj = json.loads(s)
            if isinstance(obj, list):
                return obj
        except Exception:
            pass
        try:
            obj = ast.literal_eval(s)
            if isinstance(obj, list):
                return obj
        except Exception:
            pass
        return [x.strip() for x in s.split(",") if x.strip()]
    return []


def safe_pct_change(new: float, base: float) -> Optional[float]:
    if base in [None, 0] or pd.isna(base) or pd.isna(new):
        return None
    return ((new - base) / base) * 100.0


def classify_tradeoff(row: pd.Series) -> str:
    prim = row.get("primary_p95_pct_vs_baseline")
    sec = row.get("secondary_p95_pct_vs_baseline")
    ctrl = row.get("control_p95_pct_vs_baseline")

    if pd.notna(prim) and prim <= -15:
        if (pd.isna(sec) or sec <= 10) and (pd.isna(ctrl) or ctrl <= 10):
            return "Strong favorable trade-off"
        if (pd.notna(sec) and sec > 20) or (pd.notna(ctrl) and ctrl > 20):
            return "Primary gain with relevant regression elsewhere"
        return "Primary gain with moderate trade-off"

    if pd.notna(prim) and prim < 0:
        if (pd.isna(sec) or sec <= 10) and (pd.isna(ctrl) or ctrl <= 10):
            return "Mild favorable trade-off"
        return "Small primary gain with trade-off"

    if pd.notna(prim) and prim >= 0:
        if (pd.notna(sec) and sec > 0) or (pd.notna(ctrl) and ctrl > 0):
            return "Weak candidate"
        return "Neutral candidate"

    return "Insufficient data"


def format_pct(x: Any) -> str:
    if x is None or pd.isna(x):
        return "-"
    return f"{float(x):+.1f}%"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# =========================================================
# Loading / preparation
# =========================================================

def load_catalog(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    list_cols = [
        "embedded_entities", "snapshot_entities", "referenced_entities",
        "changed_region_entities", "derived_from_queries",
        "primary_queries", "secondary_affected_queries", "control_queries"
    ]
    for col in list_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_listlike_cell)

    if "changed_region_entities" in df.columns and "n_changed_region_entities" not in df.columns:
        df["n_changed_region_entities"] = df["changed_region_entities"].apply(len)
    return df


def load_query_matrix(path: Optional[Path]) -> Optional[pd.DataFrame]:
    if path is None:
        return None
    df = pd.read_csv(path)
    for col in ["Qi_entities_touched"]:
        if col in df.columns:
            df[col] = df[col].apply(parse_listlike_cell)
    return df


def filter_scale_and_phase(agg_df: pd.DataFrame, scale_label: str, run_phase: Optional[str]) -> pd.DataFrame:
    df = agg_df.copy()
    df = df[df["scale_label"] == scale_label].copy()
    if run_phase is not None:
        df = df[df["run_phase"] == run_phase].copy()
    return df.reset_index(drop=True)


# =========================================================
# Core analysis
# =========================================================

def determine_baseline_config(benchmark_family: str) -> str:
    if benchmark_family == "containment_family":
        return "series_g7"
    return "watchitem_g0"


def build_merged_results(
    agg_df: pd.DataFrame,
    catalog_df: pd.DataFrame,
) -> pd.DataFrame:
    keep_cols = [
        "experiment_id", "config_name", "activated_class", "benchmark_family",
        "selected_root", "proposed_embedding_depth", "embedding_variant",
        "scale_label", "n_supporting_queries", "n_primary_queries",
        "n_secondary_affected_queries", "n_control_queries",
        "experiment_goal", "primary_queries", "secondary_affected_queries",
        "control_queries", "changed_region_entities"
    ]
    keep_cols = [c for c in keep_cols if c in catalog_df.columns]

    merged = agg_df.merge(
        catalog_df[keep_cols].drop_duplicates(subset=["experiment_id"]),
        on=["experiment_id", "config_name", "activated_class", "benchmark_family", "scale_label"],
        how="left",
    )

    if "benchmark_family" in merged.columns:
        merged["baseline_config_name"] = merged["benchmark_family"].apply(determine_baseline_config)
    else:
        merged["baseline_config_name"] = "watchitem_g0"

    return merged


def add_baseline_deltas(merged: pd.DataFrame) -> pd.DataFrame:
    df = merged.copy()

    baseline_ref = df[
        ["scale_label", "benchmark_family", "query_name", "query_group", "run_phase",
         "config_name", "avg_latency_ms", "median_latency_ms", "p95_latency_ms", "p99_latency_ms", "std_latency_ms"]
    ].copy()

    baseline_ref = baseline_ref.rename(columns={
        "config_name": "baseline_config_name_ref",
        "avg_latency_ms": "baseline_avg_latency_ms",
        "median_latency_ms": "baseline_median_latency_ms",
        "p95_latency_ms": "baseline_p95_latency_ms",
        "p99_latency_ms": "baseline_p99_latency_ms",
        "std_latency_ms": "baseline_std_latency_ms",
    })

    df = df.merge(
        baseline_ref,
        left_on=["scale_label", "benchmark_family", "query_name", "query_group", "run_phase", "baseline_config_name"],
        right_on=["scale_label", "benchmark_family", "query_name", "query_group", "run_phase", "baseline_config_name_ref"],
        how="left"
    )

    for metric in ["avg_latency_ms", "median_latency_ms", "p95_latency_ms", "p99_latency_ms", "std_latency_ms"]:
        df[f"{metric}_pct_vs_baseline"] = df.apply(
            lambda row: safe_pct_change(row[metric], row[f"baseline_{metric}"]),
            axis=1
        )

    return df


def summarize_by_experiment_and_group(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for exp_id, grp in df.groupby("experiment_id"):
        meta = grp.iloc[0].to_dict()

        row = {
            "experiment_id": exp_id,
            "config_name": meta.get("config_name"),
            "activated_class": meta.get("activated_class"),
            "benchmark_family": meta.get("benchmark_family"),
            "selected_root": meta.get("selected_root"),
            "proposed_embedding_depth": meta.get("proposed_embedding_depth"),
            "embedding_variant": meta.get("embedding_variant"),
            "baseline_config_name": meta.get("baseline_config_name"),
            "n_primary_queries": meta.get("n_primary_queries"),
            "n_secondary_affected_queries": meta.get("n_secondary_affected_queries"),
            "n_control_queries": meta.get("n_control_queries"),
        }

        for group_name, prefix in [
            ("primary", "primary"),
            ("secondary_affected", "secondary"),
            ("control", "control"),
        ]:
            g = grp[grp["query_group"] == group_name]

            row[f"{prefix}_n_rows"] = len(g)
            row[f"{prefix}_avg_latency_ms"] = g["avg_latency_ms"].mean() if not g.empty else np.nan
            row[f"{prefix}_median_latency_ms"] = g["median_latency_ms"].mean() if not g.empty else np.nan
            row[f"{prefix}_p95_latency_ms"] = g["p95_latency_ms"].mean() if not g.empty else np.nan
            row[f"{prefix}_p99_latency_ms"] = g["p99_latency_ms"].mean() if not g.empty else np.nan
            row[f"{prefix}_std_latency_ms"] = g["std_latency_ms"].mean() if not g.empty else np.nan

            row[f"{prefix}_avg_pct_vs_baseline"] = g["avg_latency_ms_pct_vs_baseline"].mean() if not g.empty else np.nan
            row[f"{prefix}_median_pct_vs_baseline"] = g["median_latency_ms_pct_vs_baseline"].mean() if not g.empty else np.nan
            row[f"{prefix}_p95_pct_vs_baseline"] = g["p95_latency_ms_pct_vs_baseline"].mean() if not g.empty else np.nan
            row[f"{prefix}_p99_pct_vs_baseline"] = g["p99_latency_ms_pct_vs_baseline"].mean() if not g.empty else np.nan

        primary_gain = -row["primary_p95_pct_vs_baseline"] if pd.notna(row["primary_p95_pct_vs_baseline"]) else np.nan
        secondary_penalty = max(row["secondary_p95_pct_vs_baseline"], 0) if pd.notna(row["secondary_p95_pct_vs_baseline"]) else 0
        control_penalty = max(row["control_p95_pct_vs_baseline"], 0) if pd.notna(row["control_p95_pct_vs_baseline"]) else 0

        if pd.notna(primary_gain):
            row["tradeoff_score"] = primary_gain - 0.6 * secondary_penalty - 0.4 * control_penalty
        else:
            row["tradeoff_score"] = np.nan

        row["tradeoff_class"] = classify_tradeoff(pd.Series(row))
        rows.append(row)

    out = pd.DataFrame(rows)
    out = out.sort_values(
        by=["benchmark_family", "tradeoff_score", "primary_p95_pct_vs_baseline"],
        ascending=[True, False, True]
    ).reset_index(drop=True)
    return out


def build_query_level_delta_table(df: pd.DataFrame, query_matrix_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    q = df.copy()

    if query_matrix_df is not None and "query_name" in query_matrix_df.columns:
        rename_map = {}
        if "selected_root" in query_matrix_df.columns:
            rename_map["selected_root"] = "selected_root_method"
        q = q.merge(query_matrix_df.rename(columns=rename_map), on="query_name", how="left")

    if "selected_root_method" in q.columns:
        q["query_baseline_config"] = np.where(q["selected_root_method"] == "Series", "series_g7", "watchitem_g0")
    elif "selected_root" in q.columns:
        q["query_baseline_config"] = np.where(q["selected_root"] == "Series", "series_g7", "watchitem_g0")
    else:
        q["query_baseline_config"] = "watchitem_g0"

    baseline_ref = q[
        ["query_name", "query_group", "run_phase", "config_name", "p95_latency_ms", "avg_latency_ms"]
    ].copy().rename(columns={
        "config_name": "query_baseline_config_ref",
        "p95_latency_ms": "query_baseline_p95_latency_ms",
        "avg_latency_ms": "query_baseline_avg_latency_ms",
    })

    q = q.merge(
        baseline_ref,
        left_on=["query_name", "query_group", "run_phase", "query_baseline_config"],
        right_on=["query_name", "query_group", "run_phase", "query_baseline_config_ref"],
        how="left"
    )

    q["query_p95_pct_vs_query_baseline"] = q.apply(
        lambda row: safe_pct_change(row["p95_latency_ms"], row["query_baseline_p95_latency_ms"]),
        axis=1
    )
    q["query_avg_pct_vs_query_baseline"] = q.apply(
        lambda row: safe_pct_change(row["avg_latency_ms"], row["query_baseline_avg_latency_ms"]),
        axis=1
    )

    return q


def summarize_config_variable_impact(experiment_summary_df: pd.DataFrame) -> pd.DataFrame:
    candidate_vars = [
        "benchmark_family",
        "selected_root",
        "proposed_embedding_depth",
        "embedding_variant",
        "activated_class",
    ]
    candidate_vars = [c for c in candidate_vars if c in experiment_summary_df.columns]

    rows = []
    for var in candidate_vars:
        for value, grp in experiment_summary_df.groupby(var):
            rows.append({
                "variable_name": var,
                "variable_value": value,
                "n_experiments": len(grp),
                "avg_primary_p95_pct_vs_baseline": grp["primary_p95_pct_vs_baseline"].mean(),
                "avg_secondary_p95_pct_vs_baseline": grp["secondary_p95_pct_vs_baseline"].mean(),
                "avg_control_p95_pct_vs_baseline": grp["control_p95_pct_vs_baseline"].mean(),
                "avg_tradeoff_score": grp["tradeoff_score"].mean(),
                "best_tradeoff_score": grp["tradeoff_score"].max(),
            })

    out = pd.DataFrame(rows).sort_values(
        ["variable_name", "avg_tradeoff_score"],
        ascending=[True, False]
    ).reset_index(drop=True)
    return out


def summarize_query_variable_impact(query_delta_df: pd.DataFrame) -> pd.DataFrame:
    candidate_vars = [
        "Rc",
        "D_value",
        "selected_document_depth",
        "selected_DeltaR_ratio",
        "selected_structural_coverage",
        "query_volatility_class",
        "query_sharedness_class",
        "document_candidate_assessment",
        "query_type",
    ]
    candidate_vars = [c for c in candidate_vars if c in query_delta_df.columns]

    rows = []
    for var in candidate_vars:
        tmp = query_delta_df[query_delta_df["config_name"] != query_delta_df["query_baseline_config"]].copy()
        if tmp.empty:
            continue

        for value, grp in tmp.groupby(var):
            rows.append({
                "variable_name": var,
                "variable_value": value,
                "n_rows": len(grp),
                "avg_query_p95_pct_vs_query_baseline": grp["query_p95_pct_vs_query_baseline"].mean(),
                "median_query_p95_pct_vs_query_baseline": grp["query_p95_pct_vs_query_baseline"].median(),
                "avg_query_avg_pct_vs_query_baseline": grp["query_avg_pct_vs_query_baseline"].mean(),
            })

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows).sort_values(
        ["variable_name", "avg_query_p95_pct_vs_query_baseline"],
        ascending=[True, True]
    ).reset_index(drop=True)
    return out


# =========================================================
# Markdown report
# =========================================================

def build_markdown_report(
    scale_label: str,
    run_phase: Optional[str],
    experiment_summary_df: pd.DataFrame,
    variable_impact_df: pd.DataFrame,
    query_variable_impact_df: Optional[pd.DataFrame],
) -> str:
    phase_txt = run_phase if run_phase is not None else "all phases"

    lines: List[str] = []
    lines.append(f"# Methodological analysis report — {scale_label}")
    lines.append("")
    lines.append(f"Phase analyzed: **{phase_txt}**.")
    lines.append("")
    lines.append("## 1. How to read this analysis")
    lines.append("")
    lines.append("The analysis follows the framework logic:")
    lines.append("1. prioritize performance on **primary queries**;")
    lines.append("2. measure regression on **secondary affected** and **control** queries;")
    lines.append("3. compare not only average latency, but also **p95**, because p95 represents the more critical tail behavior;")
    lines.append("4. inspect which configuration variables are most associated with better or worse trade-offs.")
    lines.append("")

    lines.append("## 2. Best candidates by family")
    lines.append("")
    if experiment_summary_df.empty:
        lines.append("No experiment summary rows available.")
    else:
        for fam, fam_df in experiment_summary_df.groupby("benchmark_family"):
            fam_top = fam_df.sort_values("tradeoff_score", ascending=False).head(3)
            lines.append(f"### {fam}")
            lines.append("")
            for _, r in fam_top.iterrows():
                lines.append(
                    f"- **{r['config_name']}**: "
                    f"primary p95 {format_pct(r['primary_p95_pct_vs_baseline'])} vs baseline, "
                    f"secondary p95 {format_pct(r['secondary_p95_pct_vs_baseline'])}, "
                    f"control p95 {format_pct(r['control_p95_pct_vs_baseline'])}, "
                    f"class = **{r['tradeoff_class']}**."
                )
            lines.append("")

    lines.append("## 3. Strongest primary gains")
    lines.append("")
    prim_best = experiment_summary_df.sort_values("primary_p95_pct_vs_baseline").head(5)
    for _, r in prim_best.iterrows():
        lines.append(
            f"- **{r['config_name']}** ({r['benchmark_family']}): "
            f"primary p95 {format_pct(r['primary_p95_pct_vs_baseline'])}; "
            f"secondary p95 {format_pct(r['secondary_p95_pct_vs_baseline'])}; "
            f"control p95 {format_pct(r['control_p95_pct_vs_baseline'])}."
        )
    lines.append("")

    lines.append("## 4. Configurations with larger regressions")
    lines.append("")
    reg = experiment_summary_df.sort_values("secondary_p95_pct_vs_baseline", ascending=False).head(5)
    for _, r in reg.iterrows():
        lines.append(
            f"- **{r['config_name']}** ({r['benchmark_family']}): "
            f"secondary p95 {format_pct(r['secondary_p95_pct_vs_baseline'])}; "
            f"primary p95 {format_pct(r['primary_p95_pct_vs_baseline'])}; "
            f"control p95 {format_pct(r['control_p95_pct_vs_baseline'])}."
        )
    lines.append("")

    lines.append("## 5. Configuration-variable impact")
    lines.append("")
    if variable_impact_df.empty:
        lines.append("No configuration-variable impact table was generated.")
    else:
        for var, var_df in variable_impact_df.groupby("variable_name"):
            top = var_df.sort_values("avg_tradeoff_score", ascending=False).head(3)
            lines.append(f"### {var}")
            lines.append("")
            for _, r in top.iterrows():
                lines.append(
                    f"- **{r['variable_value']}**: "
                    f"avg trade-off score {r['avg_tradeoff_score']:.2f}, "
                    f"avg primary p95 {format_pct(r['avg_primary_p95_pct_vs_baseline'])}, "
                    f"avg secondary p95 {format_pct(r['avg_secondary_p95_pct_vs_baseline'])}, "
                    f"avg control p95 {format_pct(r['avg_control_p95_pct_vs_baseline'])}."
                )
            lines.append("")

    lines.append("## 6. Optional query-methodology variable impact")
    lines.append("")
    if query_variable_impact_df is None or query_variable_impact_df.empty:
        lines.append(
            "This section was skipped because no query-level methodology matrix "
            "(for example `document_variable_matrix.csv`) was supplied."
        )
    else:
        for var, var_df in query_variable_impact_df.groupby("variable_name"):
            top = var_df.sort_values("avg_query_p95_pct_vs_query_baseline").head(3)
            lines.append(f"### {var}")
            lines.append("")
            for _, r in top.iterrows():
                lines.append(
                    f"- **{r['variable_value']}**: "
                    f"avg query p95 delta vs query baseline {format_pct(r['avg_query_p95_pct_vs_query_baseline'])}, "
                    f"median {format_pct(r['median_query_p95_pct_vs_query_baseline'])}, "
                    f"n = {int(r['n_rows'])}."
                )
            lines.append("")

    lines.append("## 7. Recommended reading of the sf results")
    lines.append("")
    lines.append("A configuration should be considered strong when:")
    lines.append("- it reduces **primary p95** substantially;")
    lines.append("- it does not produce large regressions in **secondary affected** queries;")
    lines.append("- control queries stay relatively stable;")
    lines.append("- the result is coherent with the methodological variables (depth, structural absorption, volatility, sharedness).")
    lines.append("")
    lines.append("A practical selection rule is:")
    lines.append("- first rank by **primary p95 improvement**;")
    lines.append("- then eliminate configurations with excessive secondary/control regression;")
    lines.append("- finally compare the survivors by family and implementation complexity.")
    lines.append("")

    return "\n".join(lines)


# =========================================================
# Main
# =========================================================

def main():
    parser = argparse.ArgumentParser(description="Analyze MongoDB benchmark results according to the framework methodology.")
    parser.add_argument("--agg", required=True, help="Path to benchmark_aggregate_results.csv")
    parser.add_argument("--catalog", required=True, help="Path to mongo_experiment_catalog.csv")
    parser.add_argument("--query-matrix", required=False, help="Optional path to document_variable_matrix.csv or equivalent")
    parser.add_argument("--scale-label", required=True, help="Scale label to analyze, e.g. sf0.25")
    parser.add_argument("--run-phase", required=False, default="cold", help="Phase to analyze: cold, hot, or empty for all")
    parser.add_argument("--outdir", required=True, help="Output folder")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    ensure_dir(outdir)

    run_phase = args.run_phase
    if run_phase is not None and str(run_phase).strip() == "":
        run_phase = None

    agg_df = pd.read_csv(args.agg)
    catalog_df = load_catalog(Path(args.catalog))
    query_matrix_df = load_query_matrix(Path(args.query_matrix)) if args.query_matrix else None

    filtered_agg = filter_scale_and_phase(agg_df, args.scale_label, run_phase)
    merged = build_merged_results(filtered_agg, catalog_df)
    merged = add_baseline_deltas(merged)

    experiment_summary_df = summarize_by_experiment_and_group(merged)
    variable_impact_df = summarize_config_variable_impact(experiment_summary_df)

    query_delta_df = build_query_level_delta_table(merged, query_matrix_df)
    query_variable_impact_df = summarize_query_variable_impact(query_delta_df) if query_matrix_df is not None else None

    merged.to_csv(outdir / "merged_experiment_results.csv", index=False)
    experiment_summary_df.to_csv(outdir / "experiment_tradeoff_summary.csv", index=False)
    query_delta_df.to_csv(outdir / "query_level_deltas_vs_baseline.csv", index=False)
    variable_impact_df.to_csv(outdir / "config_variable_impact.csv", index=False)
    if query_variable_impact_df is not None:
        query_variable_impact_df.to_csv(outdir / "optional_query_variable_impact.csv", index=False)

    report_md = build_markdown_report(
        scale_label=args.scale_label,
        run_phase=run_phase,
        experiment_summary_df=experiment_summary_df,
        variable_impact_df=variable_impact_df,
        query_variable_impact_df=query_variable_impact_df,
    )
    (outdir / "sf_analysis_report.md").write_text(report_md, encoding="utf-8")

    print("\n=== Analysis completed ===")
    print(f"Output folder: {outdir}")
    print("- merged_experiment_results.csv")
    print("- experiment_tradeoff_summary.csv")
    print("- query_level_deltas_vs_baseline.csv")
    print("- config_variable_impact.csv")
    if query_variable_impact_df is not None:
        print("- optional_query_variable_impact.csv")
    print("- sf_analysis_report.md")

    print("\nTop 5 configurations by trade-off score:")
    preview_cols = [
        "experiment_id", "config_name", "benchmark_family",
        "primary_p95_pct_vs_baseline", "secondary_p95_pct_vs_baseline",
        "control_p95_pct_vs_baseline", "tradeoff_score", "tradeoff_class"
    ]
    preview_cols = [c for c in preview_cols if c in experiment_summary_df.columns]
    print(experiment_summary_df[preview_cols].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
