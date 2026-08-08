import json

def update_crops():
    with open('data/crops.json', 'r') as f:
        crops = json.load(f)

    for c in crops:
        if '_sources' in c:
            src = c.pop('_sources')
            c['sources'] = {
                "water_requirement": src.get('water', 'FAO Irrigation & Drainage Paper 56'),
                "season_calendar": src.get('season', 'ICAR Crop Calendar'),
                "market_volatility": src.get('volatility', 'Agmarknet 2023-24'),
                "rotation": src.get('rotation', 'ICAR Advisories')
            }
        
        name = c['name'].lower()
        if any(x in name for x in ['rice', 'wheat', 'maize', 'sorghum', 'millet', 'sugarcane']):
            c['family'] = 'Poaceae'
        elif any(x in name for x in ['gram', 'groundnut', 'soybean', 'bean', 'pea', 'horse']):
            c['family'] = 'Fabaceae'
        elif any(x in name for x in ['tomato', 'potato', 'chilli', 'pepper']):
            c['family'] = 'Solanaceae'
        elif 'onion' in name:
            c['family'] = 'Amaryllidaceae'
        elif 'cotton' in name:
            c['family'] = 'Malvaceae'
        elif 'sunflower' in name:
            c['family'] = 'Asteraceae'
        elif 'sesame' in name:
            c['family'] = 'Pedaliaceae'
        elif 'banana' in name:
            c['family'] = 'Musaceae'
        elif 'turmeric' in name or 'ginger' in name:
            c['family'] = 'Zingiberaceae'
        elif 'mustard' in name:
            c['family'] = 'Brassicaceae'
        elif 'coconut' in name:
            c['family'] = 'Arecaceae'
        else:
            c['family'] = 'Other'
            
        c['bad_predecessor_families'] = [c['family']]
        
        if c['family'] == 'Poaceae':
            c['good_predecessor_families'] = ['Fabaceae']
        elif c['family'] == 'Solanaceae':
            c['good_predecessor_families'] = ['Poaceae', 'Fabaceae']
        elif c['family'] == 'Fabaceae':
            c['good_predecessor_families'] = ['Poaceae']
        else:
            c['good_predecessor_families'] = ['Fabaceae']

    with open('data/crops.json', 'w') as f:
        json.dump(crops, f, indent=2)

def update_districts():
    with open('data/districts.json', 'r') as f:
        districts = json.load(f)

    for d in districts:
        if '_sources' in d:
            src = d.pop('_sources')
        d['source'] = "IMD District Rainfall Dataset, ICAR"
            
        state = d['state'].lower()
        # Seasonal distribution
        if 'tamil nadu' in state:
            d['seasonal_rainfall_share'] = {"kharif": 0.35, "rabi": 0.50, "summer": 0.15}
        elif any(x in state for x in ['karnataka', 'andhra', 'maharashtra', 'madhya pradesh']):
            d['seasonal_rainfall_share'] = {"kharif": 0.75, "rabi": 0.15, "summer": 0.10}
        else:
            d['seasonal_rainfall_share'] = {"kharif": 0.80, "rabi": 0.10, "summer": 0.10}
            
        # Soil proxy
        d_name = d['district'].lower()
        if d_name in ['thanjavur', 'nagapattinam', 'guntur']:
            d['soil_type'] = "Clayey / Deltaic Alluvium"
            d['soil_drainage'] = "Poor"
        elif 'nadu' in state:
            d['soil_type'] = "Red Loam"
            d['soil_drainage'] = "Good"
        elif 'maharashtra' in state or d_name in ['bellary', 'dharwad', 'raichur']:
            d['soil_type'] = "Black Cotton Soil (Vertisols)"
            d['soil_drainage'] = "Poor"
        elif 'rajasthan' in state:
            d['soil_type'] = "Sandy/Arid"
            d['soil_drainage'] = "Excellent"
        else:
            d['soil_type'] = "Alluvial Soil"
            d['soil_drainage'] = "Moderate"

    with open('data/districts.json', 'w') as f:
        json.dump(districts, f, indent=2)

update_crops()
update_districts()
