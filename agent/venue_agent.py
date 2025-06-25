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

class VenueSearchInput(BaseModel):
    location: str
    capacity: Optional[int] = None

class VenueFinderAgent:
    def __init__(self, llm):
        """Initialize the venue finder agent."""
        self.llm = llm
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()

    def _create_tools(self) -> List[Tool]:
        """Create the tools for the agent."""
        # Ensure SERPER_API_KEY is set in the environment
        search = GoogleSerperAPIWrapper()
        return [
            Tool(
                name="web_search_venues",
                func=search.run,
                description="""Search the web for venues, cafes, restaurants, food stalls, or interesting places based on user requirements. Input can be any natural language description of the place, food, drink, or experience the user wants. Present the results in a clear, conversational format."""
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

    def _create_agent(self) -> AgentExecutor:
        """Create the agent with tools and prompt."""
        system_message = SystemMessage(content="""
        You are a helpful assistant for finding places. You can help users discover venues, cafes, restaurants, food stalls, and interesting places for any occasion or interest, including food, drinks, and hangouts. Use the web_search_venues tool to search the web for any place or experience the user requests.
        
        IMPORTANT RULES:
        - ALWAYS use the web_search_venues tool for any place, cafe, restaurant, or venue search
        - NEVER return code blocks or raw data in your responses
        - ALWAYS format your responses in **Markdown** (using tables, bullet lists, and headings as appropriate)
        - When presenting place information, use bullet points, numbered lists, or Markdown tables for clarity
        - When listing multiple places, present each place as an individual Markdown table with its features (such as Name, Location, Type, Price, Amenities, etc.).
        - When comparing places, ALWAYS use a valid Markdown table. Each row must be on its own line, columns separated by single pipes (|), and include a header separator row with dashes (---).
        - Never show code or raw data structures
        - Keep responses conversational and friendly
        """)

        prompt = ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    def process_query(self, query: str) -> str:
        """Process a user query and return a response. LLM extracts requirements and calls tools."""
        try:
            response = self.agent.invoke({"input": query})
            return response["output"] if isinstance(response, dict) and "output" in response else str(response)
        except Exception as e:
            print(f"Error processing query: {str(e)}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}" 