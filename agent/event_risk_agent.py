import os
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
import re
from typing import List, Dict

# --- Venue parsing function (DEPRECATED - Now using LLM-based extraction) ---
# This function is kept for backward compatibility but is no longer used
# The intelligent_venue_processor_node in venue_graph.py now handles venue extraction using LLM

# --- Direct risk assessment function for individual venues ---
def assess_venue_risks_directly(llm, venue_info: Dict, time_period=""):
    """Assess risks for a specific venue with targeted, venue-specific searches."""
    
    venue_name = venue_info.get('name', 'Unknown Venue')
    venue_location = venue_info.get('location', 'Unknown')
    
    # Create search wrapper
    search = GoogleSerperAPIWrapper()
    
    try:
        print(f"Starting venue-specific risk assessment for {venue_name}")
        
        # Make targeted searches for venue-specific risks
        risk_reports = {}
        
        # 1. Weather risks - search for current weather alerts and forecasts for the specific venue area
        weather_query = f"current weather alerts warnings {venue_name} {venue_location} {time_period} monsoon rain flood heat wave"
        print(f"Searching for weather risks: {weather_query}")
        weather_results = search.run(weather_query)
        
        # 2. Political/security risks - search for recent incidents, protests, or security issues near the venue
        security_query = f"recent incidents protests security issues crime {venue_name} {venue_location} last week month"
        print(f"Searching for security risks: {security_query}")
        security_results = search.run(security_query)
        
        # 3. Health risks - search for health alerts, disease outbreaks, or health-related issues in the venue area
        health_query = f"health alerts disease outbreak COVID dengue health issues {venue_name} {venue_location} current"
        print(f"Searching for health risks: {health_query}")
        health_results = search.run(health_query)
        
        # 4. Logistical risks - search for traffic, construction, road closures, or infrastructure issues affecting the venue
        logistics_query = f"traffic construction road closure infrastructure issues parking {venue_name} {venue_location} current"
        print(f"Searching for logistical risks: {logistics_query}")
        logistics_results = search.run(logistics_query)
        
        # 5. Event conflicts - search for conflicting events, VIP movements, or major events near the venue
        events_query = f"upcoming events VIP movement Prime Minister rally concert festival {venue_name} {venue_location} {time_period}"
        print(f"Searching for event conflicts: {events_query}")
        events_results = search.run(events_query)
        
        print(f"Completed targeted searches for {venue_name}")
        
        # Create comprehensive venue-specific risk analysis prompt
        risk_analysis_prompt = f"""
        You are an Event Risk Assessment AI specializing in venue-specific risk analysis. Analyze the following targeted search results and create a detailed, venue-specific risk assessment for: {venue_name} in {venue_location}.

        **VENUE-SPECIFIC SEARCH RESULTS:**

        **Weather & Environmental Risks:**
        {weather_results}

        **Security & Political Risks:**
        {security_results}

        **Health & Safety Risks:**
        {health_results}

        **Logistical & Infrastructure Risks:**
        {logistics_results}

        **Event Conflicts & VIP Movements:**
        {events_results}

        **INSTRUCTIONS:**
        Create a venue-specific risk assessment that focuses ONLY on actual, current risks found in the search results. Do NOT provide generic advice. Instead:

        1. **Weather Risks**: Mention specific weather alerts, monsoon warnings, heat waves, or flood risks for this venue's exact location
        2. **Political/Security Risks**: Report any recent incidents, protests, security threats, or political activities near this venue
        3. **Health Risks**: Identify any current health alerts, disease outbreaks, or health-related issues affecting this venue area
        4. **Logistical Risks**: Report specific traffic issues, construction work, road closures, or infrastructure problems affecting access to this venue
        5. **Event Conflicts**: Identify any conflicting events, VIP movements, rallies, or major events that could impact this venue

        **For each risk category:**
        - If specific risks are found: Describe them in detail with exact dates, locations, and impacts
        - If no specific risks are found: State "No specific risks identified for this venue" and assign score 1
        - Provide actionable, venue-specific recommendations
        - Assign a risk score (1-10) based on the severity of actual risks found
        - Include specific mitigation strategies for the identified risks

        **Format your response as:**
        ## Risk Assessment: {venue_name}, {venue_location}

        **1. Weather Risks (Score: X/10)**
        [Specific weather alerts/risks for this venue]

        **2. Political/Security Risks (Score: X/10)**
        [Specific security incidents/political activities near this venue]

        **3. Health Risks (Score: X/10)**
        [Specific health alerts/disease outbreaks affecting this venue area]

        **4. Logistical Risks (Score: X/10)**
        [Specific traffic/construction/infrastructure issues affecting this venue]

        **5. Event Conflicts (Score: X/10)**
        [Specific conflicting events/VIP movements near this venue]

        **Overall Risk Assessment:**
        [Summary of the most critical venue-specific risks]

        **Venue-Specific Recommendations:**
        [Actionable recommendations based on the actual risks found]
        """
        
        # Get venue-specific risk analysis from LLM
        risk_analysis = llm.invoke(risk_analysis_prompt)
        risk_report = risk_analysis.content if hasattr(risk_analysis, 'content') else str(risk_analysis)
        
        return risk_report
        
    except Exception as e:
        print(f"Error in venue-specific risk assessment for {venue_name}: {str(e)}")
        return f"""## Risk Assessment: {venue_name}, {venue_location}

**Error in Risk Assessment:**
I encountered an error while conducting venue-specific risk assessment: {str(e)}

**Recommendation:**
Please consult local authorities, venue management, or recent news sources for current risk information specific to this venue.

**Alternative Sources:**
- Contact the venue directly for current safety information
- Check local police department for recent incidents
- Monitor local weather services for venue-specific alerts
- Review recent news coverage of the venue area"""

# --- Calculate venue risk score ---
def calculate_venue_score(risk_report: str) -> Dict:
    """Extract risk scores from risk report and calculate overall venue score."""
    try:
        # Look for risk scores in the report
        score_pattern = r'(\d+)/10'
        scores = re.findall(score_pattern, risk_report)
        
        if scores:
            # Convert to integers and calculate average
            risk_scores = [int(score) for score in scores]
            average_score = sum(risk_scores) / len(risk_scores)
            
            # Calculate risk level based on average score
            if average_score <= 3:
                risk_level = "Low"
            elif average_score <= 6:
                risk_level = "Medium"
            else:
                risk_level = "High"
            
            return {
                'average_score': round(average_score, 1),
                'risk_level': risk_level,
                'individual_scores': risk_scores
            }
        else:
            return {
                'average_score': 5.0,  # Default medium risk
                'risk_level': "Medium",
                'individual_scores': [5, 5, 5, 5, 5]
            }
    except Exception as e:
        print(f"Error calculating venue score: {e}")
        return {
            'average_score': 5.0,
            'risk_level': "Medium",
            'individual_scores': [5, 5, 5, 5, 5]
        }

# --- Direct risk assessment function ---
def assess_risks_directly(llm, location, time_period=""):
    """Direct risk assessment without using agent framework to avoid Gemini API issues."""
    
    # Create search wrapper
    search = GoogleSerperAPIWrapper()
    
    try:
        # Make comprehensive search for risks
        search_query = f"weather political health security logistical risks events {location} {time_period}"
        print(f"Searching for risks with query: {search_query}")
        
        search_results = search.run(search_query)
        print(f"Search completed, results length: {len(search_results)}")
        
        # Create prompt for risk analysis
        risk_analysis_prompt = f"""
        You are an Event Risk Assessment AI. Analyze the following web search results and create a comprehensive risk assessment for an event in {location}.

        Web Search Results:
        {search_results}

        Please create a structured risk assessment report with the following sections:
        1. Weather Risks (with risk level: Low/Medium/High)
        2. Political Risks (with risk level: Low/Medium/High)  
        3. Health Risks (with risk level: Low/Medium/High)
        4. Security Risks (with risk level: Low/Medium/High)
        5. Logistical Risks (with risk level: Low/Medium/High)

        For each risk category:
        - Summarize the key risks found
        - Provide actionable recommendations
        - Include mitigation strategies

        If no specific risks are found for a category, state that explicitly.
        Format your response in clear Markdown with proper headers and bullet points.
        """
        
        # Get risk analysis from LLM
        risk_analysis = llm.invoke(risk_analysis_prompt)
        risk_report = risk_analysis.content if hasattr(risk_analysis, 'content') else str(risk_analysis)
        
        return risk_report
        
    except Exception as e:
        print(f"Error in direct risk assessment: {str(e)}")
        return f"## Event Risk Assessment for {location}\n\nI encountered an error while assessing risks: {str(e)}\n\nPlease consult local authorities for current risk information."

# --- LangGraph node function ---
def event_risk_assessment_node(state: dict) -> dict:
    """LangGraph node for event risk assessment using direct web search approach."""
    if "llm" not in state:
        raise ValueError("LLM not found in state! State keys: " + str(list(state.keys())))
    
    llm = state["llm"]
    input_text = state["input"]
    chat_history = state.get("chat_history", [])
    
    print(f"Starting direct risk assessment for: {input_text}")
    
    try:
        # Extract location and time from input
        # Simple extraction - look for common patterns
        import re
        
        # Common Indian cities
        cities = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow"]
        location = "Unknown"
        
        for city in cities:
            if city.lower() in input_text.lower():
                location = city
                break
        
        # Extract time period if mentioned
        time_period = ""
        time_patterns = ["next week", "this week", "next month", "tomorrow", "today"]
        for pattern in time_patterns:
            if pattern in input_text.lower():
                time_period = pattern
                break
        
        print(f"Extracted location: {location}, time period: {time_period}")
        
        if location == "Unknown":
            risk_report = "## Event Risk Assessment\n\nUnable to determine the location from your query. Please specify the city/location for a proper risk assessment."
        else:
            # Perform direct risk assessment
            risk_report = assess_risks_directly(llm, location, time_period)
        
        # Update chat history with the interaction
        updated_chat_history = chat_history + [
            HumanMessage(content=input_text),
            HumanMessage(content=risk_report)
        ]
        
        return {
            **state,
            "risk_report": risk_report,
            "chat_history": updated_chat_history
        }
        
    except Exception as e:
        print(f"Error in event risk assessment node: {str(e)}")
        error_report = f"## Event Risk Assessment\n\nI apologize, but I encountered an error while assessing event risk: {str(e)}"
        
        return {
            **state,
            "risk_report": error_report,
            "chat_history": chat_history
        } 

def batch_assess_venue_risks(llm, venues_info: List[Dict], time_period=""):
    """Batch risk assessment for multiple venues in a single LLM call."""
    search = GoogleSerperAPIWrapper()
    all_venue_data = []
    for venue in venues_info:
        venue_name = venue.get('name', 'Unknown Venue')
        venue_location = venue.get('location', 'Unknown')
        # Do web searches as before
        weather_results = search.run(f"current weather alerts warnings {venue_name} {venue_location} {time_period} monsoon rain flood heat wave")
        security_results = search.run(f"recent incidents protests security issues crime {venue_name} {venue_location} last week month")
        health_results = search.run(f"health alerts disease outbreak COVID dengue health issues {venue_name} {venue_location} current")
        logistics_results = search.run(f"traffic construction road closure infrastructure issues parking {venue_name} {venue_location} current")
        events_results = search.run(f"upcoming events VIP movement Prime Minister rally concert festival {venue_name} {venue_location} {time_period}")
        all_venue_data.append({
            "name": venue_name,
            "location": venue_location,
            "weather": weather_results,
            "security": security_results,
            "health": health_results,
            "logistics": logistics_results,
            "events": events_results
        })
    # Build a single prompt
    prompt = "You are an Event Risk Assessment AI. For each venue below, analyze the search results and provide a risk assessment and risk score (1-10):\n\n"
    for i, v in enumerate(all_venue_data, 1):
        prompt += f"Venue {i}: {v['name']} ({v['location']})\n"
        prompt += f"Weather: {v['weather']}\n"
        prompt += f"Security: {v['security']}\n"
        prompt += f"Health: {v['health']}\n"
        prompt += f"Logistics: {v['logistics']}\n"
        prompt += f"Events: {v['events']}\n\n"
    prompt += "For each venue, provide:\n- A risk assessment by category\n- An overall risk score (1-10)\n- A summary and recommendations\n"
    # Single LLM call
    result = llm.invoke(prompt)
    return result.content if hasattr(result, 'content') else str(result) 