import os
import pandas as pd
import re
from collections import Counter

# Set NLTK_DATA environment variable first
os.environ['NLTK_DATA'] = r'C:\nltk_data'

# Import NLTK after setting environment variable
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer

# Print NLTK path to debug
print("NLTK is looking for data in these locations:")
print(nltk.data.path)

# Verify resources are available or download them
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
    nltk.data.find('sentiment/vader_lexicon.zip')
    print("All NLTK resources are available!")
except LookupError as e:
    print(f"Resource not found: {str(e)}")
    print("Downloading missing resources...")
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('vader_lexicon')

# Function for text preprocessing
def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove special characters and numbers
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    
    # Tokenize
    try:
        tokens = word_tokenize(text)
    except:
        print("Error with word_tokenize, using simple split")
        tokens = text.split()
    
    # Remove stopwords and lemmatize
    try:
        stop_words = set(stopwords.words('english'))
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words]
    except:
        print("Error with stopwords or lemmatization, skipping")
    
    # Rejoin tokens
    return ' '.join(tokens)

# Function for sentiment analysis
def analyze_sentiment(text):
    if not isinstance(text, str) or not text.strip():
        return {'compound': 0, 'pos': 0, 'neg': 0, 'neu': 1, 'sentiment': 'NEUTRAL'}
    
    try:
        sid = SentimentIntensityAnalyzer()
        scores = sid.polarity_scores(text)
        
        # Determine sentiment label
        if scores['compound'] >= 0.05:
            sentiment = 'POSITIVE'
        elif scores['compound'] <= -0.05:
            sentiment = 'NEGATIVE'
        else:
            sentiment = 'NEUTRAL'
            
        scores['sentiment'] = sentiment
        return scores
    except Exception as e:
        print(f"Error in sentiment analysis: {str(e)}")
        return {'compound': 0, 'pos': 0, 'neg': 0, 'neu': 1, 'sentiment': 'NEUTRAL'}

# Function for extracting frequent terms
def extract_frequent_terms(processed_texts, top_n=20):
    all_words = []
    for text in processed_texts:
        if isinstance(text, str) and text.strip():
            all_words.extend(text.split())
    
    word_counts = Counter(all_words)
    return word_counts.most_common(top_n)

# Main analysis function
def analyze_reviews(file_path, text_column='review_text'):
    # Read the CSV file
    try:
        reviews_df = pd.read_csv(file_path)
        print(f"Loaded {len(reviews_df)} reviews from {file_path}")
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        return None
    
    # Check if the text column exists
    if text_column not in reviews_df.columns:
        print(f"Column '{text_column}' not found. Available columns: {', '.join(reviews_df.columns)}")
        return None
    
    # Preprocess text
    print("Preprocessing text...")
    reviews_df['processed_text'] = reviews_df[text_column].apply(preprocess_text)
    
    # Analyze sentiment
    print("Analyzing sentiment...")
    sentiment_results = reviews_df[text_column].apply(analyze_sentiment)
    
    # Extract sentiment scores
    reviews_df['compound'] = sentiment_results.apply(lambda x: x['compound'])
    reviews_df['positive'] = sentiment_results.apply(lambda x: x['pos'])
    reviews_df['negative'] = sentiment_results.apply(lambda x: x['neg'])
    reviews_df['neutral'] = sentiment_results.apply(lambda x: x['neu'])
    reviews_df['sentiment'] = sentiment_results.apply(lambda x: x['sentiment'])
    
    # Print sentiment distribution
    sentiment_counts = reviews_df['sentiment'].value_counts()
    print("\nSentiment Distribution:")
    print(sentiment_counts)
    
    # Extract frequent terms
    print("\nExtracting frequent terms...")
    top_terms = extract_frequent_terms(reviews_df['processed_text'])
    print("\nTop 20 Terms Overall:")
    for term, count in top_terms:
        print(f"{term}: {count}")
    
    # Extract frequent terms by sentiment
    for sentiment in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']:
        sentiment_texts = reviews_df[reviews_df['sentiment'] == sentiment]['processed_text']
        top_sentiment_terms = extract_frequent_terms(sentiment_texts)
        print(f"\nTop 20 Terms in {sentiment} Reviews:")
        for term, count in top_sentiment_terms:
            print(f"{term}: {count}")
    
    # Save results
    output_file = 'analyzed_reviews.csv'
    reviews_df.to_csv(output_file, index=False)
    print(f"\nAnalysis complete! Results saved to '{output_file}'")
    
    return reviews_df

if __name__ == "__main__":
    # Get input from user
    file_path = input("Enter the path to your CSV file: ")
    text_column = input("Enter the name of the column containing review text (default: review_text): ") or 'review_text'
    
    # Run analysis
    analyze_reviews(file_path, text_column)
