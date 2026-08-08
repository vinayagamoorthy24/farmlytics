import json
import os
import math

# --- CONFIGURATION (SCIENTIFIC BOUNDS) ---
VALID_SOIL_TYPES = {
    'Red Loam', 'Black Cotton Soil (Vertisol)', 'Alluvial Soil', 
    'Lateritic Soil', 'Clayey Delta Soil', 'Sandy Soil'
}

VALID_FAMILIES = {
    'Poaceae', 'Fabaceae', 'Solanaceae', 'Malvaceae', 'Asteraceae', 
    'Brassicaceae', 'Cucurbitaceae', 'Pedaliaceae', 'Euphorbiaceae',
    'Musaceae', 'Zingiberaceae', 'Arecaceae' # Added common families
}

VALID_VOLATILITY = {'low', 'medium', 'high'}
VALID_SEASONS = {'kharif', 'rabi', 'summer'}

# Physics & Physiology Bounds
RAINFALL_BOUNDS = (200, 3000)      # mm (Annual avg)
TEMP_SAFE_BOUNDS = (10, 45)        # Celsius
DURATION_BOUNDS = (30, 365)        # days
WATER_NEED_BOUNDS = (100, 2500)    # mm (Crop cycle total)

def validate_districts(path):
    print(f"\n[VALIDATING DISTRICTS]: {path}")
    if not os.path.exists(path):
        print(f"  [FATAL] File not found: {path}")
        return 1
        
    with open(path, 'r', encoding='utf-8') as f:
        districts = json.load(f)
    
    errors = 0
    warnings = 0
    for d in districts:
        name = d.get('district', 'Unknown ID')
        
        # 1. Required Fields
        required = ['id', 'district', 'state', 'avg_annual_rainfall_mm', 'soil_type']
        for field in required:
            if field not in d:
                print(f"  [ERROR] {name}: Missing required field '{field}'")
                errors += 1
        
        # 2. Rainfall Sanity
        annual_rain = d.get('avg_annual_rainfall_mm', 0)
        if not (RAINFALL_BOUNDS[0] <= annual_rain <= RAINFALL_BOUNDS[1]):
            print(f"  [ERROR] {name}: Rainfall anomaly ({annual_rain}mm)")
            errors += 1
            
        # 3. Rainfall Shares sum check
        shares = d.get('seasonal_rainfall_share', {})
        total_share = sum(shares.values())
        if not math.isclose(total_share, 1.0, rel_tol=1e-4):
            print(f"  [ERROR] {name}: Rainfall shares sum to {total_share} (expected 1.0)")
            errors += 1
            
    if errors == 0:
        print(f"  ✓ Districts valid. ({warnings} warnings)")
    return errors

def validate_crops(path):
    print(f"\n[VALIDATING CROPS]: {path}")
    if not os.path.exists(path):
        print(f"  [FATAL] File not found: {path}")
        return 1

    with open(path, 'r', encoding='utf-8') as f:
        crops = json.load(f)
    
    crop_ids = {c['id'] for c in crops if 'id' in c}
    errors = 0
    
    for c in crops:
        name = c.get('name', c.get('id', 'Unknown'))
        
        # 1. Range Anomaly Checks (Physiological Bounds)
        wmin = c.get('water_need_mm_min', 0)
        wmax = c.get('water_need_mm_max', 0)
        if not (WATER_NEED_BOUNDS[0] <= wmin <= WATER_NEED_BOUNDS[1]):
            print(f"  [ERROR] {name}: water_min anomaly ({wmin}mm)")
            errors += 1
        if wmin > wmax:
            print(f"  [ERROR] {name}: water_min > water_max")
            errors += 1
            
        dmin = c.get('growth_duration_days_min', 0)
        dmax = c.get('growth_duration_days_max', 0)
        if not (DURATION_BOUNDS[0] <= dmin <= DURATION_BOUNDS[1]):
            print(f"  [ERROR] {name}: duration anomaly ({dmin} days)")
            errors += 1

        # 2. Enum & Season Checks
        for s in c.get('seasons', []):
            if s.lower() not in VALID_SEASONS:
                print(f"  [ERROR] {name}: Invalid season '{s}'")
                errors += 1

        # 3. Cross-Reference (Rotation IDs)
        for pred in c.get('good_predecessors', []):
            if pred not in crop_ids:
                 print(f"  [WARNING] {name}: Good predecessor '{pred}' not found in crop list")

    if errors == 0:
        print("  ✓ Crops valid (including physiological bounds).")
    return errors

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d_err = validate_districts(os.path.join(base_dir, 'data', 'districts.json'))
    c_err = validate_crops(os.path.join(base_dir, 'data', 'crops.json'))
    
    print("\n[STRICT VALIDATION FINISHED]")
    if (d_err + c_err) > 0:
        exit(1)
    else:
        exit(0)
