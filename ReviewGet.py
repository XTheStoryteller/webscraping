import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time
import random
import os
import csv
import urllib3
import certifi
import ssl

def print_page_structure(html_content, output_file="page_structure.html"):

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Saved HTML structure to {output_file} for debugging")
    
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    
    time_elements = soup.find_all('time')
    print(f"Found {len(time_elements)} time elements")
    if time_elements:
        print("Sample time element:")
        print(time_elements[0])
        
    
    review_containers = soup.find_all('div', {'class': lambda x: x and ('card' in x.lower() or 'review' in x.lower())})
    print(f"Found {len(review_containers)} potential review containers")
    if review_containers:
        print("Sample review container classes:")
        for i, container in enumerate(review_containers[:3]):
            if 'class' in container.attrs:
                print(f"Container {i+1}: {container['class']}")

def scrape_trustpilot_reviews(company_url, num_pages=5, bypass_ssl=False, debug=False):
    """
    Scrape Trustpilot reviews for a specific company URL.
    Focus only on review text and dates.
    
    Args:
        company_url (str): The company URL on Trustpilot (e.g., 'support.microsoft.com')
        num_pages (int): Number of pages to scrape (default: 5)
        bypass_ssl (bool): Whether to bypass SSL verification (default: False)
        debug (bool): Whether to save debug information (default: False)
    
    Returns:
        pandas.DataFrame: DataFrame containing the scraped reviews
    """
    
    review_dates = []
    review_texts = []
    
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    
    # Loop through pages
    for page in range(1, num_pages + 1):
        # Construct the URL 
        url = f"https://www.trustpilot.com/review/{company_url}?page={page}"
        
        print(f"Scraping page {page}...")
        
        try:
            # Send request with headers
            if bypass_ssl:
                # Disable SSL verification (only use for testing/debugging)
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                response = requests.get(url, headers=headers, verify=False)
            else:
                
                try:
                    # Use the certifi package to get a trusted certificate bundle
                    response = requests.get(url, headers=headers, verify=certifi.where())
                except Exception as cert_error:
                    print(f"Certificate error: {cert_error}")
                    print("Retrying with SSL verification disabled...")
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    response = requests.get(url, headers=headers, verify=False)
            
            # Check 
            if response.status_code == 200:
                # Parse HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # If debug mode is on, save the HTML for analysis
                if debug:
                    debug_file = f"trustpilot_page_{page}.html"
                    print_page_structure(response.text, debug_file)
                    print(f"Saved page {page} HTML to {debug_file} for debugging")
                
                # Find all review cards
                # Updated to look for more potential container elements based on your screenshot
                review_cards = soup.find_all('div', {'class': 'styles_cardWrapper__LcCPA'})
                
                if not review_cards:
                    print(f"No review cards found with primary class, trying alternative classes...")
                    # Try finding cards by the reviewCardInnerHeader class you shared
                    header_elements = soup.find_all('div', {'class': lambda x: x and 'styles_reviewCardInnerHeader' in x})
                    if header_elements:
                        print(f"Found {len(header_elements)} review headers, extracting their parent elements...")
                        # Get the parent elements of these headers as they contain the full review
                        review_cards = [header.find_parent('div') for header in header_elements]
                    else:
                        # Try yet another approach - look for any div that contains a time element
                        time_elements = soup.find_all('time', {'data-service-review-date-time-ago': 'true'})
                        if time_elements:
                            print(f"Found {len(time_elements)} time elements, extracting their parent review cards...")
                            # Get the parent div elements that contain the full review
                            review_cards = [time_elem.find_parent('div', {'class': lambda x: x and 'card' in x.lower()}) 
                                           for time_elem in time_elements]
                            # Filter out None values
                            review_cards = [card for card in review_cards if card is not None]
                
                # If we still don't find any, print a sample of the HTML for debugging
                if not review_cards:
                    print("Could not find review cards with either selector.")
                    print("Sample of HTML received:")
                    print(soup.prettify()[:1000])  # Print first 1000 chars for debugging
                    continue
                
                print(f"Found {len(review_cards)} reviews on page {page}")
                
                # Process each review card
                for review in review_cards:
                    # Extract review date - updated to match the exact structure you shared
                    # Look for time element with data-service-review-date-time-ago attribute
                    date_element = review.find('time', {'data-service-review-date-time-ago': 'true'})
                    if date_element and date_element.has_attr('datetime'):
                        review_date = date_element['datetime']
                        review_dates.append(review_date)
                    else:
                        # Alternative search for any time element
                        date_element = review.find('time')
                        if date_element and date_element.has_attr('datetime'):
                            review_date = date_element['datetime']
                            review_dates.append(review_date)
                        else:
                            print("Could not find date element")
                            review_dates.append(None)
                    
                    # Extract review text
                    # Updated to match the exact class structure you found
                    text_element = review.find('p', {'class': 'typography_body-l__v5JLj typography_appearance-default__t8iAq'})
                    if text_element:
                        review_texts.append(text_element.get_text(strip=True))
                    else:
                        # Try alternative class formats if the first one doesn't work
                        text_element = review.find('p', {'data-service-review-text-typography': 'true'})
                        if text_element:
                            review_texts.append(text_element.get_text(strip=True))
                        else:
                            # Try yet another alternative format
                            text_element = review.find('p', {'class': lambda x: x and 'typography_body-l__v5JLj' in x})
                            if text_element:
                                review_texts.append(text_element.get_text(strip=True))
                            else:
                                review_texts.append(None)
                                print("Could not find review text with any of the selectors")
            
            else:
                print(f"Failed to retrieve page {page}. Status code: {response.status_code}")
            
            # random delay
            delay = random.uniform(2, 5)
            print(f"Waiting {delay:.2f} seconds before next request...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"Error scraping page {page}: {str(e)}")
    
    # Create a DataFrame 
    reviews_data = {
        'Date': review_dates,
        'Review Text': review_texts
    }
    
    # Filter out  None 
    df = pd.DataFrame(reviews_data)
    df = df.dropna(how='all')
    
    # Process dates
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    return df

def save_to_corpus_folder(df, company_name):
   
    # Create Corpus folder 
    corpus_folder = os.path.join("Corpus", company_name)
    os.makedirs(corpus_folder, exist_ok=True)
    
   
    for index, row in df.iterrows():
        # Create a filename with the date
        if pd.notna(row['Date']):
            date_str = row['Date'].strftime('%Y-%m-%d')
        else:
            date_str = 'unknown_date'
        
        filename = f"review_{index+1}_{date_str}.txt"
        file_path = os.path.join(corpus_folder, filename)
        
        # review text 
        if pd.notna(row['Review Text']):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Date: {row['Date']}\n\n")
                f.write(row['Review Text'])
            
            print(f"Saved review to {file_path}")
    
   
    csv_path = os.path.join(corpus_folder, f"{company_name}_reviews.csv")
    df.to_csv(csv_path, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8-sig')
    print(f"Saved combined reviews to {csv_path}")


if __name__ == "__main__":
    # The company URL part from the Trustpilot URL
    company_url = "support.microsoft.com"
    company_name = "microsoft_support"  # Used for folder naming
    
    # Number of pages
    num_pages = 3
    
    print(f"Starting to scrape Trustpilot reviews for {company_url}...")
    
   
    reviews_df = scrape_trustpilot_reviews(company_url, num_pages, bypass_ssl=True, debug=True)
    

    print(f"\nSuccessfully scraped {len(reviews_df)} reviews.")
    if not reviews_df.empty:
        print("\nSample of the data:")
        print(reviews_df.head())
        
        # Save the data to the Corpus folder
        save_to_corpus_folder(reviews_df, company_name)
        
        print("\nScraping and saving to Corpus folder complete!")
    else:
        print("\nNo reviews were scraped. Check the debug HTML files to analyze the page structure.")
