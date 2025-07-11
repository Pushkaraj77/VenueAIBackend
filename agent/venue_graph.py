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
    chat_history = state.get("chat_history", [])

    # Use LLM to analyze the venue output and make decisions
    analysis_prompt = f"""
    You are the coordinator for a venue and risk assessment system. You have access to:
    - The user's original query
    - The chat history
    - The latest venue finder output (which may be empty or unhelpful)

    Your job is to decide what to do next.

    Possible actions:
    - "extract_venues": Present venue recommendations based on the user's requirements.
    - "risk_assessment": Perform a risk assessment for the specified venue(s) if the user is asking about risks, safety, or assessment and you have venue info (from the venue finder output).
    - "end": End the conversation if the user's needs are fully met or they indicate they are done.

    Rules:
    - If the user asks for both venue recommendations and risk assessment in the same query, always perform the venue search first, present the venue options, and only then offer risk assessment. Do not proceed to risk assessment until venues have been found and presented.
    - Do NOT select 'risk_assessment' unless the venue finder output contains real venues (not just info extracted from the user's query).
    - If the user's query is about risk, safety, or assessment, and you can extract a venue name and location, and at least one of date or expected attendance from the venue finder output, choose "risk_assessment".
    - Only ask for more info if BOTH the date and expected attendance are missing.
    - If the user provides location, event type, capacity, and a time frame (even if vague, like 'next week'), proceed to venue search.
    - Only ask for more info if a truly critical detail is missing.
    - If the user is asking for venues or for recommendations, choose "extract_venues".
    - If the conversation is complete, choose "end".

    IMPORTANT: Do NOT select 'risk_assessment' as the first action unless the venue finder output contains real venues. If the user has not asked for risk assessment, and venues have been found, your action should be 'end' and you should present the venue list to the user. You may choose 'risk_assessment' ONLY after venues have been found and presented.

    Respond with ONLY a JSON object:
    {{
      "action": "...",
      "reasoning": "...",
      "venues": [
        {{
          "name": "Venue Name",
          "location": "Specific Location",
          "type": "Venue Type",
          "features": "Key Features"
        }}
      ]
    }}
    User's original query: {input_text}
    Chat history: {chat_history}
    Venue finder output: {venue_output}
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
                "action": "extract_venues",
                "reasoning": "Could not parse LLM response",
                "venues": []
            }

        print(f"LLM Analysis Result: {analysis_result}")

        # --- FIX: If LLM returns risk_assessment but venue_output is empty or has no venues, override to extract_venues ---
        action = analysis_result.get("action", "extract_venues")
        venues = analysis_result.get("venues", [])
        if action == "risk_assessment":
            # Only override if both venues is empty and venue_output is empty/whitespace
            if (not venue_output.strip()) and (not venues or all(v.get('name', '').lower() == 'unknown' for v in venues)):
                analysis_result["action"] = "extract_venues"
                print("Overriding action to 'extract_venues' because no real venues found in venue_output and venues list is empty.")

        # Update state with analysis results
        state.update({
            "llm_analysis": analysis_result,
            "extracted_venues": analysis_result.get("venues", []),
            "next_action": analysis_result.get("action", "extract_venues")
        })

        return state

    except Exception as e:
        print(f"Error in LLM venue analysis: {e}")
        # Fallback to asking for info
        state.update({
            "llm_analysis": {"action": "extract_venues", "reasoning": "Error in analysis", "venues": []},
            "extracted_venues": [],
            "next_action": "extract_venues"
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

# --- Utility to merge requirements from chat history and current input ---
def merge_requirements_from_history(chat_history, current_input):
    """
    Merge structured requirements from previous user messages in chat_history with the current_input.
    The current_input takes precedence for any new/overriding requirements.
    Returns a single merged string for the venue finder.
    """
    import re
    # Collect previous user messages (excluding system/agent messages)
    user_msgs = []
    for msg in reversed(chat_history):
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            # Heuristic: skip agent/system messages
            if not msg.content.strip().lower().startswith(("okay", "i can help", "here are", "i have searched", "would you like", "thank you", "no venues were found")):
                user_msgs.append(msg.content.strip())
        if len(user_msgs) >= 3:
            break
    # Try to find the most recent message with lots of requirements
    best_msg = ""
    for m in user_msgs:
        # Heuristic: look for numbers, dates, or keywords
        if re.search(r"\d{2,}", m) or any(word in m.lower() for word in ["people", "attendees", "capacity", "budget", "date", "event", "workshop", "conference", "wedding", "banquet", "resort", "hotel", "catering", "wifi", "room", "hall", "outdoor", "parking"]):
            best_msg = m
            break
    # Merge: combine best previous message with current input, with current input last (so it can override)
    if best_msg and best_msg != current_input:
        merged = best_msg + ". " + current_input
    else:
        merged = current_input
    return merged


def handle_venue_finding(state: dict) -> dict:
    llm = state["llm"]
    input_text = state["input"]
    chat_history = state.get("chat_history", [])
    
    print("Step 1: Finding venues")
    
    # --- Use merged requirements for follow-up queries ---
    merged_input = merge_requirements_from_history(chat_history, input_text)
    
    # Step 1: Find venues
    venue_state = {
        "llm": llm,
        "input": merged_input,
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
            "input": merged_input
        }
        
        analysis_result = intelligent_venue_processor_node(analysis_state)
        next_action = analysis_result.get("next_action", "extract_venues")
        extracted_venues = analysis_result.get("extracted_venues", [])
        
        print(f"LLM decided next action: {next_action}")
        print(f"Extracted venues: {[v.get('name', 'Unknown') for v in extracted_venues]}")
        
        # Only show risk assessment option if venues are found
        venue_section = f"## Venue Recommendations\n{venue_output}\n"
        if extracted_venues:
            venue_section += f"\n## Risk Assessment Option\n\nI found {len(extracted_venues)} venues that match your requirements. Would you like me to perform a detailed risk assessment for these venues?\n\n**Available venues:**\n"
            for i, venue in enumerate(extracted_venues, 1):
                venue_section += f"{i}. **{venue.get('name', 'Unknown')}** - {venue.get('location', 'Unknown')}\n"
            # Removed the block that adds detailed instructions for requesting risk assessment
        else:
            # Only show fallback if venue_output is empty or whitespace
            if not venue_output.strip():
                # Check if user is asking for more options
                if any(phrase in input_text.lower() for phrase in ["more options", "more venues", "show more", "additional venues", "other options"]):
                    venue_section += "\nI couldn't find any more venues matching your criteria. Would you like to adjust your requirements or search in a wider area?"
                else:
                    venue_section += "\nNo venues were found that match your requirements. Please provide more details or adjust your criteria."
        return {
            **state,
            "output": venue_section,
            "chat_history": venue_chat_history,
            "extracted_venues": extracted_venues
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

        # Check for venue names mentioned (allow partial, case-insensitive match)
        input_lower = input_text.lower()
        for venue in extracted_venues:
            venue_name = venue.get('name', '').lower()
            if venue_name in input_lower or venue_name.split()[0] in input_lower or any(part in input_lower for part in venue_name.split()):
                if venue not in venues_to_assess:
                    venues_to_assess.append(venue)
            elif any(input_part in venue_name for input_part in input_lower.split()):
                if venue not in venues_to_assess:
                    venues_to_assess.append(venue)

        # If no specific venues found, ask for clarification
        if not venues_to_assess:
            venue_list = "\n".join([f"{i+1}. {venue.get('name', 'Unknown')}" for i, venue in enumerate(extracted_venues)])
            return {
                **state,
                "output": f"""I'm not sure which venues you'd like me to assess for risks. \n\n{venue_list}\n\nPlease specify which venues you'd like me to assess by responding with:\n- \"All venues\" or \"Yes\" - for all venues\n- \"Venue 1\" or \"The Leela\" - for specific venue(s)\n- Venue numbers like \"1 and 3\" or \"first and third\"""" ,
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

def orchestrator_node(state: dict) -> dict:
    """LLM-driven orchestrator: decides which agent to call next based on user query and chat history."""
    llm = state["llm"]
    input_text = state["input"]
    chat_history = state.get("chat_history", [])
    
    orchestrator_prompt = f"""
    You are the orchestrator for a venue and risk assessment system.
    
    Given:
    - The user's latest message
    - The full chat history
    
    Decide which action to take next. Possible actions:
    - "venue_finder": Search for venues based on the user's requirements.
    - "risk_assessment": Assess risks for a specified venue.
    - "end": End the conversation.
    
    Rules:
    - If the user asks for both venue recommendations and risk assessment in the same query, always perform the venue search first, present the venue options, and then ask if the user wants a risk assessment for any or all of the venues. Do not proceed to risk assessment until venues have been found and presented.
    - If the user asks about risks and provides a venue, location, and date, choose "risk_assessment".
    - If the user asks for venues, choose "venue_finder".
    - If the conversation is complete, choose "end".
    
    Respond with ONLY a JSON object:
    {{
      "action": "...",
      "reasoning": "...",
      "venues": [
        {{
          "name": "Venue Name",
          "location": "Specific Location",
          "type": "Venue Type",
          "features": "Key Features"
        }}
      ]
    }}
    User's message: {input_text}
    Chat history: {chat_history}
    """
    try:
        response = llm.invoke(orchestrator_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        import json, re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            orchestration = json.loads(json_match.group())
        else:
            orchestration = {"action": "venue_finder", "reasoning": "Could not parse LLM response", "venues": []}
        print(f"LLM Orchestrator Decision: {orchestration}")
        state.update({
            "orchestration": orchestration,
            "extracted_venues": orchestration.get("venues", []),
            "next_action": orchestration.get("action", "venue_finder")
        })
        return state
    except Exception as e:
        print(f"Error in LLM orchestrator: {e}")
        state.update({
            "orchestration": {"action": "venue_finder", "reasoning": "Error in orchestration", "venues": []},
            "extracted_venues": [],
            "next_action": "venue_finder"
        })
        return state

# Main entry point for the graph

def run_llm_orchestrated_graph(llm, input_text, chat_history=None):
    state = {
        "llm": llm,
        "input": input_text,
        "chat_history": chat_history or []
    }
    while True:
        # Let the LLM decide the next action based on user query and chat history
        analysis_state = {
            "llm": llm,
            "input": state["input"],
            "chat_history": state["chat_history"],
            "venue_output": state.get("venue_output", "")
        }
        analysis_result = intelligent_venue_processor_node(analysis_state)
        next_action = analysis_result.get("next_action", "venue_finder")
        extracted_venues = analysis_result.get("extracted_venues", [])
        print(f"LLM decided next action: {next_action}")
        print(f"Extracted venues: {[v.get('name', 'Unknown') for v in extracted_venues]}")

        # --- FIX: Always show venues before risk assessment if none found yet ---
        if next_action == "risk_assessment" and not extracted_venues:
            # No real venues yet, so do venue finding first
            next_action = "venue_finder"

        if next_action in ["venue_finder", "extract_venues"]:
            # Use handle_venue_finding to get venue recommendations
            venue_state = {
                "llm": llm,
                "input": state["input"],
                "chat_history": state["chat_history"]
            }
            venue_result = handle_venue_finding(venue_state)
            state["output"] = venue_result.get("output", "")
            state["chat_history"] = venue_result.get("chat_history", state["chat_history"])
            state["venue_output"] = state["output"]
            # After venue finding, show the venue output to the user and break (do not loop back to LLM)

            # --- NEW: If the original query asks for both recommendations and risk, immediately follow with risk assessment ---
            user_query_lower = state["input"].lower()
            risk_keywords = ["risk", "risks", "safety", "safe", "assessment", "flood", "weather"]
            venue_keywords = ["venue", "venues", "recommend", "suggest", "find", "conference", "banquet", "resort", "hotel", "hall"]
            asks_for_risk = any(word in user_query_lower for word in risk_keywords)
            asks_for_venue = any(word in user_query_lower for word in venue_keywords)
            venues_found = venue_result.get("extracted_venues", [])
            if asks_for_risk and asks_for_venue and venues_found:
                # Perform risk assessment for all found venues and append to output
                risk_state = {
                    **state,
                    "extracted_venues": venues_found
                }
                risk_result = handle_risk_assessment_request(risk_state)
                risk_output = risk_result.get("output", "")
                state["output"] += "\n\n---\n\n" + risk_output
            break
        elif next_action == "risk_assessment":
            state["extracted_venues"] = extracted_venues
            risk_result = handle_risk_assessment_request(state)
            state["output"] = risk_result.get("output", "")
            state["chat_history"] = risk_result.get("chat_history", state["chat_history"])
            break
        elif next_action == "end":
            state["output"] = "Thank you for using the Venue Finder and Risk Assessment system. If you have more questions, feel free to ask!"
            break
        else:
            state["output"] = "I'm not sure how to proceed. Could you clarify your request?"
            break
    return state["output"], state["chat_history"]

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