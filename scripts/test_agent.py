import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from agent.venue_agent import VenueFinderAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

def test_venue_finder():
    """Test the venue finder agent with some sample queries."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize the LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            convert_system_message_to_human=True
        )
        
        # Initialize the venue finder agent
        agent = VenueFinderAgent(llm)
        
        # Test queries
        test_queries = [
            "I need a venue for a corporate conference in Lonavla for 60 people",
            "Show me venues that have both AV and Wi-Fi",
            "What venues are available for a wedding reception?",
            "Compare V001 and V002"
        ]
        
        print("Testing Venue Finder Agent...\n")
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            print("-" * 50)
            response = agent.process_query(query)
            print(f"Response: {response}")
            print("-" * 50)
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    test_venue_finder() 