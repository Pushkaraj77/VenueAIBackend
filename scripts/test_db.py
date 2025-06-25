import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from models.database import SessionLocal, Venue
from sqlalchemy import text

def test_database_connection():
    """Test database connection and basic queries."""
    try:
        # Create a database session
        db = SessionLocal()
        
        # Test 1: Basic connection
        print("Test 1: Testing database connection...")
        result = db.execute(text("SELECT 1")).scalar()
        print(f"✓ Database connection successful! Result: {result}")
        
        # Test 2: Count venues
        print("\nTest 2: Counting venues...")
        venue_count = db.query(Venue).count()
        print(f"✓ Found {venue_count} venues in the database")
        
        # Test 3: List all venues
        print("\nTest 3: Listing all venues...")
        venues = db.query(Venue).all()
        for venue in venues:
            print(f"\nVenue: {venue.name}")
            print(f"  ID: {venue.venue_id}")
            print(f"  Capacity: {venue.capacity}")
            print(f"  Price: ₹{venue.price_per_day:,.2f}")
            print(f"  Amenities: {', '.join(a.name for a in venue.amenities)}")
            print(f"  Event Types: {', '.join(et.name for et in venue.event_types)}")
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    test_database_connection() 