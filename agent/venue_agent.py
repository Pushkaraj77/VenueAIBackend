import os
from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
from langchain.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from pydantic import BaseModel
import logging

# --- Tool and prompt setup as functions ---
def create_tools():
    search = GoogleSerperAPIWrapper()
    return [
        Tool(
            name="web_search_venues",
            func=search.run,
            description="""Search the web for venues, facilities, and places based on user requirements. Pay attention to the specific event type or activity mentioned in the query and search for appropriate venues. For example, if the user asks for a sports event, search for sports complexes, stadiums, athletic facilities. If they ask for a corporate event, search for conference centers, business venues. If they ask for a wedding, search for wedding venues, banquet halls. Always match the venue type to the event context. Input can be any natural language description of the place, event type, or experience the user wants. Present the results in a clear, conversational format."""
        ),
        Tool(
            name="get_venue_details",
            func=lambda venue_id: "Please use the web_search_venues tool to find details about the specified place.",
            description="""Get detailed information about a specific place. Use the web_search_venues tool to search the web for details about the place and present them in a natural, conversational way. DO NOT show the function call or code in your response."""
        ),
        Tool(
            name="compare_venues",
            func=lambda venue_ids: "Please use the web_search_venues tool to find information about the specified places and present a comparison.",
            description="""Compare multiple places based on user requirements. Use the web_search_venues tool to search the web for information about the places and present the comparison in a natural, conversational way. DO NOT show the function call or code in your response."""
        ),
        Tool(
            name="check_location_availability",
            func=lambda location: "Please use the web_search_venues tool to check if places exist in the location.",
            description="""Check if any places exist for the given location. Use the web_search_venues tool to search the web to determine if places exist in the location and respond accordingly."""
        )
    ]

def create_prompt():
    system_message = SystemMessage(content="""
    You are a helpful assistant for finding places. You can help users discover venues, cafes, restaurants, food stalls, and interesting places for any occasion or interest, including food, drinks, and hangouts. Use the web_search_venues tool to search the web for any place or experience the user requests.
    
    IMPORTANT RULES:
    - ALWAYS ensure that user query has a location, if it's not present, ask the user for the location, until then you can't proceed with the search.
    - ALWAYS use the web_search_venues tool for any place, cafe, restaurant, or venue search
    - ALWAYS provide atleast 5 locations for the user to choose from, if the user asks for a specific place, you can provide 1 option.
    - NEVER return code blocks or raw data in your responses
    - ALWAYS format your responses in **Markdown** (using tables, bullet lists, and headings as appropriate)
    - When presenting place information, use bullet points, numbered lists, or Markdown tables for clarity
    - When listing multiple places, present each place as an individual Markdown table with its features (such as Name, Location, Type, Price, Amenities, etc.).
    - When comparing places, ALWAYS use a valid Markdown table. Each row must be on its own line, columns separated by single pipes (|), and include a header separator row with dashes (---).
    - Keep responses conversational and friendly
    - ALWAYS include the city/location name prominently in your response for context
    - For each venue, provide: Name, Location (specific area), Type, Capacity, Price Range, Key Features
    - Structure your response so that each venue is clearly separated and identifiable
    - ALWAYS present venues in a proper Markdown table format with headers and separators
    - Use this exact table format:
    | Name | Location | Type | Capacity | Price Range | Key Features |
    |------|----------|------|----------|-------------|--------------|
    | Venue Name | Specific Area | Venue Type | Capacity Info | Price Info | Key Features |
    
    CONTEXT UNDERSTANDING:
    - Pay close attention to the specific type of event or activity mentioned in the user's query
    - If they mention "sports event", search for sports-related venues like stadiums, sports complexes, athletic facilities, etc.
    - If they mention "corporate event", search for business venues like conference centers, meeting rooms, etc.
    - If they mention "wedding", search for wedding venues like banquet halls, marriage gardens, etc.
    - If they mention "party", search for party venues like event spaces, clubs, etc.
    - If they mention "cultural event", search for cultural venues like auditoriums, theaters, etc.
    - If they mention "outdoor event", search for outdoor venues like parks, gardens, open grounds, etc.
    - Always match the venue type to the event type mentioned in the query
    - Do NOT recommend restaurants for sports events or banquet halls for outdoor activities unless specifically requested
    - Use your understanding of the event context to find the most appropriate venues
    """)
    return ChatPromptTemplate.from_messages([
        system_message,
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

# --- LangGraph node function ---
def venue_finder_node(state: dict) -> dict:
    """LangGraph node for venue finding. Expects state with 'input' and 'chat_history'. Returns updated state with 'output'."""
    if "llm" not in state:
        raise ValueError("LLM not found in state! State keys: " + str(list(state.keys())))
    llm = state["llm"]
    input_text = state["input"]
    chat_history = state.get("chat_history", [])
    
    tools = create_tools()
    prompt = create_prompt()
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    agent = create_openai_functions_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        max_iterations=3  # Allow multiple searches for comprehensive results
    )
    # Set memory state if provided
    if chat_history:
        memory.chat_memory.messages = chat_history
    try:
        response = agent_executor.invoke({"input": input_text})
        output = response["output"] if isinstance(response, dict) and "output" in response else str(response)
    except Exception as e:
        output = f"I apologize, but I encountered an error while processing your request: {str(e)}"
    # Update state with output and chat_history
    return {
        **state,
        "output": output,
        "chat_history": memory.chat_memory.messages
    } 