from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from agent.venue_agent import VenueFinderAgent
from models.venue_models import VenueSearchCriteria, VenueSearchResponse, VenueComparison
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(
    title="VenueAI API",
    description="AI-powered venue finder and recommendation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    convert_system_message_to_human=True
)

# Initialize the venue finder agent
venue_agent = VenueFinderAgent(llm)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return the agent's response."""
    try:
        response = venue_agent.process_query(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/venue/search", response_model=VenueSearchResponse)
async def search_venues(criteria: VenueSearchCriteria):
    """Search for venues based on the provided criteria."""
    try:
        # Convert criteria to a natural language query
        query = f"Find venues in {criteria.location} for {criteria.event_type} event "
        query += f"from {criteria.start_date} to {criteria.end_date} "
        query += f"with capacity {criteria.min_capacity} to {criteria.max_capacity} "
        query += f"and {criteria.food_preference} food options"
        response = venue_agent.process_query(query)
        # TODO: Parse response and convert to VenueSearchResponse
        return VenueSearchResponse(
            venues=[],
            total_count=0,
            page=1,
            total_pages=1
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/venue/{venue_id}")
async def get_venue_details(venue_id: str):
    """Get detailed information about a specific venue."""
    try:
        response = venue_agent.process_query(f"Get details for venue {venue_id}")
        # TODO: Parse response and return venue details
        return {"message": "Venue details retrieved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/venue/compare")
async def compare_venues(venue_ids: List[str]):
    """Compare multiple venues."""
    try:
        response = venue_agent.process_query(f"Compare venues {', '.join(venue_ids)}")
        # TODO: Parse response and return comparison
        return {"message": "Venue comparison completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 