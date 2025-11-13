import os
import glob
from collections import defaultdict

def listdir_nohidden(path):
    return [
        os.path.basename(f) 
        for f in glob.glob(os.path.join(path, '*')) 
        if os.path.isfile(f)
    ]

date = '20230310'
session = 'SE_Lek1'

# Paths (adjust if needed)
rawdata_root = '/Volumes/EAS_shared/blackbuck/working/rawdata/Field_Recording_2023/Original/lekking/' + date + '/' + session
# processed_root = '/Volumes/EAS_shared/blackbuck/working/processed/Field_Recording_2023/SpatialRegistration/' + date + '/' + session
processed_root = '/Volumes/SSD4/processed/Field_Recording_2023/SpatialRegistration/' + date + '/' + session

# Define global required suffixes (apply to all drones)
global_required_suffixes = [
    '_3D_trajectories_utm.csv',
    '_3D_trajectories.csv',
    '_Anchored_trajectories.csv',
    '_3D_territories_utm.csv',
    '_3D_territories.csv',
    '_Anchored_matched.csv',
    '_Metashape_uv.csv',
    '_trajectories_uv.csv',
    '_homographies.pkl',
    '_Anchored.csv',
    '_YOLO_tracked.csv',
    '_YOLO.csv',
    '.csv'
]

# Define position-specific DLC suffixes
position_dlc_suffixes = {
    "P1": [
        'DLC_dlcrnetms5_06_TerritoryDetectionP1Aug1shuffle1_50000_assemblies.pickle',
        'DLC_dlcrnetms5_06_TerritoryDetectionP1Aug1shuffle1_50000_el.h5',
        'DLC_dlcrnetms5_06_TerritoryDetectionP1Aug1shuffle1_50000_el.pickle',
        'DLC_dlcrnetms5_06_TerritoryDetectionP1Aug1shuffle1_50000_full.pickle',
        'DLC_dlcrnetms5_06_TerritoryDetectionP1Aug1shuffle1_50000_meta.pickle'
    ],
    "P2": [
        'DLC_dlcrnetms5_05_TerritoryDetectionP2Jul10shuffle1_50000_assemblies.pickle',
        'DLC_dlcrnetms5_05_TerritoryDetectionP2Jul10shuffle1_50000_el.h5',
        'DLC_dlcrnetms5_05_TerritoryDetectionP2Jul10shuffle1_50000_el.pickle',
        'DLC_dlcrnetms5_05_TerritoryDetectionP2Jul10shuffle1_50000_full.pickle',
        'DLC_dlcrnetms5_05_TerritoryDetectionP2Jul10shuffle1_50000_meta.pickle'
    ],
    "P3": [
        'DLC_dlcrnetms5_07_TerritoryDetectionP3Aug18shuffle1_50000_assemblies.pickle',
        'DLC_dlcrnetms5_07_TerritoryDetectionP3Aug18shuffle1_50000_el.h5',
        'DLC_dlcrnetms5_07_TerritoryDetectionP3Aug18shuffle1_50000_el.pickle',
        'DLC_dlcrnetms5_07_TerritoryDetectionP3Aug18shuffle1_50000_full.pickle',
        'DLC_dlcrnetms5_07_TerritoryDetectionP3Aug18shuffle1_50000_meta.pickle'
    ]
}

# Collect raw video IDs
raw_videos = defaultdict(list)
for subdir, _, files in os.walk(rawdata_root):
    for f in files:
        if f.endswith(('.MP4', '.mp4')):
            base, _ = os.path.splitext(f)
            parts = base.split("_")
            if len(parts) >= 6:
                video_id = "_".join(parts[:4])
                raw_videos[video_id].append(base)

for drone in ['P1D1', 'P1D2', 'P2D3', 'P2D4', 'P3D5', 'P3D6']:
    position = drone[-4:-2]  # "P1", "P2", "P3"

    # List required suffixes for current drone
    required_suffixes = global_required_suffixes[:]
    if position in position_dlc_suffixes:
        required_suffixes += position_dlc_suffixes[position]

    # List raw video IDs in current drone
    key = next((k for k in raw_videos if drone in k), None)
    
    # List expected files in the processed root directory
    expected_files = [raw + suf for raw in raw_videos[key] for suf in required_suffixes]

    # List files in processed root directory
    folder_path = os.path.join(processed_root, drone)
    processed_files = listdir_nohidden(folder_path)

    # Convert lists to sets
    expected_set = set(expected_files)
    processed_set = set(processed_files)

    # Files that are missing in processed_files
    missing_files = expected_set - processed_set

    # Files that are extra/unexpected in processed_files
    unexpected_files = processed_set - expected_set

    # Logging
    if missing_files:
        print(f"❌ {len(missing_files)} missing files in processed_files:")
        for f in sorted(missing_files):
            print(f"   - {f}")

    if unexpected_files:
        print("⚠️ Unexpected extra files in processed_files:")
        for f in sorted(unexpected_files):
            print(f"   - {f}")

    if not missing_files and not unexpected_files:
        print(f"✅ All files for {date} {session} {drone} match exactly!")
