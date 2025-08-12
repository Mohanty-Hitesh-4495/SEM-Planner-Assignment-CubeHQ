import pandas as pd
import os

def clean_data(input_csv="data/wordstream_output.csv", output_csv="data/cleaned_keywords.csv", min_volume=1, match_type="broad"):
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file not found: {input_csv}")
    df = pd.read_csv(input_csv)
    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # Remove duplicates
    df = df.drop_duplicates(subset=["keyword"])
    # Filter by search volume
    if "monthly_volume" in df.columns:
        df = df[df["monthly_volume"].astype(str).str.replace(",", "").astype(float) >= min_volume]
    # Keep relevant columns
    keep_cols = ["keyword", "monthly_volume", "cpc", "competition"]
    df = df[[col for col in keep_cols if col in df.columns]]
    # Add match_type column
    df["match_type"] = match_type
    # Save cleaned data
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"Cleaned data saved to {output_csv} ({len(df)} rows)")

if __name__ == "__main__":
    clean_data()
