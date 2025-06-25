import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from models.database import SessionLocal, Venue, Amenity, EventType, Purpose, AvailableDate
from datetime import date

def init_db():
    db = SessionLocal()
    
    try:
        # Create amenities
        amenities = {
            "AV": Amenity(name="AV"),
            "Wi-Fi": Amenity(name="Wi-Fi"),
            "Parking": Amenity(name="Parking"),
            "Catering": Amenity(name="Catering"),
            "Accommodation": Amenity(name="Accommodation"),
            "Decor": Amenity(name="Decor")
        }
        for amenity in amenities.values():
            db.add(amenity)
        
        # Create event types
        event_types = {
            "Corporate": EventType(name="Corporate"),
            "Social": EventType(name="Social")
        }
        for event_type in event_types.values():
            db.add(event_type)
        
        # Create purposes
        purposes = {
            "Seminars": Purpose(name="Seminars"),
            "Conference": Purpose(name="Conference"),
            "Birthday Party": Purpose(name="Birthday Party"),
            "Product Launch": Purpose(name="Product Launch"),
            "Team Offsite": Purpose(name="Team Offsite"),
            "Wedding": Purpose(name="Wedding"),
            "Reception": Purpose(name="Reception"),
            "Engagement": Purpose(name="Engagement")
        }
        for purpose in purposes.values():
            db.add(purpose)
        
        db.commit()
        
        # Create venues
        venues_data = [
            {
                "venue_id": "V001",
                "name": "Lonavla Convention Center",
                "location": "Lonavla",
                "capacity": 500,
                "price_per_day": 350000,
                "contact_number": "9876543210",
                "description": "A modern convention center perfect for corporate events",
                "has_veg": True,
                "has_non_veg": True,
                "amenities": ["AV", "Wi-Fi", "Parking", "Catering"],
                "event_types": ["Corporate", "Social"],
                "purposes": ["Seminars", "Conference", "Product Launch"],
                "available_dates": [(date(2025, 7, 21), date(2025, 9, 15))]
            },
            {
                "venue_id": "V002",
                "name": "The Hillside Resort",
                "location": "Lonavla",
                "capacity": 200,
                "price_per_day": 420000,
                "contact_number": "9988776655",
                "description": "A scenic resort with modern amenities",
                "has_veg": True,
                "has_non_veg": True,
                "amenities": ["Wi-Fi", "Parking", "Catering", "Accommodation"],
                "event_types": ["Corporate", "Social"],
                "purposes": ["Team Offsite", "Conference", "Birthday Party"],
                "available_dates": [(date(2025, 8, 1), date(2025, 9, 19))]
            },
            {
                "venue_id": "V003",
                "name": "Lonavla Grand Ballroom",
                "location": "Lonavla",
                "capacity": 800,
                "price_per_day": 580000,
                "contact_number": "8899001122",
                "description": "An elegant ballroom for grand celebrations",
                "has_veg": True,
                "has_non_veg": True,
                "amenities": ["AV", "Wi-Fi", "Parking", "Catering", "Decor"],
                "event_types": ["Social"],
                "purposes": ["Wedding", "Reception", "Engagement"],
                "available_dates": [(date(2025, 7, 28), date(2025, 9, 10))]
            },
            {
                "venue_id": "V004",
                "name": "Serene Gardens",
                "location": "Lonavla",
                "capacity": 100,
                "price_per_day": 110000,
                "contact_number": "7766554433",
                "description": "A peaceful garden venue for intimate gatherings",
                "has_veg": True,
                "has_non_veg": False,
                "amenities": ["Wi-Fi", "Parking", "Catering"],
                "event_types": ["Social", "Corporate"],
                "purposes": ["Birthday Party", "Team Offsite", "Seminars"],
                "available_dates": [(date(2025, 7, 21), date(2025, 8, 31))]
            },
            {
                "venue_id": "V005",
                "name": "Summit Hall",
                "location": "Lonavla",
                "capacity": 80,
                "price_per_day": 200000,
                "contact_number": "6655443322",
                "description": "A modern conference hall for corporate events",
                "has_veg": True,
                "has_non_veg": True,
                "amenities": ["AV", "Wi-Fi", "Catering"],
                "event_types": ["Corporate"],
                "purposes": ["Conference", "Seminars", "Product Launch"],
                "available_dates": [(date(2025, 8, 5), date(2025, 9, 19))]
            },
            {
                "venue_id": "V006",
                "name": "Green Valley Resort",
                "location": "Lonavla",
                "capacity": 150,
                "price_per_day": 300000,
                "contact_number": "5544332211",
                "description": "A scenic resort with modern facilities",
                "has_veg": True,
                "has_non_veg": True,
                "amenities": ["Parking", "Catering", "Accommodation"],
                "event_types": ["Social"],
                "purposes": ["Wedding", "Reception", "Birthday Party"],
                "available_dates": [(date(2025, 7, 21), date(2025, 9, 19))]
            }
        ]
        
        for venue_data in venues_data:
            venue = Venue(
                venue_id=venue_data["venue_id"],
                name=venue_data["name"],
                location=venue_data["location"],
                capacity=venue_data["capacity"],
                price_per_day=venue_data["price_per_day"],
                contact_number=venue_data["contact_number"],
                description=venue_data["description"],
                has_veg=venue_data["has_veg"],
                has_non_veg=venue_data["has_non_veg"]
            )
            
            # Add amenities
            for amenity_name in venue_data["amenities"]:
                venue.amenities.append(amenities[amenity_name])
            
            # Add event types
            for event_type_name in venue_data["event_types"]:
                venue.event_types.append(event_types[event_type_name])
            
            # Add purposes
            for purpose_name in venue_data["purposes"]:
                venue.purposes.append(purposes[purpose_name])
            
            # Add available dates
            for start_date, end_date in venue_data["available_dates"]:
                venue.available_dates.append(
                    AvailableDate(start_date=start_date, end_date=end_date)
                )
            
            db.add(venue)
        
        db.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 