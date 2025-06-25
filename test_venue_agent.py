from agent.venue_agent import VenueFinderAgent
import os
from dotenv import load_dotenv

def test_venue_agent():
    # Load environment variables
    load_dotenv()
    
    # Check if Google API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found in environment variables")
        return
    
    # Initialize the venue finder agent
    print("Initializing VenueFinderAgent...")
    agent = VenueFinderAgent()
    
    # Test queries
    test_queries = [
        "Find venues in Mumbai for a corporate event with capacity of 100 people",
        "Show me wedding venues in Bangalore that serve vegetarian food",
        "Compare venues in Pune for a party with budget under 50000"
    ]
    
    # Process each test query
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}:")
        print(f"Query: {query}")
        try:
            response = agent.process_query(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error processing query: {str(e)}")

if __name__ == "__main__":
    test_venue_agent() 