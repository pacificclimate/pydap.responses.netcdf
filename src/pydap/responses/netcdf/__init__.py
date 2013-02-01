from pydap.model import *
from pydap.lib import walk, get_var
from pydap.responses.lib import BaseResponse
from itertools import chain
from numpy.compat import asbytes

from pupynere import netcdf_file, nc_generator

class NCResponse(BaseResponse):
    def __init__(self, dataset):
        BaseResponse.__init__(self, dataset)

        self.nc = netcdf_file(None)
        self.nc._attributes.update(self.dataset.attributes['NC_GLOBAL'])

        dimensions = [var.dimensions for var in walk(self.dataset) if isinstance(var, BaseType)]
        dimensions = set(reduce(lambda x, y: x+y, dimensions))
        try:
            unlim_dim = self.dataset.attributes['DODS_EXTRA']['Unlimited_Dimension']
        except:
            unlim_dim = None

        # Create the dimensions
        for dim in dimensions:
            n = None if dim == unlim_dim else len(self.dataset[dim])
            self.nc.createDimension(dim, n)
            # Create the unlimited dimension and corresponding variable
            if not n:
                self.nc.set_numrecs(len(self.dataset[dim]))
            if dim in self.dataset.keys():
                var = self.dataset[dim]
                self.nc.createVariable(dim, var.dtype.char, (dim,), attributes=var.attributes)

        # Create the variables
        for var in walk(self.dataset, BaseType):
            if var.name not in self.nc.variables.keys():
                v = self.nc.createVariable(var.name, var.dtype.char, var.dimensions, attributes=var.attributes)

        self.headers.extend([
            ('Content-description', 'dods_ascii'),
            ('Content-type', 'application/x-netcdf'),
            ('Content-length', self.nc.filesize),
        ])

    def __iter__(self):
        nc = self.nc

        var2id = {}
        for recvar in nc.variables.keys():
            for dstvar in walk(self.dataset, BaseType):
                if recvar == dstvar.name:
                    var2id[recvar] = dstvar.id
                    continue

        input = iter([ get_var(self.dataset, var2id[varname]).data for varname in nc.non_recvars.keys() ])

        recvars = nc.recvars.keys()

        def record_generator(nc, dst, table):
            vars = [ get_var(dst, table[varname]) for varname in nc.recvars.keys() ]
            for i in range(nc._recs):
                for var in vars:
                    yield var.data[i]

        more_input = record_generator(nc, self.dataset, var2id)
        pipeline = nc_generator(nc, chain(input, more_input))

        for block in pipeline:
            yield block
