import datetime
import os
import time 
import unittest

import numpy

import cf

class DimensionCoordinateTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')

        dim1 = cf.DimensionCoordinate()
        dim1.standard_name = 'latitude'
        a = numpy.array([-30, -23.5, -17.8123, -11.3345, -0.7, -0.2, 0, 0.2, 0.7, 11.30003, 17.8678678, 23.5, 30])
        dim1.set_data(cf.Data(a, 'degrees_north'))
        bounds = cf.Bounds()
        b = numpy.empty(a.shape + (2,))
        b[:, 0] = a - 0.1
        b[:, 1] = a + 0.1
        bounds.set_data(cf.Data(b))
        dim1.set_bounds(bounds)
        self.dim = dim1

    def test_DimensionCoordinate__repr__str__dump(self):
        f = cf.read(self.filename)[0]
        x = f.dimension_coordinates('X').value()
        
        _ = repr(x)
        _ = str(x)
        _ = x.dump(display=False)

        self.assertTrue(x.isdimension)

           
    def test_DimensionCoordinate_convert_reference_time(self):
        self.assertTrue(False)

           
    def test_DimensionCoordinate_roll(self):
        f = cf.read(self.filename)[0]
        x = f.dimension_coordinates('X').value()

        with self.assertRaises(Exception):
            x.roll(0, 3)

        x.period(360)
        _ = x.roll(0, 3)
        _ = x.roll(-1, 3)
        with self.assertRaises(Exception):
            _ = x.roll(2, 3)
        
        a = x[0]
        _ = a.roll(0, 3)
        self.assertTrue(a.roll(0, 3, inplace=True) is None)

        _ = x.roll(0, 0)
        _ = x.roll(0, 3, inplace=True)
        self.assertTrue(x.roll(0, 0, inplace=True) is None)

        _ = x._centre(360)
        _ = x.flip()._centre(360) 

                
    def test_DimensionCoordinate_cellsize(self):
        d = self.dim.copy()

        c = d.cellsize
        self.assertTrue(numpy.allclose(c.array, 0.2))
        
        d.del_bounds()
        c = d.cellsize
        self.assertTrue(numpy.allclose(c.array, 0))

                
    def test_DimensionCoordinate_bounds(self):
        f = cf.read(self.filename)[0]
        x = f.dimension_coordinates('X').value()
        
        _ = x.upper_bounds
        _ = x.lower_bounds

        self.assertTrue(x.increasing)
        
        y = x.flip()
        self.assertTrue(y.decreasing)
        self.assertTrue(y.upper_bounds.equals(x.upper_bounds[::-1]))
        self.assertTrue(y.lower_bounds.equals(x.lower_bounds[::-1]))
        
        c = x.cellsize
        c = y.cellsize

        y.del_bounds()

        b = y.create_bounds()

        
    def test_DimensionCoordinate_properties(self):
        f = cf.read(self.filename)[0]
        x = f.dimension_coordinates('X').value()
        
        x.positive = 'up'
        self.assertTrue(x.positive == 'up')
        del x.positive

        x.axis = 'Z'
        self.assertTrue(x.axis == 'Z')
        del x.axis

        x.axis = 'T'
        self.assertTrue(x.ndim == 1)

    
    def test_DimensionCoordinate_insert_dimension(self):
        f = cf.read(self.filename)[0]
        x = f.dimension_coordinates('X').value()
        
        self.assertTrue(x.shape == (9,))
        self.assertTrue(x.bounds.shape == (9, 2))
        
        y = x.insert_dimension(0)
        self.assertTrue(y.shape == (1, 9))
        self.assertTrue(y.bounds.shape == (1, 9, 2), y.bounds.shape)
        
        x.insert_dimension(-1, inplace=True)
        self.assertTrue(x.shape == (9, 1))
        self.assertTrue(x.bounds.shape == (9, 1, 2), x.bounds.shape)            

        
    def test_DimensionCoordinate_binary_operation(self):
        f = cf.read(self.filename)[0]
        x = f.dimension_coordinates('X').value()
        
        d = x.array
        b = x.bounds.array
        d2= numpy.expand_dims(d, -1)
        
        # --------------------------------------------------------
        # Out-of-place addition
        # --------------------------------------------------------
        c = x + 2
        self.assertTrue((c.array == d + 2).all())
        self.assertTrue((c.bounds.array == b + 2).all())
        
        c = x + x
        self.assertTrue((c.array == d + d).all())
        self.assertTrue((c.bounds.array == b + d2).all())
        
        c = x + 2
        self.assertTrue((c.array == d + 2).all())
        self.assertTrue((c.bounds.array == b + 2).all())
        
        self.assertTrue((x.array == d).all())
        self.assertTrue((x.bounds.array == b).all())
        
        # --------------------------------------------------------
        # In-place addition
        # --------------------------------------------------------
        x += 2
        self.assertTrue((x.array == d + 2).all())
        self.assertTrue((x.bounds.array == b + 2).all())
        
        x += x
        self.assertTrue((x.array == (d+2) * 2).all())
        self.assertTrue((x.bounds.array == b+2 + d2+2).all())
        
        x += 2
        self.assertTrue((x.array == (d+2)*2 + 2).all())
        self.assertTrue((x.bounds.array == b+2 + d2+2 + 2).all())
        
        # --------------------------------------------------------
        # Out-of-place addition (no bounds)
        # --------------------------------------------------------
        f = cf.read(self.filename)[0]
        x = f.dimension_coordinates('X').value()
        x.del_bounds()
        
        self.assertFalse(x.has_bounds())
        
        d = x.array
        
        c = x + 2
        self.assertTrue((c.array == d + 2).all())
        
        c = x + x
        self.assertTrue((c.array == d + d).all())
        
        c = x + 2
        self.assertTrue((c.array == d + 2).all())
        
        self.assertTrue((x.array == d).all())
        
        # --------------------------------------------------------
        # In-place addition (no bounds)
        # --------------------------------------------------------
        x += 2
        self.assertTrue((x.array == d + 2).all())
        
        x += x
        self.assertTrue((x.array == (d+2) * 2).all())
        
        x += 2
        self.assertTrue((x.array == (d+2)*2 + 2).all())


#--- End: class

if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cf.environment()
    print()
    unittest.main(verbosity=2)
