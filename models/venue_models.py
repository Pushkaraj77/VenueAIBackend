from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    CORPORATE = "corporate"
    WEDDING = "wedding"
    PARTY = "party"
    SEMINAR = "seminar"
    CONFERENCE = "conference"
    TEAM_OFFSITE = "team_offsite"
    PRODUCT_LAUNCH = "product_launch"

class FoodPreference(str, Enum):
    VEG = "veg"
    NON_VEG = "non_veg"
    BOTH = "both"

class Amenity(str, Enum):
    PARKING = "parking"
    CATERING = "catering"
    WIFI = "wifi"
    AUDIO_VISUAL = "audio_visual"
    AIR_CONDITIONING = "air_conditioning"
    OUTDOOR_SPACE = "outdoor_space"
    POOL = "pool"
    GYM = "gym"
    SPA = "spa"
    SCENIC_VIEW = "scenic_view"
    BUSINESS_LOUNGE = "business_lounge"
    CENTRAL_LOCATION = "central_location"

class Venue(BaseModel):
    venue_id: str = Field(..., description="Unique identifier for the venue")
    name: str = Field(..., description="Name of the venue")
    location: str = Field(..., description="Location of the venue")
    city: str = Field(..., description="City where the venue is located")
    capacity: int = Field(..., description="Maximum capacity of the venue")
    price_per_day: float = Field(..., description="Price per day in INR")
    amenities: List[Amenity] = Field(default_factory=list, description="Available amenities")
    event_types: List[EventType] = Field(..., description="Types of events supported")
    food_preferences: List[FoodPreference] = Field(..., description="Food preferences supported")
    contact_number: str = Field(..., description="Contact number for the venue")
    email: Optional[str] = Field(None, description="Email address for the venue")
    description: Optional[str] = Field(None, description="Detailed description of the venue")
    images: Optional[List[str]] = Field(None, description="List of image URLs")
    rating: Optional[float] = Field(None, description="Venue rating out of 5")
    reviews: Optional[List[str]] = Field(None, description="List of reviews")
    available_dates: Dict[str, datetime] = Field(..., description="Available dates for booking")

class VenueSearchCriteria(BaseModel):
    location: Optional[str] = Field(None, description="Location to search in")
    start_date: Optional[datetime] = Field(None, description="Start date for the event")
    end_date: Optional[datetime] = Field(None, description="End date for the event")
    min_capacity: Optional[int] = Field(None, description="Minimum capacity required")
    max_capacity: Optional[int] = Field(None, description="Maximum capacity required")
    event_type: Optional[EventType] = Field(None, description="Type of event")
    food_preference: Optional[FoodPreference] = Field(None, description="Food preference")
    min_price: Optional[float] = Field(None, description="Minimum price per day")
    max_price: Optional[float] = Field(None, description="Maximum price per day")
    required_amenities: Optional[List[Amenity]] = Field(None, description="Required amenities")

class VenueSearchResponse(BaseModel):
    venues: List[Venue] = Field(..., description="List of matching venues")
    total_count: int = Field(..., description="Total number of matching venues")
    page: int = Field(..., description="Current page number")
    total_pages: int = Field(..., description="Total number of pages")

class VenueComparison(BaseModel):
    venue1: Venue = Field(..., description="First venue to compare")
    venue2: Venue = Field(..., description="Second venue to compare")
    comparison_points: List[str] = Field(..., description="Points of comparison")
    recommendation: Optional[str] = Field(None, description="Recommendation based on comparison") 