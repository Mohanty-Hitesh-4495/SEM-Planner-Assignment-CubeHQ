import os
import yaml
from modules.scraper import scrape
from modules.keyword_collector import collect_keywords
from modules.data_cleaner import clean_data
from modules.group_keywords import group_keywords_with_llm
import pandas as pd

def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main(config_path="config.yml", scrape_content=False):
    config = load_config(config_path)
    # Step 1: Scrape brand/competitor (optional)
    if scrape_content:
        print("Scraping brand website...")
        brand_content = scrape(config["brand_website"])
        print("Scraping competitor website...")
        competitor_content = scrape(config["competitor_website"])
        # Optionally save scraped content for LLM seed extraction
        os.makedirs("output", exist_ok=True)
        with open("output/brand_content.txt", "w", encoding="utf-8") as f:
            f.write(str(brand_content))
        with open("output/competitor_content.txt", "w", encoding="utf-8") as f:
            f.write(str(competitor_content))
    # Step 2: Fetch keywords from WordStream
    print("Collecting keywords from WordStream...")
    collect_keywords(config, output_csv="data/wordstream_output.csv")
    # Step 3: Clean & filter data
    print("Cleaning keyword data...")
    clean_data(input_csv="data/wordstream_output.csv", output_csv="data/cleaned_keywords.csv")
    # Step 4: Group keywords via LLM
    print("Grouping keywords via LLM...")
    api_key = os.getenv("GROQ_API_KEY")
    df = pd.read_csv("data/cleaned_keywords.csv")
    grouped_df = group_keywords_with_llm(df, api_key, output_csv="output/ad_groups.csv")
    print("Pipeline complete. Output saved to output/ad_groups.csv")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SEM Keyword Pipeline")
    parser.add_argument("--config", type=str, default="config.yml", help="Path to config YAML")
    parser.add_argument("--scrape", action="store_true", help="Scrape brand/competitor content")
    args = parser.parse_args()
    main(config_path=args.config, scrape_content=args.scrape)
