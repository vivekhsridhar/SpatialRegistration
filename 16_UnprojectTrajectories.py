import Metashape
import numpy as np
import pandas as pd
import os
import glob
import concurrent.futures
import time

def process_camera(camera, df_dict, surface, transform_matrix, chunk):
    """Process a single camera in parallel."""
    start_time = time.time()
    data = []

    if camera.label not in df_dict:
        print(f"[DEBUG] Camera '{camera.label}' not found in CSV. Skipping.")
        return data  # Skip if camera not in CSV
    
    df_filtered = df_dict[camera.label]
    skipped_points = 0
    processed_points = 0

    for _, row in df_filtered.iterrows():
        frame, x, y, point, video, best_anchor_frame, class_id, class_name, u, v = row['frame'], row['x'], row['y'], row['Point'], row['video'], row['best_anchor_frame'], row['class_id'], row['class_name'], row['u'], row['v']

        coords_2D = Metashape.Vector([u, v])
        coords_3D = camera.unproject(coords_2D)            

        point_internal = surface.pickPoint(camera.center, coords_3D)
        if point_internal is None:
            print(f"Surface model could not be found. Camera: {camera.label}, u: {u}, v: {v}")
            skipped_points += 1
            continue  # Skip to next point if no projection

        # Transform 3D point to world coordinates
        point3D_world = chunk.crs.project(transform_matrix.mulp(point_internal))

        # Append data
        data.append({
            'frame': frame,
            'x': x,
            'y': y,
            'Point': point,
            'Camera': camera.label,
            'Video': video,
            'anchor_frame': best_anchor_frame,
            'class_id': class_id,
            'class_name': class_name,
            'u': u,
            'v': v,
            'latitude': point3D_world.y,
            'longitude': point3D_world.x,
            'altitude': point3D_world.z
        })
        processed_points += 1

    elapsed_time = time.time() - start_time
    print(f"[INFO] Camera '{camera.label}' processed {processed_points} points, skipped {skipped_points}. Time taken: {elapsed_time:.2f} seconds.")
    return data

# Main Processing
date = '20230309'
session = 'SE_Lek1'
DRONE = ['P1D1', 'P1D2']

doc = Metashape.app.document
chunk = doc.chunks[0]
surface = chunk.model

for drone in DRONE:
    # Define the input/output directory
    base_dir = f'/Volumes/SSD4/processed/Field_Recording_2023/SpatialRegistration/{date}/{session}/{drone}'

    # Get a sorted list of CSV files using glob
    csv_files = sorted(glob.glob(os.path.join(base_dir, '*_trajectories_uv.csv')))
    
    for csv_file in csv_files:
        csv_path = os.path.join(base_dir, csv_file)
        print(f"Processing file: {csv_file}")

        df = pd.read_csv(csv_path)

        # Group by camera label for fast lookups
        df_dict = {cam: group for cam, group in df.groupby('Camera')}

        # Cache transformation matrix
        transform_matrix = chunk.transform.matrix

        if not surface:
            raise ValueError("Surface model not found in chunk.")

        # Filter Cameras** (Keep only those with 7 label parts)
        valid_cameras = [
            camera for camera in chunk.cameras
            if len(camera.label.split('_')) == 7 and camera.label.split('_')[3] == drone
        ]

        # Parallel processing for cameras
        all_data = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_camera, camera, df_dict, surface, transform_matrix, chunk): camera.label for camera in valid_cameras}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    all_data.extend(result)

        if not all_data:
            print(f"[ERROR] No valid 3D world coordinates generated for {csv_file}. Check camera matching and surface model.")

        # Convert to DataFrame and save
        df_output = pd.DataFrame(all_data)
        output_csv_path = os.path.join(base_dir, csv_file.replace('_trajectories_uv.csv', '_3D_trajectories.csv'))
        df_output.to_csv(output_csv_path, index=False)

        print(f"3D world coordinates saved to {output_csv_path}")