#!/usr/bin/env python3
"""
Test script for the interactive collaborative multi-agent system with two-step workflow
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from agent.venue_graph import run_venue_finder_graph

# Load environment variables
load_dotenv()

def test_interactive_workflow():
    """Test the interactive two-step collaborative workflow"""
    
    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        convert_system_message_to_human=True
    )
    
    print("Testing Interactive Two-Step Collaborative Workflow")
    print("=" * 70)
    print("Step 1: User asks for venues")
    print("Step 2: System offers risk assessment option")
    print("Step 3: User chooses which venues to assess")
    print("=" * 70)
    
    # Test the complete interactive flow
    chat_history = []
    
    # Step 1: Initial venue request
    print("\n=== STEP 1: Initial Venue Request ===")
    test_query_1 = "I need a venue for a corporate event in Delhi next week"
    print(f"User: {test_query_1}")
    print("-" * 50)
    
    try:
        response_1, chat_history = run_venue_finder_graph(llm, test_query_1, chat_history)
        print("System Response:")
        print("=" * 50)
        print(response_1)
        print("=" * 50)
        
        # Check if venue recommendations with risk assessment option are provided
        if "Risk Assessment Option" in response_1 and "Available venues:" in response_1:
            print("✅ Step 1 successful: Venue recommendations with risk assessment option provided")
        else:
            print("⚠️ Step 1 may have issues: Risk assessment option not found")
        
        # Step 2: User requests risk assessment for all venues
        print("\n=== STEP 2: User Requests Risk Assessment for All Venues ===")
        test_query_2 = "Yes, please assess risks for all venues"
        print(f"User: {test_query_2}")
        print("-" * 50)
        
        response_2, chat_history = run_venue_finder_graph(llm, test_query_2, chat_history)
        print("System Response:")
        print("=" * 50)
        print(response_2[:1000] + "..." if len(response_2) > 1000 else response_2)
        print("=" * 50)
        
        # Check if risk assessment was performed
        if "Venue Risk Assessment Results" in response_2 and "Detailed Venue-Specific Risk Assessments" in response_2:
            print("✅ Step 2 successful: Risk assessment completed for all venues")
            
            # Show a sample of the risk assessment
            if "### 1." in response_2:
                print("\n" + "=" * 50)
                print("SAMPLE RISK ASSESSMENT:")
                print("=" * 50)
                venue_start = response_2.find("### 1.")
                venue_end = response_2.find("### 2.") if "### 2." in response_2 else len(response_2)
                venue_section = response_2[venue_start:venue_end]
                print(venue_section[:800] + "..." if len(venue_section) > 800 else venue_section)
        else:
            print("⚠️ Step 2 may have issues: Risk assessment not found in response")
        
    except Exception as e:
        print(f"Error during interactive workflow: {e}")
        import traceback
        traceback.print_exc()

def test_specific_venue_selection():
    """Test selecting specific venues for risk assessment"""
    
    print("\n" + "=" * 70)
    print("Testing Specific Venue Selection")
    print("=" * 70)
    
    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        convert_system_message_to_human=True
    )
    
    chat_history = []
    
    # Step 1: Get venues
    print("\n=== STEP 1: Get Venues ===")
    test_query_1 = "I need venues for a wedding in Mumbai next month"
    print(f"User: {test_query_1}")
    
    try:
        response_1, chat_history = run_venue_finder_graph(llm, test_query_1, chat_history)
        
        if "Risk Assessment Option" in response_1:
            print("✅ Venues provided with risk assessment option")
            
            # Step 2: Request risk assessment for specific venue
            print("\n=== STEP 2: Request Risk Assessment for Specific Venue ===")
            test_query_2 = "Please assess risks for venue 1"
            print(f"User: {test_query_2}")
            
            response_2, chat_history = run_venue_finder_graph(llm, test_query_2, chat_history)
            
            if "Venue Risk Assessment Results" in response_2:
                print("✅ Specific venue risk assessment completed")
                print(f"Response length: {len(response_2)} characters")
            else:
                print("⚠️ Specific venue risk assessment may have failed")
        else:
            print("⚠️ Venues not provided with risk assessment option")
            
    except Exception as e:
        print(f"Error: {e}")

def test_edge_cases():
    """Test edge cases in the interactive workflow"""
    
    print("\n" + "=" * 70)
    print("Testing Edge Cases")
    print("=" * 70)
    
    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        convert_system_message_to_human=True
    )
    
    # Test Case 1: Vague query
    print("\n=== Test Case 1: Vague Query ===")
    test_query_1 = "I need a venue"
    print(f"User: {test_query_1}")
    
    try:
        response_1, chat_history = run_venue_finder_graph(llm, test_query_1, [])
        print("Response:")
        print(response_1[:300] + "..." if len(response_1) > 300 else response_1)
        
        if any(phrase in response_1.lower() for phrase in ['location', 'city', 'area']):
            print("✅ Correctly asking for more information")
        else:
            print("⚠️ May not be handling vague queries properly")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test Case 2: Risk assessment without venues
    print("\n=== Test Case 2: Risk Assessment Without Venues ===")
    test_query_2 = "Yes, assess risks"
    print(f"User: {test_query_2}")
    
    try:
        response_2, chat_history = run_venue_finder_graph(llm, test_query_2, [])
        print("Response:")
        print(response_2[:300] + "..." if len(response_2) > 300 else response_2)
        
        if "don't have any venues stored" in response_2.lower():
            print("✅ Correctly handling risk assessment without venues")
        else:
            print("⚠️ May not be handling this edge case properly")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_interactive_workflow()
    test_specific_venue_selection()
    test_edge_cases() 