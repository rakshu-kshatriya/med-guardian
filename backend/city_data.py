"""
Indian cities data with coordinates and state information.
Used for disease tracking, predictions, and route calculations.
"""

CITIES = [
    {"city_name": "New Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2090},
    {"city_name": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777},
    {"city_name": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946},
    {"city_name": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lng": 88.3639},
    {"city_name": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707},
    {"city_name": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lng": 78.4867},
    {"city_name": "Pune", "state": "Maharashtra", "lat": 18.5204, "lng": 73.8567},
    {"city_name": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714},
    {"city_name": "Surat", "state": "Gujarat", "lat": 21.1702, "lng": 72.8311},
    {"city_name": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lng": 75.7873},
    {"city_name": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lng": 80.9462},
    {"city_name": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lng": 77.4126},
    {"city_name": "Patna", "state": "Bihar", "lat": 25.5941, "lng": 85.1376},
    {"city_name": "Kochi", "state": "Kerala", "lat": 9.9312, "lng": 76.2673},
    {"city_name": "Visakhapatnam", "state": "Andhra Pradesh", "lat": 17.6868, "lng": 83.2185},
    {"city_name": "Vadodara", "state": "Gujarat", "lat": 22.3072, "lng": 73.1812},
    {"city_name": "Indore", "state": "Madhya Pradesh", "lat": 22.7196, "lng": 75.8577},
    {"city_name": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lng": 79.0882},
    {"city_name": "Thiruvananthapuram", "state": "Kerala", "lat": 8.5241, "lng": 76.9366},
    {"city_name": "Ranchi", "state": "Jharkhand", "lat": 23.3441, "lng": 85.3096},
    {"city_name": "Guwahati", "state": "Assam", "lat": 26.1445, "lng": 91.7362},
    {"city_name": "Dehradun", "state": "Uttarakhand", "lat": 30.3165, "lng": 78.0322},
    {"city_name": "Chandigarh", "state": "Chandigarh", "lat": 30.7333, "lng": 76.7794},
    {"city_name": "Amritsar", "state": "Punjab", "lat": 31.6340, "lng": 74.8723},
    {"city_name": "Jodhpur", "state": "Rajasthan", "lat": 26.2389, "lng": 73.0243},
    {"city_name": "Raipur", "state": "Chhattisgarh", "lat": 21.2514, "lng": 81.6296},
    {"city_name": "Mysore", "state": "Karnataka", "lat": 12.2958, "lng": 76.6394},
    {"city_name": "Mangalore", "state": "Karnataka", "lat": 12.9141, "lng": 74.8560},
    {"city_name": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0168, "lng": 76.9558},
    {"city_name": "Bhubaneswar", "state": "Odisha", "lat": 20.2961, "lng": 85.8245},
]

def get_city_by_name(city_name: str) -> dict:
    """Get city data by name (case-insensitive)."""
    for city in CITIES:
        if city["city_name"].lower() == city_name.lower():
            return city
    return None

def get_all_cities() -> list:
    """Get all cities."""
    return CITIES

