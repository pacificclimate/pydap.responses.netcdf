from cStringIO import StringIO

from pupynere import netcdf_file
import numpy as np

from pydap.model import *
from pydap.lib import walk
from pydap.responses.lib import BaseResponse


class NetCDFResponse(BaseResponse):
    def __init__(self, dataset):
        BaseResponse.__init__(self, dataset)

        self.headers.extend([
            ('Content-description', 'dods_netcdf'),
            ('Content-type', 'application/x-netcdf'),
        ])

    def __iter__(self):
        buf = StringIO()
        f = netcdf_file(buf, 'w')

        nc_global = self.dataset.attributes.pop('NC_GLOBAL', {})
        for k, v in nc_global.items():
            if not isinstance(v, dict):
                setattr(f, k, v)
        for k, v in self.dataset.attributes.items():
            if not isinstance(v, dict):
                setattr(f, k, v)

        # Gridded data
        for grid in walk(self.dataset, GridType):
            for dim, map_ in grid.maps.items():
                if dim in f.dimensions:
                    continue

                length = map_.shape[0]
                try:
                    unlimited = self.dataset.attributes['DODS_EXTRA']['Unlimited_Dimensions']
                    if dim == unlimited:
                        length = None
                except KeyError:
                    pass

                f.createDimension(dim, length)
                var = f.createVariable(dim, map_.dtype.char, (dim,))
                var[:] = map_[:]
                for k, v in map_.attributes.items():
                    if not isinstance(v, dict):
                        setattr(var, k, v)

            var = f.createVariable(grid.name, grid.array.dtype.char, grid.dimensions)
            var[:] = grid.array[:]
            for k, v in grid.attributes.items():
                if not isinstance(v, dict):
                    setattr(var, k, v)

        f.flush()
        buf.seek(0)
        return iter([buf.getvalue()])


def save(dataset, filename):
    f = open(filename, 'w')
    for chunk in NetCDFResponse(dataset):
        f.write(chunk)
    f.close()


if __name__ == '__main__':
    from pydap.client import open_url

    dataset = open_url('http://podaac-opendap.jpl.nasa.gov/opendap/allData/oscar/preview/L4/oscar_third_deg/oscar_vel7001.nc.gz')
    save(dataset, 'oscar_vel2009.nc')
