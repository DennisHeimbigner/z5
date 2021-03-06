import unittest
import sys
import numpy as np
import os
from shutil import rmtree

try:
    import zarr
    HAVE_ZARR = True
except ImportError:
    HAVE_ZARR = False

try:
    import z5py
except ImportError:
    sys.path.append('..')
    import z5py


class TestZarrCompatibility(unittest.TestCase):
    def setUp(self):
        self.path = 'f.zr'
        self.shape = (100, 100, 100)
        self.chunks = (10, 10, 10)

    def tearDown(self):
        try:
            rmtree(self.path)
        except OSError:
            pass

    @unittest.skipUnless(HAVE_ZARR, 'Requires zarr package')
    def test_read_zarr(self):
        import numcodecs
        from z5py.dataset import Dataset
        dtypes = list(Dataset._zarr_dtype_dict.values())
        compressions = Dataset.compressors_zarr
        zarr_compressors = {'blosc': numcodecs.Blosc(),
                            'zlib': numcodecs.Zlib(),
                            'raw': None,
                            'bzip2': numcodecs.BZ2()}

        for dtype in dtypes:
            for compression in compressions:
                data = np.random.randint(0, 127, size=self.shape).astype(dtype)
                # write the data with zarr
                key = 'test_%s_%s' % (dtype, compression)
                ar = zarr.open(os.path.join(self.path, key), mode='w',
                               shape=self.shape, chunks=self.chunks,
                               dtype=dtype, compressor=zarr_compressors[compression])
                ar[:] = data
                # read with z5py
                out = z5py.File(self.path)[key][:]
                self.assertEqual(data.shape, out.shape)
                self.assertTrue(np.allclose(data, out))

    @unittest.skipUnless(HAVE_ZARR, 'Requires zarr package')
    def test_write_zarr(self):
        from z5py.dataset import Dataset
        dtypes = list(Dataset._zarr_dtype_dict.values())
        compressions = Dataset.compressors_zarr

        for dtype in dtypes:
            for compression in compressions:
                data = np.random.randint(0, 127, size=self.shape).astype(dtype)
                key = 'test_%s_%s' % (dtype, compression)
                # read with z5py
                ds = z5py.File(self.path)
                ds.create_dataset(key, data=data, compression=compression,
                                  chunks=self.chunks)
                # read the data with z5py
                ar = zarr.open(os.path.join(self.path, key))
                out = ar[:]
                self.assertEqual(data.shape, out.shape)
                self.assertTrue(np.allclose(data, out))

    @unittest.skipUnless(HAVE_ZARR, 'Requires zarr package')
    def test_fillvalue(self):
        test_values = [0, 10, 42, 255]
        for val in test_values:
            key = 'test_%i' % val
            zarr.open(os.path.join(self.path, key), shape=self.shape,
                      fill_value=val, dtype='<u1')
            out = z5py.File(self.path)[key][:]
            self.assertEqual(self.shape, out.shape)
            self.assertTrue(np.allclose(val, out))


if __name__ == '__main__':
    unittest.main()
