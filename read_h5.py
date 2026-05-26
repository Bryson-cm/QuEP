#Read levels of h5 file

import h5py

def get_keys_at_level(file_path, level):
    keys_at_level = []

    # Open the HDF5 file in read mode
    with h5py.File(file_path, 'r') as hdf:
        def visit_items(name, obj):
            # Count the depth of the current object
            current_level = name.count('/')

            if current_level == level:
                keys_at_level.append(name)

        # Visit all items in the HDF5 file
        hdf.visititems(visit_items)

    return keys_at_level

# Usage
file_path = 'b1_cyl_m-0-re-00016500.h5'  # Replace with your file path
level = 1  # Specify the level you want to inspect (0 for top level)
keys = get_keys_at_level(file_path, level)
print(f"Keys at level {level}: {keys}")