from langgraph.graph import StateGraph, END
from langchain_core.language_models.base import BaseLanguageModel
from agent.venue_agent import venue_finder_node
from agent.event_risk_agent import event_risk_assessment_node
import re

# --- Router node ---
def router_node(state: dict) -> dict:
    """Router that directs all queries to collaborative workflow."""
    input_text = state["input"]
    chat_history = state.get("chat_history", [])
    
    print(f"Router received: 'collaborative' for input: '{input_text}'")
    print("Routing to collaborative mode")
    
    # All queries go to collaborative workflow
    state["route"] = "collaborative"
    return state

# --- LLM-based venue extraction and decision node ---
def intelligent_venue_processor_node(state: dict) -> dict:
    """Uses LLM to intelligently process venue output and decide next steps."""
    llm = state["llm"]
    venue_output = state.get("venue_output", "")
    input_text = state["input"]
    
    # Use LLM to analyze the venue output and make decisions
    analysis_prompt = f"""
    You are an intelligent coordinator for a venue and risk assessment system. Analyze the venue finder's response and determine the next steps.

    User's original query: {input_text}
    
    Venue finder's response:
    {venue_output}

    Please analyze this response and provide a JSON response with the following structure:
    {{
        "action": "ask_for_info" | "extract_venues" | "no_venues_found",
        "reasoning": "Brief explanation of your decision",
        "venues": [
            {{
                "name": "Venue Name",
                "location": "Specific Location",
                "type": "Venue Type",
            }}
        ]
    }}

    Decision rules:
    - If the venue finder is asking for more information (questions, clarifications), set action to "ask_for_info"
    - If the venue finder provided actual venues (names, locations, details), set action to "extract_venues" and extract the venue information
    - If no venues were found or the response is unclear, set action to "no_venues_found"
    - Only extract venues that are actual venue names, not generic words or descriptions
    - For venues, extract the most relevant information available (name, location, type)
    - Only ask for more information if the venue finder output is missing location or event type, NOT capacity or price.

    Respond with ONLY the JSON, no additional text.
    """
    
    try:
        response = llm.invoke(analysis_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        import json
        import re
        
        # Find JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            analysis_result = json.loads(json_match.group())
        else:
            # Fallback if JSON parsing fails
            analysis_result = {
                "action": "ask_for_info",
                "reasoning": "Could not parse LLM response",
                "venues": []
            }
        
        print(f"LLM Analysis Result: {analysis_result}")
        
        # Update state with analysis results
        state.update({
            "llm_analysis": analysis_result,
            "extracted_venues": analysis_result.get("venues", []),
            "next_action": analysis_result.get("action", "ask_for_info")
        })
        
        return state
        
    except Exception as e:
        print(f"Error in LLM venue analysis: {e}")
        # Fallback to asking for info
        state.update({
            "llm_analysis": {"action": "ask_for_info", "reasoning": "Error in analysis", "venues": []},
            "extracted_venues": [],
            "next_action": "ask_for_info"
        })
        return state

# --- Interactive collaborative venue and risk assessment node ---
def interactive_collaborative_node(state: dict) -> dict:
    """Interactive collaborative workflow: venue finding first, then optional risk assessment."""
    llm = state["llm"]
    input_text = state["input"]
    chat_history = state.get("chat_history", [])
    extracted_venues = state.get("extracted_venues", [])
    
    print("Starting interactive collaborative venue and risk assessment")
    print(f"Current extracted venues: {len(extracted_venues)} venues")
    
    # Check if this is a follow-up response to venue recommendations
    is_follow_up = any(phrase in input_text.lower() for phrase in [
        'yes', 'risk assessment', 'assess risks', 'check risks', 'all venues', 
        'venue 1', 'venue 2', 'first venue', 'second venue', 'the leela', 'taj palace'
    ])
    
    if is_follow_up and extracted_venues:
        print("Detected follow-up response with venues - proceeding to risk assessment")
        # This is a follow-up response - handle risk assessment request
        return handle_risk_assessment_request(state)
    elif is_follow_up and not extracted_venues:
        print("Detected follow-up response but no venues found - asking user to start over")
        return {
            **state,
            "output": "I don't have any venues stored from our previous conversation. Please start by asking for venue recommendations.",
            "chat_history": chat_history
        }
    else:
        print("New query detected - proceeding to venue finding")
        # This is a new query - find venues first
        return handle_venue_finding(state)

def handle_venue_finding(state: dict) -> dict:
    """Handle the venue finding step of the collaborative workflow."""
    llm = state["llm"]
    input_text = state["input"]
    chat_history = state.get("chat_history", [])
    
    print("Step 1: Finding venues")
    
    # Step 1: Find venues
    venue_state = {
        "llm": llm,
        "input": input_text,
        "chat_history": chat_history
    }
    
    try:
        venue_result = venue_finder_node(venue_state)
        venue_output = venue_result.get("output", "")
        venue_chat_history = venue_result.get("chat_history", [])
        print("Venue finder completed")
        
        # Step 2: Use LLM to analyze venue output
        analysis_state = {
            "llm": llm,
            "venue_output": venue_output,
            "input": input_text
        }
        
        analysis_result = intelligent_venue_processor_node(analysis_state)
        next_action = analysis_result.get("next_action", "ask_for_info")
        extracted_venues = analysis_result.get("extracted_venues", [])
        
        print(f"LLM decided next action: {next_action}")
        print(f"Extracted venues: {[v.get('name', 'Unknown') for v in extracted_venues]}")
        
        # Step 3: Handle different actions based on LLM decision
        if next_action == "ask_for_info":
            print("LLM detected venue agent is asking for information - returning venue response only")
            return {
                **state,
                "output": venue_output,
                "chat_history": venue_chat_history
            }
        
        elif next_action == "no_venues_found":
            print("LLM detected no venues found")
            return {
                **state,
                "output": f"""## Venue Information
{venue_output}

## Risk Assessment
Unable to identify specific venues for risk assessment. Please provide more specific details about your event requirements.""",
                "chat_history": venue_chat_history
            }
        
        elif next_action == "extract_venues" and extracted_venues:
            print(f"LLM extracted {len(extracted_venues)} venues - providing venue recommendations with risk assessment option")
            
            # Store venues in state for potential risk assessment
            state["extracted_venues"] = extracted_venues
            
            # Create venue recommendations with risk assessment option
            venue_section = f"""## Venue Recommendations
{venue_output}

## Risk Assessment Option

I found {len(extracted_venues)} venues that match your requirements. Would you like me to perform a detailed risk assessment for these venues?

**Available venues:**
"""
            
            for i, venue in enumerate(extracted_venues, 1):
                venue_section += f"{i}. **{venue.get('name', 'Unknown')}** - {venue.get('location', 'Unknown')}\n"
            
            venue_section += f"""
**To get risk assessment, please respond with:**
- "Yes" or "Risk assessment" - to assess risks for all venues
- "Venue 1" or "The Leela" - to assess risks for specific venue(s)
- "No" - if you don't need risk assessment

The risk assessment will include venue-specific information about:
• Current weather alerts and warnings
• Recent security incidents in the area
• Health alerts and disease outbreaks
• Traffic and infrastructure issues
• Conflicting events or VIP movements"""
            
            return {
                **state,
                "output": venue_section,
                "chat_history": venue_chat_history,
                "extracted_venues": extracted_venues  # Ensure venues are stored in the returned state
            }
        
        else:
            # Fallback case
            return {
                **state,
                "output": f"""## Venue Information
{venue_output}

## Risk Assessment
Unable to process venue information for risk assessment. Please try rephrasing your query.""",
                "chat_history": venue_chat_history
            }
        
    except Exception as e:
        print(f"Venue finding error: {e}")
        error_output = f"I apologize, but I encountered an error during venue finding: {str(e)}"
        return {
            **state,
            "output": error_output,
            "chat_history": chat_history
        }

def handle_risk_assessment_request(state: dict) -> dict:
    """Handle the risk assessment step based on user's venue selection."""
    llm = state["llm"]
    input_text = state["input"]
    chat_history = state.get("chat_history", [])
    extracted_venues = state.get("extracted_venues", [])
    
    print("Step 2: Handling risk assessment request")
    
    if not extracted_venues:
        return {
            **state,
            "output": "I don't have any venues stored from our previous conversation. Please start by asking for venue recommendations.",
            "chat_history": chat_history
        }
    
    # Determine which venues to assess based on user input
    venues_to_assess = []
    
    if any(phrase in input_text.lower() for phrase in ['yes', 'all venues', 'all', 'risk assessment', 'assess risks']):
        # User wants risk assessment for all venues
        venues_to_assess = extracted_venues
        print(f"User requested risk assessment for all {len(venues_to_assess)} venues")
    else:
        # User specified specific venues
        venue_names = [venue.get('name', '').lower() for venue in extracted_venues]
        
        # Check for venue numbers (e.g., "venue 1", "first venue")
        if '1' in input_text or 'first' in input_text:
            if len(extracted_venues) >= 1:
                venues_to_assess.append(extracted_venues[0])
        if '2' in input_text or 'second' in input_text:
            if len(extracted_venues) >= 2:
                venues_to_assess.append(extracted_venues[1])
        if '3' in input_text or 'third' in input_text:
            if len(extracted_venues) >= 3:
                venues_to_assess.append(extracted_venues[2])
        
        # Check for venue names mentioned
        for venue in extracted_venues:
            venue_name = venue.get('name', '').lower()
            if venue_name in input_text.lower():
                venues_to_assess.append(venue)
        
        # If no specific venues found, ask for clarification
        if not venues_to_assess:
            venue_list = "\n".join([f"{i+1}. {venue.get('name', 'Unknown')}" for i, venue in enumerate(extracted_venues)])
            return {
                **state,
                "output": f"""I'm not sure which venues you'd like me to assess for risks. \n\n{venue_list}\n\nPlease specify which venues you'd like me to assess by responding with:\n- \"All venues\" or \"Yes\" - for all venues\n- \"Venue 1\" or \"The Leela\" - for specific venue(s)\n- Venue numbers like \"1 and 3\" or \"first and third\"""",
                "chat_history": chat_history
            }
    
    print(f"Assessing risks for {len(venues_to_assess)} venues: {[v.get('name', 'Unknown') for v in venues_to_assess]}")
    
    # Perform batch risk assessment for selected venues
    try:
        # Extract time period from original query or chat history
        time_period = ""
        original_query = ""
        if chat_history:
            # Look for time period in recent messages
            for msg in reversed(chat_history[-5:]):  # Check last 5 messages
                if hasattr(msg, 'content'):
                    content = msg.content.lower()
                    time_patterns = ["next week", "this week", "next month", "tomorrow", "today"]
                    for pattern in time_patterns:
                        if pattern in content:
                            time_period = pattern
                            original_query = msg.content
                            break
                if time_period:
                    break
        
        from agent.event_risk_agent import batch_assess_venue_risks
        risk_report = batch_assess_venue_risks(llm, venues_to_assess, time_period)
        
        # Return the batch risk report as output
        return {
            **state,
            "output": risk_report,
            "chat_history": chat_history
        }
    except Exception as e:
        print(f"Risk assessment error: {e}")
        error_output = f"I apologize, but I encountered an error during risk assessment: {str(e)}"
        return {
            **state,
            "output": error_output,
            "chat_history": chat_history
        }

def build_venue_finder_graph():
    print("build_venue_finder_graph called")
    graph = StateGraph(dict)
    # print("StateGraph object created:", graph)
    
    # Add nodes - only collaborative workflow
    graph.add_node("router", router_node)
    graph.add_node("collaborative", interactive_collaborative_node)
    
    graph.set_entry_point("router")
    
    # All routes go to collaborative
    graph.add_edge("router", "collaborative")
    
    # End points
    graph.add_edge("collaborative", END)
    
    compiled = graph.compile()
    print("Compiled graph in build_venue_finder_graph:", compiled)
    return compiled

# Expose a function to run the graph

def run_venue_finder_graph(llm: BaseLanguageModel, input_text: str, chat_history=None):
    # print("run_venue_finder_graph called with:")
    # print("  llm:", llm)
    # print("  input_text:", input_text)
    # print("  chat_history:", chat_history)
    compiled_graph = build_venue_finder_graph()
    # print("Compiled graph:", compiled_graph)
    
    # Extract venues from chat history if they exist
    extracted_venues = []
    if chat_history:
        # Look for venues in the last few messages
        for msg in reversed(chat_history[-3:]):
            if hasattr(msg, 'content') and isinstance(msg.content, str) and "VENUES_STORED:" in msg.content:
                # Extract venues from the special message
                try:
                    import json
                    venues_str = msg.content.split("VENUES_STORED:")[1].strip()
                    extracted_venues = json.loads(venues_str)
                    break
                except:
                    pass
    
    state = {
        "llm": llm,
        "input": input_text,
        "chat_history": chat_history or [],
        "extracted_venues": extracted_venues  # Pass venues from previous conversation
    }
    # print("State to be passed to graph:", state)
    result = compiled_graph.invoke(state)
    # print("Graph result keys:", list(result.keys()) if isinstance(result, dict) else "Not a dict")
    
    # Store venues in chat history for next call
    updated_chat_history = result.get("chat_history", chat_history or [])
    if "extracted_venues" in result and result["extracted_venues"]:
        # Add venues to chat history as a special message
        from langchain.schema import HumanMessage
        import json
        venues_json = json.dumps(result["extracted_venues"])
        venue_msg = HumanMessage(content=f"VENUES_STORED:{venues_json}")
        updated_chat_history.append(venue_msg)
    
    # Return output from the correct node
    if "risk_report" in result:
        print("Returning risk_report")
        return result["risk_report"], updated_chat_history
    elif "output" in result:
        print("Returning output")
        return result["output"], updated_chat_history
    else:
        print("No output found in result, returning error message")
        return "I apologize, but I encountered an error processing your request.", updated_chat_history 