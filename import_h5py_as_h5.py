import h5py as h5
#000130
#f = h5.File('data/OSIRIS/Quasi3D/b1_cyl_m-0-re-'+ '00016500' + '.h5',"r")
f = h5.File('e1_cyl_m-0-re-000130' + '.h5',"r")
#Field_dat = f['data']['16500']['fields']['B']['z'][:][0].astype(float)
datasetNames = [n for n in f.keys()]
field = datasetNames[-1]
Field_dat = f[field][:].astype(float)

print(Field_dat)