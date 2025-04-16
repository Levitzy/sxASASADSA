"""
Enhanced user data generation for account creation
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
        """Generate random user information for account creation that looks natural"""
        # Generate random first and last names - ensuring consistent gender
        first_name, gender = self._get_gender_appropriate_name()
        last_name = self._get_realistic_last_name()
        
        # Generate a realistic birthdate (25-50 years old for better acceptance)
        current_year = datetime.datetime.now().year
        min_age = CONFIG.get("min_age", 25)  # Increased minimum age 
        max_age = CONFIG.get("max_age", 50)  # More realistic age range
        birth_year = random.randint(current_year - max_age, current_year - min_age)
        birth_month = random.randint(1, 12)
        
        # Determine max days based on month
        max_days = days_in_month(birth_month, birth_year)
        birth_day = random.randint(1, max_days)
        
        # Generate a strong random password
        password_length = CONFIG.get("password_length", 12)
        password = generate_strong_password(password_length)
        
        # Generate consistent device information
        device_id = self.device_id
        machine_id = str(uuid.uuid4())
        
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "birth_year": birth_year,
            "birth_month": birth_month,
            "birth_day": birth_day,
            "gender": gender,
            "password": password,
            "device_id": device_id,
            "machine_id": machine_id,
            "locale": "en_US",
            "timezone": "-480"  # Pacific Time
        }
        
        self.account_data = user_data
        return user_data
    
    def _get_gender_appropriate_name(self):
        """Get a gender-appropriate first name"""
        # Male first names
        male_names = [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", 
            "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark", 
            "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", 
            "George", "Timothy", "Ronald", "Jason", "Edward", "Jeffrey", "Ryan", "Jacob",
            "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott",
            "Brandon", "Benjamin", "Samuel", "Gregory", "Alexander", "Patrick", "Frank",
            "Raymond", "Jack", "Dennis", "Jerry", "Tyler", "Aaron", "Henry", "Douglas", "Adam"
        ]
        
        # Female first names
        female_names = [
            "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", 
            "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Sandra", "Margaret", 
            "Ashley", "Kimberly", "Emily", "Donna", "Michelle", "Carol", "Amanda", "Dorothy", 
            "Melissa", "Deborah", "Stephanie", "Rebecca", "Laura", "Sharon", "Cynthia",
            "Kathleen", "Amy", "Angela", "Shirley", "Anna", "Ruth", "Brenda", "Pamela",
            "Nicole", "Katherine", "Virginia", "Catherine", "Christine", "Samantha", "Debra",
            "Janet", "Rachel", "Carolyn", "Emma", "Maria", "Heather", "Diane", "Julie"
        ]
        
        # Choose gender first
        gender = random.choice(["1", "2"])  # 1 for female, 2 for male
        
        # Choose name based on gender
        if gender == "1":  # Female
            first_name = random.choice(female_names)
        else:  # Male
            first_name = random.choice(male_names)
            
        return first_name, gender
    
    def _get_realistic_last_name(self):
        """Get a realistic last name"""
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
            "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", 
            "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", 
            "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
            "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
            "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
            "Carter", "Roberts", "Phillips", "Evans", "Turner", "Parker", "Collins",
            "Edwards", "Stewart", "Flores", "Morris", "Nguyen", "Murphy", "Rivera",
            "Cook", "Rogers", "Morgan", "Peterson", "Cooper", "Reed", "Bailey",
            "Bell", "Gomez", "Kelly", "Howard", "Ward", "Cox", "Diaz", "Richardson"
        ]
        
        return random.choice(last_names)