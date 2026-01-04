#!/usr/bin/env python3
"""
Phase 6: Generate Academic Metrics Report

Produces comprehensive metrics and visualizations for academic evaluation:
- Training curves (loss vs steps)
- Validation curves
- Perplexity analysis
- Retrieval metrics (recall@k)
- Debate-level metrics
- Ablation study (base vs adapter)

Run from project root:
    python scripts/generate_academic_report.py
"""

import sys
import json
import math
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    domain: str = "education"
    output_dir: Path = PROJECT_ROOT / "runs" / "reports"
    train_runs_dir: Path = PROJECT_ROOT / "runs" / "train"
    eval_runs_dir: Path = PROJECT_ROOT / "runs" / "eval"
    debates_dir: Path = PROJECT_ROOT / "runs" / "debates"


def load_training_report(config: ReportConfig) -> dict | None:
    """Load the most recent training report."""
    domain_dir = config.train_runs_dir / config.domain

    if not domain_dir.exists():
        print(f"No training runs found at {domain_dir}")
        return None

    # Find most recent run
    runs = sorted(domain_dir.iterdir(), reverse=True)
    if not runs:
        return None

    report_path = runs[0] / "training_report.json"
    if report_path.exists():
        with open(report_path) as f:
            return json.load(f)
    return None


def load_evaluation_report(config: ReportConfig) -> dict | None:
    """Load the most recent evaluation report."""
    domain_dir = config.eval_runs_dir / config.domain

    if not domain_dir.exists():
        print(f"No evaluation runs found at {domain_dir}")
        return None

    runs = sorted(domain_dir.iterdir(), reverse=True)
    if not runs:
        return None

    report_path = runs[0] / "evaluation_report.json"
    if report_path.exists():
        with open(report_path) as f:
            return json.load(f)
    return None


def load_debate_results(config: ReportConfig) -> list[dict]:
    """Load all debate results."""
    if not config.debates_dir.exists():
        return []

    results = []
    for debate_dir in sorted(config.debates_dir.iterdir()):
        data_path = debate_dir / "debate_data.json"
        if data_path.exists():
            with open(data_path) as f:
                results.append(json.load(f))
    return results


def plot_training_curves(training_report: dict, output_dir: Path):
    """Generate training and validation loss curves."""
    history = training_report.get("training_history", {})

    steps = history.get("steps", [])
    train_loss = history.get("training_loss", [])
    val_loss = history.get("validation_loss", [])
    lr = history.get("learning_rate", [])

    if not steps or not train_loss:
        print("No training history available for plotting")
        return None

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Loss curve
    ax1 = axes[0]
    ax1.plot(steps, train_loss, 'b-', label='Training Loss', linewidth=2)
    if val_loss:
        # Validation is logged less frequently
        val_steps = np.linspace(steps[0], steps[-1], len(val_loss))
        ax1.plot(val_steps, val_loss, 'r-', label='Validation Loss', linewidth=2)
    ax1.set_xlabel('Training Steps')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training and Validation Loss')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Perplexity curve
    ax2 = axes[1]
    train_ppl = [math.exp(l) for l in train_loss]
    ax2.plot(steps, train_ppl, 'b-', label='Training PPL', linewidth=2)
    if val_loss:
        val_ppl = [math.exp(l) for l in val_loss]
        ax2.plot(val_steps, val_ppl, 'r-', label='Validation PPL', linewidth=2)
    ax2.set_xlabel('Training Steps')
    ax2.set_ylabel('Perplexity')
    ax2.set_title('Training and Validation Perplexity')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = output_dir / "training_curves.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()

    return plot_path


def plot_model_comparison(eval_report: dict, output_dir: Path):
    """Generate base vs adapter comparison chart."""
    if not eval_report or "results" not in eval_report:
        return None

    base = eval_report["results"]["base_model"]
    adapter = eval_report["results"]["adapter_model"]

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    # Loss comparison
    ax1 = axes[0]
    models = ['Base Model', 'Base + Adapter']
    losses = [base["test_loss"], adapter["test_loss"]]
    colors = ['#ff7f0e', '#2ca02c']
    bars = ax1.bar(models, losses, color=colors)
    ax1.set_ylabel('Test Loss')
    ax1.set_title('Test Loss Comparison')
    ax1.bar_label(bars, fmt='%.3f')

    # Perplexity comparison
    ax2 = axes[1]
    ppls = [base["test_perplexity"], adapter["test_perplexity"]]
    bars = ax2.bar(models, ppls, color=colors)
    ax2.set_ylabel('Test Perplexity')
    ax2.set_title('Test Perplexity Comparison')
    ax2.bar_label(bars, fmt='%.2f')

    plt.tight_layout()
    plot_path = output_dir / "model_comparison.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()

    return plot_path


def plot_debate_metrics(debate_results: list[dict], output_dir: Path):
    """Generate debate-level metrics visualization."""
    if not debate_results:
        return None

    # Extract metrics
    pro_scores = []
    con_scores = []
    faithfulness_scores = []
    winners = {"pro": 0, "con": 0, "tie": 0}

    for result in debate_results:
        if result.get("judge_score"):
            js = result["judge_score"]
            pro_scores.append(js["pro_score"])
            con_scores.append(js["con_score"])
            winners[js["winner"]] += 1

        if result.get("metrics", {}).get("fact_check"):
            faithfulness_scores.append(
                result["metrics"]["fact_check"]["avg_faithfulness"]
            )

    if not pro_scores:
        return None

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    # Score distribution
    ax1 = axes[0]
    x = np.arange(len(pro_scores))
    width = 0.35
    ax1.bar(x - width/2, pro_scores, width, label='Pro', color='#2ca02c')
    ax1.bar(x + width/2, con_scores, width, label='Con', color='#d62728')
    ax1.set_xlabel('Debate')
    ax1.set_ylabel('Score')
    ax1.set_title('Debate Scores')
    ax1.legend()
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'D{i+1}' for i in x])

    # Win rate pie chart
    ax2 = axes[1]
    win_labels = []
    win_sizes = []
    win_colors = []
    color_map = {'pro': '#2ca02c', 'con': '#d62728', 'tie': '#7f7f7f'}
    for side, count in winners.items():
        if count > 0:
            win_labels.append(f'{side.upper()} ({count})')
            win_sizes.append(count)
            win_colors.append(color_map[side])
    if win_sizes:
        ax2.pie(win_sizes, labels=win_labels, colors=win_colors, autopct='%1.1f%%')
        ax2.set_title('Win Rate Distribution')

    # Faithfulness histogram
    ax3 = axes[2]
    if faithfulness_scores:
        ax3.hist(faithfulness_scores, bins=10, color='#1f77b4', edgecolor='black')
        ax3.axvline(np.mean(faithfulness_scores), color='red', linestyle='--',
                   label=f'Mean: {np.mean(faithfulness_scores):.3f}')
        ax3.set_xlabel('Faithfulness Score')
        ax3.set_ylabel('Count')
        ax3.set_title('Faithfulness Distribution')
        ax3.legend()

    plt.tight_layout()
    plot_path = output_dir / "debate_metrics.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()

    return plot_path


def generate_latex_table(training_report: dict, eval_report: dict) -> str:
    """Generate LaTeX table for academic paper."""
    lines = []
    lines.append(r"\begin{table}[h]")
    lines.append(r"\centering")
    lines.append(r"\caption{Model Performance Comparison}")
    lines.append(r"\begin{tabular}{lcc}")
    lines.append(r"\toprule")
    lines.append(r"Metric & Base Model & Base + Adapter \\")
    lines.append(r"\midrule")

    if eval_report and "results" in eval_report:
        base = eval_report["results"]["base_model"]
        adapter = eval_report["results"]["adapter_model"]

        lines.append(f"Test Loss & {base['test_loss']:.4f} & {adapter['test_loss']:.4f} \\\\")
        lines.append(f"Test Perplexity & {base['test_perplexity']:.2f} & {adapter['test_perplexity']:.2f} \\\\")

        improvement = eval_report["results"]["improvement"]
        lines.append(f"Loss Reduction & - & {improvement['loss_reduction_pct']:.1f}\\% \\\\")

    if training_report:
        final = training_report.get("final_metrics", {})
        lines.append(f"Training Loss & - & {final.get('train_loss', 0):.4f} \\\\")
        lines.append(f"Validation Loss & - & {final.get('val_loss', 0):.4f} \\\\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    return "\n".join(lines)


def generate_markdown_report(
    config: ReportConfig,
    training_report: dict | None,
    eval_report: dict | None,
    debate_results: list[dict],
    plot_paths: dict[str, Path],
) -> str:
    """Generate comprehensive Markdown report."""
    lines = []
    lines.append("# Debate Simulator: Academic Evaluation Report")
    lines.append(f"\nGenerated: {datetime.now().isoformat()}")
    lines.append(f"\nDomain: {config.domain}")

    # Executive Summary
    lines.append("\n## Executive Summary")
    if eval_report and "results" in eval_report:
        improvement = eval_report["results"]["improvement"]
        lines.append(f"\n- **Loss Reduction**: {improvement['loss_reduction_pct']:.1f}%")
        lines.append(f"- **Perplexity Reduction**: {improvement['perplexity_reduction']:.2f}")

    # Training Results
    lines.append("\n## 1. Training Results")
    if training_report:
        cfg = training_report.get("config", {})
        final = training_report.get("final_metrics", {})

        lines.append("\n### Configuration")
        lines.append(f"- LoRA rank (r): {cfg.get('lora_r', 'N/A')}")
        lines.append(f"- LoRA alpha: {cfg.get('lora_alpha', 'N/A')}")
        lines.append(f"- Target modules: {cfg.get('target_modules', 'N/A')}")
        lines.append(f"- Learning rate: {cfg.get('learning_rate', 'N/A')}")
        lines.append(f"- Epochs: {cfg.get('num_epochs', 'N/A')}")

        lines.append("\n### Final Metrics")
        lines.append(f"- Training Loss: {final.get('train_loss', 'N/A'):.4f}")
        lines.append(f"- Training Perplexity: {final.get('train_perplexity', 'N/A'):.2f}")
        lines.append(f"- Validation Loss: {final.get('val_loss', 'N/A'):.4f}")
        lines.append(f"- Validation Perplexity: {final.get('val_perplexity', 'N/A'):.2f}")

        if "training_curves" in plot_paths:
            lines.append(f"\n![Training Curves]({plot_paths['training_curves'].name})")

    # Evaluation Results
    lines.append("\n## 2. Evaluation Results (Ablation)")
    if eval_report and "results" in eval_report:
        base = eval_report["results"]["base_model"]
        adapter = eval_report["results"]["adapter_model"]

        lines.append("\n| Model | Test Loss | Test Perplexity |")
        lines.append("|-------|-----------|-----------------|")
        lines.append(f"| Base | {base['test_loss']:.4f} | {base['test_perplexity']:.2f} |")
        lines.append(f"| Base + Adapter | {adapter['test_loss']:.4f} | {adapter['test_perplexity']:.2f} |")

        if "model_comparison" in plot_paths:
            lines.append(f"\n![Model Comparison]({plot_paths['model_comparison'].name})")

    # Debate Results
    lines.append("\n## 3. Multi-Agent Debate Results")
    if debate_results:
        lines.append(f"\nTotal debates analyzed: {len(debate_results)}")

        # Aggregate metrics
        pro_wins = sum(1 for d in debate_results if d.get("judge_score", {}).get("winner") == "pro")
        con_wins = sum(1 for d in debate_results if d.get("judge_score", {}).get("winner") == "con")
        ties = sum(1 for d in debate_results if d.get("judge_score", {}).get("winner") == "tie")

        lines.append("\n### Win Rates")
        lines.append(f"- Pro: {pro_wins}/{len(debate_results)} ({100*pro_wins/len(debate_results):.1f}%)")
        lines.append(f"- Con: {con_wins}/{len(debate_results)} ({100*con_wins/len(debate_results):.1f}%)")
        lines.append(f"- Tie: {ties}/{len(debate_results)} ({100*ties/len(debate_results):.1f}%)")

        # Faithfulness
        faithfulness_scores = [
            d["metrics"]["fact_check"]["avg_faithfulness"]
            for d in debate_results
            if d.get("metrics", {}).get("fact_check")
        ]
        if faithfulness_scores:
            lines.append(f"\n### Faithfulness (Fact-Check)")
            lines.append(f"- Mean: {np.mean(faithfulness_scores):.3f}")
            lines.append(f"- Std: {np.std(faithfulness_scores):.3f}")
            lines.append(f"- Min: {min(faithfulness_scores):.3f}")
            lines.append(f"- Max: {max(faithfulness_scores):.3f}")

        if "debate_metrics" in plot_paths:
            lines.append(f"\n![Debate Metrics]({plot_paths['debate_metrics'].name})")

    # System Architecture
    lines.append("\n## 4. System Architecture")
    lines.append("""
The multi-agent debate system consists of:

1. **DomainRouterAgent**: Classifies topics → selects domain adapter
2. **ResearchAgent**: Retrieves passages via BM25 from local corpus
3. **DebaterAgent (Pro/Con)**: Generates arguments using LLM + adapter
4. **FactCheckAgent**: Verifies claims against retrieved context
5. **JudgeAgent**: Scores arguments and determines winner
6. **LoggerAgent**: Saves all artifacts and metrics

The pipeline uses a state machine architecture for reproducible execution.
""")

    # Reproducibility
    lines.append("\n## 5. Reproducibility")
    lines.append("""
All experiments are fully reproducible:
- Fixed random seed: 42
- Deterministic data splits (80/10/10)
- All artifacts saved locally
- No external API calls for inference
""")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("PHASE 6: Academic Metrics Report Generation")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    config = ReportConfig()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print("\n--- Loading Data ---")
    training_report = load_training_report(config)
    print(f"Training report: {'Loaded' if training_report else 'Not found'}")

    eval_report = load_evaluation_report(config)
    print(f"Evaluation report: {'Loaded' if eval_report else 'Not found'}")

    debate_results = load_debate_results(config)
    print(f"Debate results: {len(debate_results)} debates found")

    # Generate plots
    print("\n--- Generating Plots ---")
    plot_paths = {}

    if training_report:
        path = plot_training_curves(training_report, config.output_dir)
        if path:
            plot_paths["training_curves"] = path
            print(f"  ✓ Training curves: {path}")

    if eval_report:
        path = plot_model_comparison(eval_report, config.output_dir)
        if path:
            plot_paths["model_comparison"] = path
            print(f"  ✓ Model comparison: {path}")

    if debate_results:
        path = plot_debate_metrics(debate_results, config.output_dir)
        if path:
            plot_paths["debate_metrics"] = path
            print(f"  ✓ Debate metrics: {path}")

    # Generate Markdown report
    print("\n--- Generating Reports ---")
    md_report = generate_markdown_report(
        config, training_report, eval_report, debate_results, plot_paths
    )

    md_path = config.output_dir / "academic_report.md"
    with open(md_path, 'w') as f:
        f.write(md_report)
    print(f"  ✓ Markdown report: {md_path}")

    # Generate LaTeX table
    if training_report or eval_report:
        latex_table = generate_latex_table(training_report, eval_report)
        latex_path = config.output_dir / "results_table.tex"
        with open(latex_path, 'w') as f:
            f.write(latex_table)
        print(f"  ✓ LaTeX table: {latex_path}")

    # Save aggregated metrics JSON
    aggregated_metrics = {
        "timestamp": datetime.now().isoformat(),
        "domain": config.domain,
        "training": training_report.get("final_metrics") if training_report else None,
        "evaluation": eval_report.get("results") if eval_report else None,
        "debates": {
            "count": len(debate_results),
            "pro_wins": sum(1 for d in debate_results if d.get("judge_score", {}).get("winner") == "pro"),
            "con_wins": sum(1 for d in debate_results if d.get("judge_score", {}).get("winner") == "con"),
        } if debate_results else None,
    }

    metrics_path = config.output_dir / "aggregated_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(aggregated_metrics, f, indent=2)
    print(f"  ✓ Aggregated metrics: {metrics_path}")

    # Summary
    print("\n" + "=" * 60)
    print("REPORT GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nAll outputs saved to: {config.output_dir}")
    print("\nGenerated artifacts:")
    for name, path in plot_paths.items():
        print(f"  - {name}: {path.name}")
    print(f"  - academic_report.md")
    print(f"  - aggregated_metrics.json")
    if training_report or eval_report:
        print(f"  - results_table.tex")

    print("\n✓ Phase 6 complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
