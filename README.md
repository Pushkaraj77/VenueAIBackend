# VenueAI - Intelligent Venue Finder

VenueAI is an intelligent venue finder agent that helps users discover and evaluate venues based on their specific requirements. The system uses advanced AI capabilities to understand user preferences and provide personalized venue recommendations.

## Features

- Natural language understanding of venue requirements
- Multi-criteria venue search and filtering
- Venue comparison and analysis
- Location-based recommendations
- Detailed venue information and insights
- User preference learning and adaptation

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## Project Structure

- `main.py`: FastAPI application entry point
- `agent/`: Core AI agent implementation
  - `venue_agent.py`: Main venue finder agent
  - `tools.py`: Custom tools for venue search
- `models/`: Data models and schemas
- `utils/`: Utility functions
- `config/`: Configuration files

## API Endpoints

- `POST /api/venue/search`: Search for venues based on requirements
- `GET /api/venue/{venue_id}`: Get detailed venue information
- `POST /api/venue/compare`: Compare multiple venues
- `GET /api/venue/recommendations`: Get personalized venue recommendations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 