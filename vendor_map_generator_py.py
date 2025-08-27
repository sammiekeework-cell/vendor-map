import folium
from folium.plugins import HeatMap
import pandas as pd
from geopy.geocoders import Nominatim
import time
import pickle
import os
import ssl
import certifi

# Fix SSL issues
try:
    from urllib3.util.ssl_ import create_urllib3_context
    ssl_context = create_urllib3_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
except:
    pass

# Load Excel file
excel_file = "C:/Users/KEESZ417/OneDrive - KDP/vendormap.xlsx"
kdp_sites = pd.read_excel(excel_file, sheet_name="KDP Sites")
inspired_coverage = pd.read_excel(excel_file, sheet_name="Inspired Coverage")
prosegur_coverage = pd.read_excel(excel_file, sheet_name="Prosegur Coverage")
unlimited_tech = pd.read_excel(excel_file, sheet_name="Unlimited Technology Coverage")

# DEBUG: Check column names
print("Column names in each sheet:")
print("KDP Sites columns:", list(kdp_sites.columns))
print("Inspired Coverage columns:", list(inspired_coverage.columns))
print("Prosegur Coverage columns:", list(prosegur_coverage.columns))
print("Unlimited Technology columns:", list(unlimited_tech.columns))
print("\nFirst few rows of KDP Sites:")
print(kdp_sites.head())

# Cache file for geocoded results
cache_file = "geocode_cache.pkl"

# Load existing cache if available
def load_cache():
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    return {}

# Save cache
def save_cache(cache):
    with open(cache_file, 'wb') as f:
        pickle.dump(cache, f)

# Comprehensive coordinate database
city_coords = {
    # KDP Sites (City,State format)
    'dallas,tx': (32.7767, -96.7970), 'beckley,wv': (37.7782, -81.1882),
    'windsor,wi': (43.2002, -89.3373), 'pewaukee,wi': (43.0820, -88.2632),
    'tukwila,wa': (47.4740, -122.2607), 'sumner,wa': (47.2023, -122.2351),
    'spokane,wa': (47.6588, -117.4260), 'essex,vt': (44.4896, -73.1123),
    'waco,tx': (31.5493, -97.1467), 'san antonio,tx': (29.4241, -98.4936),
    'irving,tx': (32.8140, -96.9489), 'houston,tx': (29.7604, -95.3698),
    'harlingen,tx': (26.1906, -97.6961), 'frisco,tx': (33.1507, -96.8236),
    'corpus christi,tx': (27.8006, -97.3964), 'austin,tx': (30.2672, -97.7431),
    'newport,tn': (35.9668, -83.1879), 'memphis,tn': (35.1495, -90.0490),
    'mcminnville,tn': (35.6834, -85.7697), 'knoxville,tn': (35.9606, -83.9207),
    'goodlettsville,tn': (36.3230, -86.7136), 'singapore': (1.3521, 103.8198),
    'spartanburg,sc': (34.9495, -81.9320), 'montreal,qc': (45.5017, -73.5673),
    'cranberry township,pa': (40.6881, -80.1078), 'lehigh valley,pa': (40.6023, -75.4714),
    'harrisburg,pa': (40.2732, -76.8839), 'allentown,pa': (40.6084, -75.4902),
    'tulsa,ok': (36.1539, -95.9928), 'oklahoma city,ok': (35.4676, -97.5164),
    'toledo,oh': (41.6528, -83.5379), 'south point,oh': (38.4162, -82.5879),
    'dayton,oh': (39.7589, -84.1916), 'columbus,oh': (39.9612, -82.9988),
    'cincinnati,oh': (39.1031, -84.5120), 'cincinnati, oh': (39.1031, -84.5120),
    'williamson,ny': (43.2059, -77.1855), 'melville,ny': (40.7934, -73.4149),
    'maspeth,ny': (40.7267, -73.9123), 'elmsford,ny': (41.0551, -73.8201),
    'las vegas,nv': (36.1699, -115.1398), 'avenel,nj': (40.5801, -74.2813),
    'omaha,ne': (41.2565, -95.9345), 'st. louis,mo': (38.6270, -90.1994),
    'hazelwood,mo': (38.7717, -90.3712), 'st. paul,mn': (44.9537, -93.0900),
    'minneapolis,mn': (44.9778, -93.2650), 'holland,mi': (42.7875, -86.1089),
    'flint,mi': (43.0125, -83.6875), 'detroit,mi': (42.3314, -83.0458),
    'benton harbor,mi': (42.1167, -86.4542), 'burlington,ma': (42.5047, -71.1956),
    'louisville,ky': (38.2527, -85.7585), 'lenexa,ks': (38.9536, -94.7336),
    'newbridge,ireland': (53.1781, -6.7967), 'south bend,in': (41.6764, -86.2520),
    'new castle,in': (39.9289, -85.3702), 'indianapolis,in': (39.7684, -86.1581),
    'fort wayne,in': (41.0793, -85.1394), 'evansville,in': (37.9716, -87.5710),
    'springfield,il': (39.7817, -89.6501), 'peoria,il': (40.6936, -89.5889),
    'northlake,il': (41.9170, -87.8870), 'ottumwa,ia': (41.0197, -92.4079),
    'cedar rapids,ia': (41.9778, -91.6656), 'norcross,ga': (33.9412, -84.2135),
    'tampa,fl': (27.9506, -82.4572), 'orlando,fl': (28.5383, -81.3792),
    'miami,fl': (25.7617, -80.1918), 'jacksonville,fl': (30.3322, -81.6557),
    'fort myers,fl': (26.6406, -81.8723), 'boynton beach,fl': (26.5318, -80.0905),
    'englewood,co': (39.6478, -104.9878), 'colorado springs,co': (38.8339, -104.8214),
    
    # Inspired Coverage (City, State format with spaces)
    'albuquerque, nm': (35.0844, -106.6504), 'anaheim, ca': (33.8366, -117.9143),
    'arlington, tx': (32.7357, -97.1081), 'atlanta, ga': (33.7490, -84.3880),
    'aurora, co': (39.7294, -104.8319), 'austin, tx': (30.2672, -97.7431),
    'bakersfield, ca': (35.3733, -119.0187), 'baltimore, md': (39.2904, -76.6122),
    'boston, ma': (42.3601, -71.0589), 'buffalo, ny': (42.8864, -78.8784),
    'chandler, az': (33.3062, -111.8413), 'charlotte, nc': (35.2271, -80.8431),
    'chesapeake, va': (36.7682, -76.2875), 'chicago, il': (41.8781, -87.6298),
    'chula vista, ca': (32.6401, -117.0842), 'cincinnati, oh': (39.1031, -84.5120),
    'cleveland, oh': (41.4993, -81.6944), 'colorado springs, co': (38.8339, -104.8214),
    'columbus, oh': (39.9612, -82.9988), 'corpus christi, tx': (27.8006, -97.3964),
    'dallas, tx': (32.7767, -96.7970), 'denver, co': (39.7392, -104.9903),
    'detroit, mi': (42.3314, -83.0458), 'durham, nc': (35.9940, -78.8986),
    'el paso, tx': (31.7619, -106.4850), 'fort wayne, in': (41.0793, -85.1394),
    'fort worth, tx': (32.7555, -97.3308), 'fresno, ca': (36.7378, -119.7871),
    'gilbert, az': (33.3528, -111.7890), 'greensboro, nc': (36.0726, -79.7920),
    'henderson, nv': (36.0395, -114.9817), 'houston, tx': (29.7604, -95.3698),
    'indianapolis, in': (39.7684, -86.1581), 'irvine, ca': (33.6846, -117.8265),
    'irving, tx': (32.8140, -96.9489), 'jacksonville, fl': (30.3322, -81.6557),
    'jersey city, nj': (40.7178, -74.0431), 'kansas city, mo': (39.0997, -94.5786),
    'laredo, tx': (27.5306, -99.4803), 'las vegas, nv': (36.1699, -115.1398),
    'lexington, ky': (38.0406, -84.5037), 'lincoln, ne': (40.8136, -96.7026),
    'long beach, ca': (33.7701, -118.1937), 'los angeles, ca': (34.0522, -118.2437),
    'louisville, ky': (38.2527, -85.7585), 'lubbock, tx': (33.5779, -101.8552),
    'madison, wi': (43.0731, -89.4012), 'memphis, tn': (35.1495, -90.0490),
    'mesa, az': (33.4152, -111.8315), 'miami, fl': (25.7617, -80.1918),
    'milwaukee, wi': (43.0389, -87.9065), 'minneapolis, mn': (44.9778, -93.2650),
    'nashville, tn': (36.1627, -86.7816), 'new orleans, la': (29.9511, -90.0715),
    'new york, ny': (40.7128, -74.0060), 'newark, nj': (40.7357, -74.1724),
    'north las vegas, nv': (36.1989, -115.1175), 'oakland, ca': (37.8044, -122.2712),
    'oklahoma city, ok': (35.4676, -97.5164), 'omaha, ne': (41.2565, -95.9345),
    'orlando, fl': (28.5383, -81.3792), 'philadelphia, pa': (39.9526, -75.1652),
    'phoenix, az': (33.4484, -112.0740), 'pittsburgh, pa': (40.4406, -79.9959),
    'plano, tx': (33.0198, -96.6989), 'portland, or': (45.5152, -122.6784),
    'raleigh, nc': (35.7796, -78.6382), 'reno, nv': (39.5296, -119.8138),
    'riverside, ca': (33.9533, -117.3962), 'sacramento, ca': (38.5816, -121.4944),
    'san antonio, tx': (29.4241, -98.4936), 'san diego, ca': (32.7157, -117.1611),
    'san francisco, ca': (37.7749, -122.4194), 'san jose, ca': (37.3382, -121.8863),
    'santa ana, ca': (33.7455, -117.8677), 'seattle, wa': (47.6062, -122.3321),
    'st. louis, mo': (38.6270, -90.1994), 'st. paul, mn': (44.9537, -93.0900),
    'st. petersburg, fl': (27.7676, -82.6403), 'stockton, ca': (37.9577, -121.2908),
    'tampa, fl': (27.9506, -82.4572), 'toledo, oh': (41.6528, -83.5379),
    'tucson, az': (32.2226, -110.9747), 'tulsa, ok': (36.1539, -95.9928),
    'virginia beach, va': (36.8529, -75.9780), 'washington, dc': (38.9072, -77.0369),
    'wichita, ks': (37.6872, -97.3301), 'winston-salem, nc': (36.0999, -80.2442),
    
    # Prosegur Coverage
    'deerfield beach, fl': (26.3184, -80.0997), 'lowell, ma': (42.6334, -71.3162),
    'madrid, spain': (40.4168, -3.7038), 'miguel hidalgo, mexico': (19.4326, -99.1332),
    'shanghai, china': (31.2304, 121.4737), 'lisbon, portugal': (38.7223, -9.1393),
    
    # Unlimited Technology Coverage
    'birmingham, al': (33.5207, -86.8025), 'boise, id': (43.6150, -116.2023),
    'burlington, vt': (44.4759, -73.2121), 'calgary, ab': (51.0447, -114.0719),
    'ciudad juárez, chihuahua': (31.6904, -106.4245), 'columbia, sk': (52.1332, -106.6700),
    'edmonton, ab': (53.5461, -113.4938), 'jackson, ms': (32.2988, -90.1848),
    'kansas city, ks': (39.1142, -94.6275), 'little rock, ar': (34.7465, -92.2896),
    'manchester, nh': (42.9956, -71.4548), 'mobile, al': (30.6954, -88.0399),
    'monterey, ca': (36.6002, -121.8947), 'monterrey, nuevo león': (25.6866, -100.3161),
    'ottawa, on': (45.4215, -75.6972), 'providence, ri': (41.8240, -71.4128),
    'quebec city, qc': (46.8139, -71.2080), 'richmond, va': (37.5407, -77.4360),
    'salt lake city, ut': (40.7608, -111.8910), 'santa barbara, ca': (34.4208, -119.6982),
    'santa cruz, ca': (36.9741, -122.0308), 'vancouver, bc': (49.2827, -123.1207),
    
    # Additional KDP locations
    'reno,nv': (39.5296, -119.8138), 'las vegas,nv': (36.1699, -115.1398),
    'san diego,ca': (32.7157, -117.1611), 'sacramento,ca': (38.5816, -121.4944),
    'tucson,az': (32.2226, -110.9747), 'colorado springs,co': (38.8339, -104.8214),
    'shenzen atc crp,guandong': (22.5431, 114.0579), 'shenzen adp crp,guangdong': (22.5431, 114.0579),
    'victorville,ca': (34.5362, -117.2911), 'vernon,ca': (34.0042, -118.2384),
    'stockton,ca': (37.9577, -121.2908), 'san leandro,ca': (37.7249, -122.1561),
    'riverside,ca': (33.9533, -117.3962), 'redlands,ca': (34.0556, -117.1825),
    'orange,ca': (33.7879, -117.8531), 'fresno,ca': (36.7378, -119.7871),
    'bakersfield,ca': (35.3733, -119.0187), 'varginha,brazil': (-21.5514, -45.4300),
    'tempe,az': (33.4255, -111.9400), 'rogers,ar': (36.3320, -94.1185),
    'union city,ga': (33.5968, -84.7344), 'aspers,pa': (39.9787, -77.2155),
    'bethlehem,pa': (40.6259, -75.3705), 'moore,sc': (34.8712, -82.0207),
    'windsor,va': (36.8043, -76.7394), 'williston,vt': (44.4281, -73.0743),
    'gaylord,mi': (45.0275, -84.6747), 'superior,wi': (46.7208, -92.1041),
    'albuquerque,nm': (35.0844, -106.6504), 'beaumont,tx': (30.0860, -94.1018),
    'boise,id': (43.6150, -116.2023), 'cadillac,mi': (44.2519, -85.4017),
    'chico,ca': (39.7285, -121.8375), 'clear lake,ia': (43.1375, -93.3813),
    'des moines,ia': (41.5868, -93.6250), 'la vista,ne': (41.1839, -96.0831),
    'lubbock,tx': (33.5779, -101.8552), 'marietta,oh': (39.4148, -81.4548),
    'midvale,oh': (40.6481, -81.7279), 'mount morris,mi': (42.9764, -83.6938),
    'petaluma,ca': (38.2324, -122.6367), 'racine,wi': (42.7261, -87.7829),
    'twinsburg,oh': (41.3125, -81.4402), 'bossier city,la': (32.5160, -93.7321),
    'corsicana,tx': (32.0954, -96.4689), 'kingsport,tn': (36.5484, -82.5618),
    'lawton,ok': (34.6087, -98.4170), 'mcalester,ok': (34.9334, -95.7697),
    'monroe,la': (32.5093, -92.1193), 'sherman,tx': (33.6357, -96.6089),
    'springdale,ar': (36.1867, -94.1288), 'texarkana,ar': (33.4418, -94.0377),
    'grand ledge,mi': (42.7517, -84.7467), 'guadalajara,jalisco': (20.6597, -103.3496),
    'oshkosh,wi': (44.0247, -88.5426), 'san fernando,ca': (34.2819, -118.4390),
    'wichita,ks': (37.6872, -97.3301), 'tomah,wi': (43.9747, -90.5037)
}

# Optimized geocode function
def geocode_locations(locations, layer_name=""):
    cache = load_cache()
    coords = []
    new_geocodes = 0
    
    print(f"Processing {len(locations)} locations for {layer_name}")
    
    for i, loc in enumerate(locations):
        # Show progress
        if i % 25 == 0:
            print(f"  Progress: {i}/{len(locations)} ({i/len(locations)*100:.1f}%)")
            
        try:
            # Check cache first
            if loc in cache:
                lat, lon = cache[loc]
                coords.append((lat, lon, loc))
                continue
            
            # Check built-in coordinates
            loc_lower = loc.lower()
            if loc_lower in city_coords:
                lat, lon = city_coords[loc_lower]
                cache[loc] = (lat, lon)
                coords.append((lat, lon, loc))
                new_geocodes += 1
                continue
            
            # Try online geocoding with SSL workaround
            try:
                geolocator = Nominatim(
                    user_agent="vendormapapp_v1", 
                    timeout=15,
                    scheme='http'  # Try HTTP instead of HTTPS
                )
                location = geolocator.geocode(loc)
                if location:
                    cache[loc] = (location.latitude, location.longitude)
                    coords.append((location.latitude, location.longitude, loc))
                    new_geocodes += 1
                    print(f"    Geocoded: {loc}")
                else:
                    print(f"    Could not find: {loc}")
            except Exception as ssl_error:
                print(f"    Could not geocode: {loc} - Add manually to coordinate database")
                
            # Save cache every 10 new geocodes
            if new_geocodes % 10 == 0 and new_geocodes > 0:
                save_cache(cache)
                    
        except Exception as e:
            print(f"    Failed: {loc} - {type(e).__name__}")
            
        # Small delay to be respectful
        if loc not in cache and loc_lower not in city_coords:
            time.sleep(0.2)
    
    # Save final cache
    save_cache(cache)
    print(f"  Completed {layer_name}: {len(coords)} locations geocoded ({new_geocodes} new)")
    return coords

# Helper function to find location column
def find_location_column(df, sheet_name):
    """Find the column that contains location data"""
    possible_names = ['Location', 'location', 'City', 'city', 'Address', 'address', 
                      'Site', 'site', 'Place', 'place', 'Area', 'area']
    
    for col in possible_names:
        if col in df.columns:
            print(f"Found location column '{col}' in {sheet_name}")
            return col
    
    # If no obvious column found, show all columns
    print(f"No obvious location column found in {sheet_name}")
    print(f"Available columns: {list(df.columns)}")
    return None

# Option 1: Skip geocoding and use sample data for testing
USE_SAMPLE_DATA = False  # Set to False to run full geocoding

if USE_SAMPLE_DATA:
    print("Using sample data - skipping geocoding for faster testing")
    # Sample coordinates for testing
    kdp_coords = [(40.7128, -74.0060, "New York"), (34.0522, -118.2437, "Los Angeles")]
    inspired_coords = [(41.8781, -87.6298, "Chicago"), (29.7604, -95.3698, "Houston")]
    prosegur_coords = [(33.4484, -112.0740, "Phoenix"), (39.7392, -104.9903, "Denver")]
    unlimited_coords = [(25.7617, -80.1918, "Miami"), (47.6062, -122.3321, "Seattle")]
else:
    # Full geocoding with optimizations
    print("Starting geocoding process...")
    
    # Find location columns for each sheet
    kdp_loc_col = find_location_column(kdp_sites, "KDP Sites")
    inspired_loc_col = find_location_column(inspired_coverage, "Inspired Coverage")
    prosegur_loc_col = find_location_column(prosegur_coverage, "Prosegur Coverage")
    unlimited_loc_col = find_location_column(unlimited_tech, "Unlimited Technology")
    
    # Only geocode if we found the location columns
    kdp_coords = []
    inspired_coords = []
    prosegur_coords = []
    unlimited_coords = []
    
    if kdp_loc_col:
        kdp_coords = geocode_locations(kdp_sites[kdp_loc_col].dropna().unique(), "KDP Sites")
    if inspired_loc_col:
        inspired_coords = geocode_locations(inspired_coverage[inspired_loc_col].dropna().unique(), "Inspired Coverage")
    if prosegur_loc_col:
        prosegur_coords = geocode_locations(prosegur_coverage[prosegur_loc_col].dropna().unique(), "Prosegur Coverage")
    if unlimited_loc_col:
        unlimited_coords = geocode_locations(unlimited_tech[unlimited_loc_col].dropna().unique(), "Unlimited Technology")

print("Creating map...")

# Base map
base_map = folium.Map(location=[39.5, -98.35], zoom_start=4)

# Heatmap data (unchanged)
heatmap_data = [
    [29.7604, -95.3698, 15], [38.6270, -90.1994, 12], [40.8270, -74.2007, 10],
    [33.1507, -96.8236, 9], [30.3322, -81.6557, 6], [39.6478, -104.9878, 5],
    [26.5318, -80.0905, 5], [34.0556, -117.1825, 4], [41.9170, -87.8870, 4],
    [40.6936, -89.5889, 3], [42.1125, -86.3580, 3], [35.7308, -81.3412, 2],
    [32.7767, -96.7970, 2], [40.6084, -75.4902, 2], [33.4255, -111.9400, 2],
    [36.1627, -86.7816, 2], [41.2565, -95.9345, 2], [35.4676, -97.5164, 2],
    [35.0844, -106.6504, 2], [38.5816, -121.4944, 2], [30.2672, -97.7431, 2],
    [25.7617, -80.1918, 2], [34.0522, -118.2437, 2], [37.7749, -122.4194, 2],
    [36.1539, -95.9928, 2], [42.3314, -83.0458, 3], [39.1031, -84.5120, 2],
    [43.0809, -88.2614, 2], [47.6588, -117.4260, 2], [44.4759, -73.2121, 2],
    [27.9506, -82.4572, 2], [40.5832, -74.2750, 2], [38.7248, -87.5558, 1],
    [26.6406, -81.8723, 1], [37.7249, -122.1561, 1], [39.7589, -84.1916, 1],
    [42.4072, -71.3824, 1], [52.2681, -9.7033, 1], [-21.5514, -45.4300, 1]
]

HeatMap(heatmap_data, radius=25, blur=18, max_zoom=7, opacity=0.6, gradient={
    0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 0.8: 'red', 1.0: 'black'
}).add_to(base_map)

# Add location layers with layer-specific offsets to prevent cross-layer overlap
def add_layer(coords, name, color):
    from folium.plugins import MarkerCluster
    import math
    from collections import defaultdict
    
    layer = folium.FeatureGroup(name=name)
    
    # Create marker cluster
    marker_cluster = MarkerCluster(
        name=f"{name} Cluster",
        overlay=True,
        control=True
    ).add_to(layer)
    
    # Layer-specific offset directions to separate different vendors
    layer_offsets = {
        'KDP Sites': (0.002, 0.002),           # Northeast
        'Inspired Coverage': (-0.002, 0.002),  # Northwest  
        'Prosegur Coverage': (0.002, -0.002),  # Southeast
        'Unlimited Technology Coverage': (-0.002, -0.002)  # Southwest
    }
    
    base_lat_offset, base_lon_offset = layer_offsets.get(name, (0, 0))
    
    # Group locations within this layer by rounded coordinates
    location_groups = defaultdict(list)
    
    for lat, lon, label in coords:
        # Round to 3 decimal places to catch overlaps within this layer
        rounded_key = f"{round(lat, 3)},{round(lon, 3)}"
        location_groups[rounded_key].append((lat, lon, label))
    
    # Process each group
    for group_key, locations in location_groups.items():
        center_lat = sum(loc[0] for loc in locations) / len(locations)
        center_lon = sum(loc[1] for loc in locations) / len(locations)
        
        for i, (lat, lon, label) in enumerate(locations):
            # Apply base layer offset to separate different vendors
            new_lat = center_lat + base_lat_offset
            new_lon = center_lon + base_lon_offset
            
            # If multiple locations in same area within this layer, spread them further
            if len(locations) > 1 and i > 0:
                angle = (i - 1) * (360 / max(len(locations) - 1, 1))
                additional_distance = 0.003 + (i * 0.002)
                
                additional_lat_offset = additional_distance * math.cos(math.radians(angle))
                additional_lon_offset = additional_distance * math.sin(math.radians(angle)) / math.cos(math.radians(center_lat))
                
                new_lat += additional_lat_offset
                new_lon += additional_lon_offset
            
            # Add marker with offset
            popup_text = f"<b>{name}</b><br>{label}"
            if base_lat_offset != 0 or base_lon_offset != 0 or len(locations) > 1:
                popup_text += "<br><i>(Positioned for visibility)</i>"
            
            folium.Marker(
                [new_lat, new_lon], 
                popup=folium.Popup(popup_text, max_width=250),
                tooltip=f"{label} - {name}",
                icon=folium.Icon(color=color)
            ).add_to(marker_cluster)
    
    layer.add_to(base_map)

add_layer(kdp_coords, "KDP Sites", "green")
add_layer(inspired_coords, "Inspired Coverage", "purple")
add_layer(prosegur_coords, "Prosegur Coverage", "orange")
add_layer(unlimited_coords, "Unlimited Technology Coverage", "darkblue")

# State labels (unchanged)
state_labels = {
    'CA': [36.7783, -119.4179], 'TX': [31.9686, -99.9018], 'FL': [27.9944, -81.7603],
    'NY': [43.0000, -75.0000], 'IL': [40.0000, -89.0000], 'MO': [38.5000, -92.5000],
    'GA': [32.1656, -82.9001], 'MI': [44.3148, -85.6024], 'OH': [40.4173, -82.9071],
    'CO': [39.5501, -105.7821], 'WA': [47.7511, -120.7401], 'TN': [35.5175, -86.5804],
    'NC': [35.7596, -79.0193], 'NJ': [40.0583, -74.4057], 'PA': [41.2033, -77.1945],
    'AZ': [34.0489, -111.0937], 'MA': [42.4072, -71.3824], 'MN': [46.7296, -94.6859]
}
for abbr, coords in state_labels.items():
    folium.Marker(coords, icon=folium.DivIcon(html=f'<div style="font-size:12px;font-weight:bold;color:black;">{abbr}</div>')).add_to(base_map)

# Legend and cluster styling
legend_html = '''
<div style="position: fixed; bottom: 50px; right: 50px; z-index:9999; background-color:white;
     padding: 10px; border:2px solid grey; font-size:14px;">
<strong>Heat Intensity</strong><br>
<span style="color:blue;">●</span> Low<br>
<span style="color:lime;">●</span> Moderate<br>
<span style="color:orange;">●</span> Elevated<br>
<span style="color:red;">●</span> High<br>
<span style="color:black;">●</span> Critical<br>
</div>
'''

# Custom CSS for better cluster visibility
cluster_css = '''
<style>
.marker-cluster-small {
    background-color: rgba(181, 226, 140, 0.9) !important;
    border: 2px solid white !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.5) !important;
}
.marker-cluster-small div {
    background-color: rgba(110, 204, 57, 0.9) !important;
    color: white !important;
    font-weight: bold !important;
    text-shadow: 1px 1px 1px rgba(0,0,0,0.5) !important;
}
.marker-cluster-medium {
    background-color: rgba(241, 211, 87, 0.9) !important;
    border: 2px solid white !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.5) !important;
}
.marker-cluster-medium div {
    background-color: rgba(240, 194, 12, 0.9) !important;
    color: white !important;
    font-weight: bold !important;
    text-shadow: 1px 1px 1px rgba(0,0,0,0.5) !important;
}
.marker-cluster-large {
    background-color: rgba(253, 156, 115, 0.9) !important;
    border: 2px solid white !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.5) !important;
}
.marker-cluster-large div {
    background-color: rgba(241, 128, 23, 0.9) !important;
    color: white !important;
    font-weight: bold !important;
    text-shadow: 1px 1px 1px rgba(0,0,0,0.5) !important;
}
</style>
'''

base_map.get_root().html.add_child(folium.Element(legend_html))
base_map.get_root().html.add_child(folium.Element(cluster_css))

# Layer control
folium.LayerControl().add_to(base_map)

# Save map
base_map.save("vendorservicemap.html")
print("Map saved as vendorservicemap.html")
print("Done!")
