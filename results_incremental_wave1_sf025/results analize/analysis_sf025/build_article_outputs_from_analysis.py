#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd


def pct_fmt(x):
    if pd.isna(x):
        return "-"
    return f"{float(x):+.1f}\\%"

def score_fmt(x):
    if pd.isna(x):
        return "-"
    return f"{float(x):.2f}"

def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

def top_configs_by_family(exp_df: pd.DataFrame, n_top: int = 2) -> pd.DataFrame:
    rows = []
    for fam, fam_df in exp_df.groupby("benchmark_family"):
        fam_sorted = fam_df.sort_values(
            ["tradeoff_score", "primary_p95_pct_vs_baseline"],
            ascending=[False, True]
        ).head(n_top)
        rows.append(fam_sorted)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)

def build_article_table(top_df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "benchmark_family",
        "config_name",
        "activated_class",
        "selected_root",
        "proposed_embedding_depth",
        "embedding_variant",
        "primary_p95_pct_vs_baseline",
        "secondary_p95_pct_vs_baseline",
        "control_p95_pct_vs_baseline",
        "tradeoff_score",
        "tradeoff_class",
    ]
    cols = [c for c in cols if c in top_df.columns]
    out = top_df[cols].copy()
    return out

def dataframe_to_latex_table(df: pd.DataFrame, caption: str, label: str) -> str:
    if df.empty:
        return "% Empty table"

    latex_df = df.copy()
    for col in ["primary_p95_pct_vs_baseline", "secondary_p95_pct_vs_baseline", "control_p95_pct_vs_baseline"]:
        if col in latex_df.columns:
            latex_df[col] = latex_df[col].apply(pct_fmt)
    if "tradeoff_score" in latex_df.columns:
        latex_df["tradeoff_score"] = latex_df["tradeoff_score"].apply(score_fmt)

    rename_map = {
        "benchmark_family": "Family",
        "config_name": "Config",
        "activated_class": "Class",
        "selected_root": "Root",
        "proposed_embedding_depth": "Depth",
        "embedding_variant": "Variant",
        "primary_p95_pct_vs_baseline": "Primary $\\Delta p95$",
        "secondary_p95_pct_vs_baseline": "Secondary $\\Delta p95$",
        "control_p95_pct_vs_baseline": "Control $\\Delta p95$",
        "tradeoff_score": "Trade-off",
        "tradeoff_class": "Interpretation",
    }
    latex_df = latex_df.rename(columns={k: v for k, v in rename_map.items() if k in latex_df.columns})

    col_fmt = "p{2.4cm} p{1.8cm} p{1.2cm} p{1.4cm} p{0.9cm} p{2.2cm} p{1.6cm} p{1.7cm} p{1.6cm} p{1.3cm} p{3.2cm}"
    lines: List[str] = []
    lines.append("\\begin{table*}[ht]")
    lines.append("\\centering")
    lines.append(f"\\caption{{{caption}}}")
    lines.append(f"\\label{{{label}}}")
    lines.append("\\scriptsize")
    lines.append("\\setlength{\\tabcolsep}{4pt}")
    lines.append(f"\\begin{{tabular}}{{{col_fmt}}}")
    lines.append("\\toprule")
    lines.append(" & ".join(latex_df.columns) + " \\\\")
    lines.append("\\midrule")
    for _, row in latex_df.iterrows():
        values = [str(v).replace("_", "\\_") for v in row.tolist()]
        lines.append(" & ".join(values) + " \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")
    return "\n".join(lines)

def build_overleaf_text(exp_df: pd.DataFrame, var_df: pd.DataFrame, scale_label: str) -> str:
    fam_top = top_configs_by_family(exp_df, n_top=1)

    lines: List[str] = []
    lines.append("\\subsection{Interpretation of the " + scale_label.replace("_", "\\_") + " results}")
    lines.append("")
    lines.append("Table~\\ref{tab:sf025_summary} summarizes the most relevant document configurations identified in the benchmark for this scale factor. ")
    lines.append("The interpretation follows the framework logic adopted in this study: configurations are assessed primarily by their effect on the latency of primary queries, and then by the regressions they induce on secondary affected queries and control queries. ")
    lines.append("For this reason, the main comparison criterion is not only average latency, but especially the variation in the 95th percentile latency (p95), since p95 captures the tail behavior of the workload and is more informative for performance-sensitive scenarios.")
    lines.append("")

    if not fam_top.empty:
        for _, r in fam_top.iterrows():
            fam = r.get("benchmark_family", "")
            cfg = r.get("config_name", "")
            prim = r.get("primary_p95_pct_vs_baseline")
            sec = r.get("secondary_p95_pct_vs_baseline")
            ctrl = r.get("control_p95_pct_vs_baseline")
            cls = r.get("tradeoff_class", "")
            lines.append(
                f"In the \\textit{{{fam.replace('_', '\\_')}}} family, the most favorable configuration according to the trade-off score was "
                f"\\texttt{{{cfg.replace('_', '\\_')}}}. This configuration produced a primary-query p95 variation of {pct_fmt(prim)}, "
                f"while the average variation in secondary affected queries was {pct_fmt(sec)} and the average variation in control queries was {pct_fmt(ctrl)}. "
                f"According to the automated classification, this result can be described as \\textit{{{cls}}}."
            )
            lines.append("")

    if not var_df.empty:
        lines.append("From the perspective of configuration variables, the results also suggest that performance is not determined by a single factor, but by the interaction between structural depth, embedding strategy, and benchmark family. ")
        best_rows = var_df.sort_values("avg_tradeoff_score", ascending=False).head(5)
        mentioned = set()
        for _, r in best_rows.iterrows():
            var = r["variable_name"]
            if var in mentioned:
                continue
            mentioned.add(var)
            val = r["variable_value"]
            score = r["avg_tradeoff_score"]
            prim = r["avg_primary_p95_pct_vs_baseline"]
            sec = r["avg_secondary_p95_pct_vs_baseline"]
            ctrl = r["avg_control_p95_pct_vs_baseline"]
            lines.append(
                f"For the variable \\texttt{{{str(var).replace('_', '\\_')}}}, the value "
                f"\\texttt{{{str(val).replace('_', '\\_')}}} was associated with an average trade-off score of {score_fmt(score)}, "
                f"with average primary p95 variation {pct_fmt(prim)}, average secondary p95 variation {pct_fmt(sec)}, "
                f"and average control p95 variation {pct_fmt(ctrl)}. "
                f"This does not by itself prove causality, but it helps explain which design choices tend to align with better overall trade-offs in this experimental setting."
            )
            lines.append("")

    lines.append("Overall, the " + scale_label.replace("_", "\\_") + " results should be interpreted as a trade-off study rather than as a simple ranking of absolute latencies. ")
    lines.append("A configuration is methodologically stronger when it improves primary queries while keeping secondary and control regressions bounded. ")
    lines.append("Therefore, the final selection for implementation or discussion should prioritize configurations that combine meaningful primary-query gains with acceptable stability in the rest of the workload.")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Build article-ready outputs from the methodology analysis.")
    parser.add_argument("--analysis-dir", required=True, help="Folder created by analyze_sf_results_methodology.py")
    parser.add_argument("--scale-label", required=True, help="Scale label, e.g. sf0.25")
    parser.add_argument("--outdir", required=True, help="Output folder for article assets")
    parser.add_argument("--top-per-family", type=int, default=2)
    args = parser.parse_args()

    analysis_dir = Path(args.analysis_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    exp_df = load_csv(analysis_dir / "experiment_tradeoff_summary.csv")
    var_df = load_csv(analysis_dir / "config_variable_impact.csv")

    top_df = top_configs_by_family(exp_df, n_top=args.top_per_family)
    article_table_df = build_article_table(top_df)
    article_table_df.to_csv(outdir / "article_summary_table.csv", index=False)

    latex_table = dataframe_to_latex_table(
        article_table_df,
        caption=f"Summary of the most relevant MongoDB configurations for {args.scale_label}.",
        label="tab:sf025_summary"
    )
    (outdir / "article_summary_table.tex").write_text(latex_table, encoding="utf-8")

    overleaf_text = build_overleaf_text(exp_df, var_df, args.scale_label)
    (outdir / "sf025_interpretation_overleaf_en.tex").write_text(overleaf_text, encoding="utf-8")

    print("Generated:")
    print("-", outdir / "article_summary_table.csv")
    print("-", outdir / "article_summary_table.tex")
    print("-", outdir / "sf025_interpretation_overleaf_en.tex")

if __name__ == "__main__":
    main()
