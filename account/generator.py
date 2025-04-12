"""
User data generation for account creation
"""

import random
import logging
import datetime
import uuid
from config import CONFIG
from utils.helpers import generate_strong_password, days_in_month

logger = logging.getLogger("FBAccountCreator")

class AccountGenerator:
    def __init__(self):
        """Initialize the account generator"""
        self.device_id = str(uuid.uuid4())
        self.account_data = {}
        
    def generate_user_data(self):
        """Generate random user information for account creation"""
        # Generate random first and last names - more diverse list
        first_names = [
            # Gender-neutral names
            "Alex", "Jordan", "Taylor", "Casey", "Riley", "Avery", "Quinn", "Jamie", 
            "Morgan", "Reese", "Bailey", "Skyler", "Sam", "Hayden", "Blake", "Dakota", 
            "Jules", "Elliot", "Remy", "Charlie", "Emerson", "Phoenix", "River", "Sage",
            
            # More traditionally gendered names for variety
            "Emma", "Olivia", "Sophia", "Ava", "Isabella", "Mia", "Charlotte", 
            "Liam", "Noah", "William", "James", "Benjamin", "Lucas", "Henry",
            
            # International names for diversity
            "Aiden", "Sofia", "Mateo", "Aria", "Elijah", "Maya", "Ethan", "Zoe"
        ]
        
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
            "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", 
            "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", 
            "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
            "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green"
        ]
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        # Generate a birthdate (18-45 years old)
        current_year = datetime.datetime.now().year
        min_age = CONFIG.get("min_age", 19)
        max_age = CONFIG.get("max_age", 45)
        birth_year = random.randint(current_year - max_age, current_year - min_age)
        birth_month = random.randint(1, 12)
        
        # Determine max days based on month
        max_days = days_in_month(birth_month, birth_year)
        birth_day = random.randint(1, max_days)
        
        # Generate random gender (for Facebook's form)
        gender = random.choice(["1", "2"])  # 1 for female, 2 for male
        
        # Generate a strong random password
        password_length = CONFIG.get("password_length", 12)
        password = generate_strong_password(password_length)
        
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "birth_year": birth_year,
            "birth_month": birth_month,
            "birth_day": birth_day,
            "gender": gender,
            "password": password,
            "device_id": self.device_id
        }
        
        self.account_data = user_data
        return user_data