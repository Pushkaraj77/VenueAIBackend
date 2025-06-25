import streamlit as st
from agent.venue_agent import VenueFinderAgent
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Initialize the venue finder agent
@st.cache_resource
def get_agent():
    return VenueFinderAgent()

# Custom CSS for better UI
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #2b313e;
    }
    .chat-message.assistant {
        background-color: #1f2937;
    }
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 1rem;
    }
    .chat-message .content {
        flex: 1;
    }
    .stTextInput>div>div>input {
        background-color: #1f2937;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🏢 Venue Finder AI")
st.markdown("Find the perfect venue for your event!")

# Sidebar with information
with st.sidebar:
    st.header("About")
    st.markdown("""
    This AI assistant helps you find the perfect venue for your event. You can:
    - Search for venues by location, capacity, and more
    - Get detailed information about specific venues
    - Compare different venues
    - Get personalized recommendations
    """)
    
    st.header("Sample Queries")
    st.markdown("""
    Try asking:
    - "Find venues in Mumbai for a corporate event"
    - "Show me venues with capacity of 100 people"
    - "Compare venues in Bangalore"
    - "What are the best venues for a wedding?"
    """)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about venues..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                agent = get_agent()
                response = agent.process_query(prompt)
                
                # Format the response if it contains venue data
                if "venue_id" in response:
                    try:
                        venue_data = json.loads(response)
                        formatted_response = f"""
                        ### {venue_data['name']}
                        **Location:** {venue_data['location']}  
                        **Capacity:** {venue_data['capacity']} people  
                        **Price:** ₹{venue_data['price_per_day']}/day  
                        **Amenities:** {', '.join(venue_data['amenities'])}  
                        **Contact:** {venue_data['contact_number']}  
                        **Email:** {venue_data['email']}  
                        """
                        st.markdown(formatted_response)
                    except:
                        st.markdown(response)
                else:
                    st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit and LangChain") 