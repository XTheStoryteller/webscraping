import pandas as pd
import os
import openai
from tqdm import tqdm

# Your OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load your CSV or Excel file
df = pd.read_csv('Corpus/amazon/amazon_reviews.csv')  # adjust path/format as needed

# Column to analyze
review_col = 'Review Text'  # name of your column with reviews

# Prepare output columns
df['sentiment'] = ""
df['summary'] = ""
df['followup'] = ""

# Function to call ChatGPT for analysis
def analyze_review(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a commercially aware customer service analyst for a retail execution consultant and their client Amazon looking out for opportunities to delight and retain clients or find new opportunities."},
                {"role": "user", "content": f"Review: \"{text}\"\n\n1. What's the overall sentiment? (positive, neutral, negative)\n2. Summarize this message in three sentences giving a potential action\n3. What questions you'd follow up to give a better service or solution"}
            ],
            temperature=0.2
        )
        output = response.choices[0].message['content']
        lines = output.strip().split("\n")
        
        # Extract sentiment from the first line
        sentiment = lines[0].split(":")[-1].strip() if lines and ":" in lines[0] else "unknown"
        
        # Extract summary from the second line
        summary = lines[1].split(":", 1)[-1].strip() if len(lines) > 1 and ":" in lines[1] else ""
        
        # Extract followup from the third line
        followup = lines[2].split(":", 1)[-1].strip() if len(lines) > 2 and ":" in lines[2] else ""
        
        return sentiment, summary, followup
    except Exception as e:
        print(f"Error processing review: {e}")
        return "error", f"Processing error: {str(e)}", ""

# Apply the analysis
for idx in tqdm(df.index):
    if pd.notna(df.loc[idx, review_col]) and df.loc[idx, review_col].strip():  # Check if review text exists and is not empty
        sentiment, summary, followup = analyze_review(df.loc[idx, review_col])
        df.at[idx, 'sentiment'] = sentiment
        df.at[idx, 'summary'] = summary
        df.at[idx, 'followup'] = followup
    else:
        df.at[idx, 'sentiment'] = "missing"
        df.at[idx, 'summary'] = "No review text provided"
        df.at[idx, 'followup'] = ""

# Create output directory if it doesn't exist
os.makedirs("Data/output", exist_ok=True)

# Save the results
df.to_csv("Data/output/agentic_analyzed_reviews.csv", index=False)
print("Analysis complete. Output saved to 'Data/output/agentic_analyzed_reviews.csv'.")
