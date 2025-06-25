import random
from faker import Faker
from models.database import SessionLocal, Venue, Amenity, EventType, Purpose, AvailableDate, Base, engine
from datetime import timedelta, date

fake = Faker()

# Predefined lists for random selection
amenities_list = ["Wi-Fi", "Parking", "Catering", "AV", "Accommodation", "Pool", "Gym", "Spa"]
event_types_list = ["Corporate", "Social", "Wedding", "Conference", "Seminar", "Birthday"]
purposes_list = ["Seminars", "Conference", "Birthday Party", "Product Launch", "Team Offsite", "Wedding", "Reception"]

def random_amenities(session):
    return random.sample(session.query(Amenity).all(), k=random.randint(2, 5))

def random_event_types(session):
    return random.sample(session.query(EventType).all(), k=random.randint(1, 3))

def random_purposes(session):
    return random.sample(session.query(Purpose).all(), k=random.randint(1, 3))

def random_dates():
    start = fake.date_between(start_date=date(2025, 1, 1), end_date=date(2025, 12, 1))
    end = start + timedelta(days=random.randint(1, 30))
    return start, end

def main():
    session = SessionLocal()

    # Ensure amenities, event types, and purposes exist
    for name in amenities_list:
        if not session.query(Amenity).filter_by(name=name).first():
            session.add(Amenity(name=name))
    for name in event_types_list:
        if not session.query(EventType).filter_by(name=name).first():
            session.add(EventType(name=name))
    for name in purposes_list:
        if not session.query(Purpose).filter_by(name=name).first():
            session.add(Purpose(name=name))
    session.commit()

    # Find the max existing venue_id number
    existing_ids = session.query(Venue.venue_id).all()
    existing_nums = [int(v[0][1:]) for v in existing_ids if v[0].startswith('V') and v[0][1:].isdigit()]
    start_num = max(existing_nums) + 1 if existing_nums else 1000

    for i in range(1000):
        venue = Venue(
            venue_id=f"V{start_num + i:04d}",
            name=fake.company() + " Venue",
            location=fake.city(),
            capacity=random.randint(20, 1000),
            price_per_day=random.randint(50000, 1000000),
            contact_number=fake.phone_number()[:20],
            description=fake.sentence(nb_words=12),
            has_veg=random.choice([True, False]),
            has_non_veg=random.choice([True, False]),
        )
        session.add(venue)
        session.commit()  # Commit to get the venue.id

        # Add relationships
        venue.amenities = random_amenities(session)
        venue.event_types = random_event_types(session)
        venue.purposes = random_purposes(session)
        # Add available dates
        for _ in range(random.randint(1, 3)):
            start, end = random_dates()
            session.add(AvailableDate(venue_id=venue.id, start_date=start, end_date=end))
        session.commit()

        if (i+1) % 100 == 0:
            print(f"Inserted {i+1} venues...")

    session.close()
    print("Done inserting dummy venues.")

if __name__ == "__main__":
    main() 