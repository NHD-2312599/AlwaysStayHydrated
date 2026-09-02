"""
Initialize Flashcard database with sample data
Run this script once to populate the database: python init_flashcard_db.py
"""

import json
import re
import sys
sys.path.insert(0, '.')

from app import app
from flashcard_models import db, Tab, Card

def extract_default_data_from_html(html_file):
    """Extract DEFAULT_DATA from Flashcard HTML file"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find DEFAULT_DATA constant
        match = re.search(r'const DEFAULT_DATA = ({.*?});', content, re.DOTALL)
        if not match:
            print("❌ Could not find DEFAULT_DATA in HTML file")
            return None
        
        # Parse JSON
        data_str = match.group(1)
        data = json.loads(data_str)
        return data
    except Exception as e:
        print(f"❌ Error parsing HTML: {e}")
        return None


def init_database():
    """Initialize database with flashcard data"""
    with app.app_context():
        # Clear existing data
        CardStatus = None
        for model in [Card, Tab]:
            try:
                db.session.query(model).delete()
                db.session.commit()
            except:
                pass
        
        # Extract data from HTML
        print("📖 Reading Flashcard data from HTML file...")
        data = extract_default_data_from_html('Flashcard/index.html')
        
        if not data or 'tabs' not in data:
            print("❌ No valid data found. Using empty database.")
            print("   You can add tabs and cards through the admin interface.")
            return
        
        # Insert tabs and cards
        print(f"📚 Found {len(data['tabs'])} tabs")
        
        total_cards = 0
        for tab_data in data['tabs']:
            tab_id = tab_data.get('id', f't{len(Tab.query.all()) + 1}')
            tab_name = tab_data.get('name', 'Untitled')
            
            tab = Tab(id=tab_id, name=tab_name)
            db.session.add(tab)
            db.session.flush()
            
            # Add cards for this tab
            cards = tab_data.get('cards', [])
            for card_data in cards:
                card_id = card_data.get('id', f'c{total_cards + 1}')
                card = Card(
                    id=card_id,
                    tab_id=tab_id,
                    ref=card_data.get('ref', ''),
                    title=card_data.get('title', ''),
                    verse=card_data.get('verse', ''),
                    analysis=card_data.get('analysis', '')
                )
                db.session.add(card)
                total_cards += 1
            
            print(f"  ✓ Tab '{tab_name}': {len(cards)} cards")
        
        db.session.commit()
        print(f"\n✅ Database initialized successfully!")
        print(f"   - {len(data['tabs'])} tabs")
        print(f"   - {total_cards} cards")
        print(f"\n📍 Access at: http://localhost:5000/flashcard/login")
        print(f"   • Password 'dongan' for view-only access")
        print(f"   • Password 'donganadmin' for edit access")


if __name__ == '__main__':
    init_database()
