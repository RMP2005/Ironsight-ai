import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    # ---------------------------------------------------------
    # 1. Setup Output Directory & Configuration
    # ---------------------------------------------------------
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Set plot aesthetic style
    sns.set_theme(style="whitegrid", palette="muted")
    
    # ---------------------------------------------------------
    # 2. Load Dataset (Read-only mode)
    # ---------------------------------------------------------
    data_path = "data/ai4i2020.csv"
    print("=" * 60)
    print(f"Loading dataset from: {data_path}")
    print("=" * 60)
    
    df = pd.read_csv(data_path)
    
    # ---------------------------------------------------------
    # 3. Print Dataset Summaries
    # ---------------------------------------------------------
    # Print Dataset Shape
    print(f"\n[1] Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Print Column Names
    print("\n[2] Column Names:")
    for idx, col in enumerate(df.columns, 1):
        print(f"  {idx:2d}. {col}")
        
    # Print Missing-Value Summary
    print("\n[3] Missing Values Summary:")
    missing_summary = df.isnull().sum()
    print(missing_summary.to_string())
    
    # Print Target Value Counts
    target_col = "Machine failure"
    print(f"\n[4] '{target_col}' Value Counts:")
    val_counts = df[target_col].value_counts()
    print(val_counts.to_string())
    percentages = df[target_col].value_counts(normalize=True) * 100
    print(f"\nFailure rate: {percentages.get(1, 0.0):.2f}% ({val_counts.get(1, 0)} failures out of {len(df)} total)")

    # ---------------------------------------------------------
    # 4. Define Selected Sensor Columns
    # ---------------------------------------------------------
    sensor_cols = [
        "Air temperature [K]",
        "Process temperature [K]",
        "Rotational speed [rpm]",
        "Torque [Nm]",
        "Tool wear [min]"
    ]

    # ---------------------------------------------------------
    # 5. Generate and Save Visualizations
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("Generating and saving charts in 'outputs/' folder...")
    print("=" * 60)
    
    # --- Chart 1: Failure Distribution ---
    plt.figure(figsize=(7, 5))
    ax = sns.countplot(data=df, x=target_col, hue=target_col, legend=False, palette=["#2b5c8f", "#d95f02"])
    plt.title("Machine Failure Distribution", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Machine Failure (0 = Normal, 1 = Failed)", fontsize=11)
    plt.ylabel("Count of Records", fontsize=11)
    plt.xticks([0, 1], ["No Failure (0)", "Failure (1)"])
    
    # Annotate bars with counts
    for p in ax.patches:
        height = int(p.get_height())
        ax.annotate(f"{height:,}", (p.get_x() + p.get_width() / 2., height),
                    ha="center", va="bottom", fontsize=10, xytext=(0, 5), textcoords="offset points")
                    
    plt.tight_layout()
    chart1_path = os.path.join(output_dir, "failure_distribution.png")
    plt.savefig(chart1_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f" Saved: {chart1_path}")

    # --- Chart 2: Tool Wear vs Failure ---
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df, x=target_col, y="Tool wear [min]", hue=target_col, legend=False, palette=["#2b5c8f", "#d95f02"])
    plt.title("Tool Wear Distribution by Machine Failure Status", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Machine Failure Status", fontsize=11)
    plt.ylabel("Tool Wear [min]", fontsize=11)
    plt.xticks([0, 1], ["No Failure (0)", "Failure (1)"])
    
    plt.tight_layout()
    chart2_path = os.path.join(output_dir, "tool_wear_vs_failure.png")
    plt.savefig(chart2_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f" Saved: {chart2_path}")

    # --- Chart 3: Torque vs Failure ---
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df, x=target_col, y="Torque [Nm]", hue=target_col, legend=False, palette=["#2b5c8f", "#d95f02"])
    plt.title("Torque Distribution by Machine Failure Status", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Machine Failure Status", fontsize=11)
    plt.ylabel("Torque [Nm]", fontsize=11)
    plt.xticks([0, 1], ["No Failure (0)", "Failure (1)"])
    
    plt.tight_layout()
    chart3_path = os.path.join(output_dir, "torque_vs_failure.png")
    plt.savefig(chart3_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f" Saved: {chart3_path}")

    # --- Chart 4: Sensor Correlation Heatmap ---
    plt.figure(figsize=(9, 7))
    analysis_cols = sensor_cols + [target_col]
    corr_matrix = df[analysis_cols].corr()
    
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1,
                linewidths=0.5, cbar_kws={"label": "Pearson Correlation"})
    plt.title("Sensor & Target Correlation Heatmap", fontsize=14, fontweight="bold", pad=12)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.yticks(fontsize=9)
    
    plt.tight_layout()
    chart4_path = os.path.join(output_dir, "sensor_correlation_heatmap.png")
    plt.savefig(chart4_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f" Saved: {chart4_path}")

    print("\n" + "=" * 60)
    print("Analysis complete! All charts saved in outputs/.")
    print("=" * 60)

if __name__ == "__main__":
    main()
