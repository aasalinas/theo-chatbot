from serpapi import GoogleSearch
import os
from dotenv import load_dotenv

# Load API Key
load_dotenv()
SERP_API_KEY = os.getenv("SERPAPI_KEY")

def test_google_search(query):
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "num": 5  # Get top 5 results
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "error" in results:
        print(f"❌ API Error: {results['error']}")
        return

    search_results = results.get("organic_results", [])
    if not search_results:
        print("⚠️ No search results found.")
        return

    # Print search results
    for index, result in enumerate(search_results):
        print(f"{index+1}. {result.get('title', 'No Title')}")
        print(f"   🔗 {result.get('link', '#')}\n")

# Run test
test_google_search("latest artificial intelligence news")