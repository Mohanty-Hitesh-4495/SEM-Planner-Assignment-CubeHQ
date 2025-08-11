import pandas as pd
import os
import json
from langchain_community.llms import Groq
from langchain.prompts import PromptTemplate

def load_keywords(input_csv="data/cleaned_keywords.csv"):
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file not found: {input_csv}")
    return pd.read_csv(input_csv)

def group_keywords_with_llm(df, api_key, model="mixtral-8x7b-32768", output_csv="data/grouped_keywords.csv"):
    # Prepare prompt
    keywords = df["keyword"].tolist()
    prompt = (
        "Group these keywords into tightly themed ad groups with match types (Exact, Phrase, Broad). "
        "Return JSON format: [{ad_group, keyword, match_type, monthly_volume, cpc}].\n"
        f"Keywords: {keywords}"
    )
    llm = Groq(api_key=api_key, model=model)
    response = llm(prompt)
    # Parse JSON from LLM response
    try:
        result = json.loads(response)
    except Exception:
        # Try to extract JSON from response
        start = response.find('[')
        end = response.rfind(']')+1
        result = json.loads(response[start:end])
    # Convert to DataFrame
    grouped_df = pd.DataFrame(result)
    # Fill missing columns from original df
    for col in ["monthly_volume", "cpc"]:
        if col not in grouped_df.columns and col in df.columns:
            grouped_df[col] = grouped_df["keyword"].map(df.set_index("keyword")[col])
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    grouped_df.to_csv(output_csv, index=False)
    print(f"Grouped keywords saved to {output_csv} ({len(grouped_df)} rows)")
    return grouped_df

if __name__ == "__main__":
    import os
    api_key = os.getenv("GROQ_API_KEY")
    df = load_keywords()
    group_keywords_with_llm(df, api_key)
