import h5py

# Replace 'your_file.h5' with the path to your HDF5 file
#file_path = 'b1_cyl_m-0-re-00016500.h5'
#file_path = 'b1_cyl_m-0-re-000130.h5'
#file_path = 'charge_cyl_m-electrons-0-re-000067.h5'

# Open the HDF5 file in read mode
#with h5py.File(file_path, 'r') as hdf:
    # Function to recursively print the structure and data of the HDF5 file
    #def print_structure(name, obj):
        #if isinstance(obj, h5py.Dataset):
            #print(f"Dataset: {name} - Shape: {obj.shape} - Data: {obj[:]}")  # Displaying shape and data
        #elif isinstance(obj, h5py.Group):
            #print(f"Group: {name}")

    # Visit all items in the HDF5 file
    #hdf.visititems(print_structure)

#import h5py

# Replace 'your_file.h5' with the path to your HDF5 file
file_path = 'b1_cyl_m-0-re-00016500.h5'

# Open the HDF5 file in read mode
#with h5py.File(file_path, 'r') as hdf:
    # Print all root level object names (aka keys) 
    #print("Keys: %s" % hdf.keys())

    # Assuming you want to read a specific dataset
    #dataset_name = 'your_dataset_name'  # Replace with your dataset name
    #data = hdf[dataset_name][:]
    
    # Print the data
    #print("Data from {}: {}".format(dataset_name, data))



 
with h5py.File(file_path, 'r') as f:
    # Get the attributes of a specific dataset
    #dataset = f[file_path]
    #attributes = list(dataset.attrs.keys())
    #print(attributes)

    # Get the attributes of a group
    group = f['data']['16500']
    attributes = list(group.attrs.keys())
    print(attributes)