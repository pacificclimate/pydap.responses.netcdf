from pydap.model import *
from pydap.lib import walk, get_var
from pydap.responses.lib import BaseResponse
from itertools import chain, ifilter
from numpy.compat import asbytes
from collections import Iterator

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

        # GridType
        for grid in walk(dataset, GridType):

            # add dimensions
            for dim, map_ in grid.maps.items():
                if dim in self.nc.dimensions:
                    continue

                n = None if dim == unlim_dim else len(grid[dim])
                self.nc.createDimension(dim, n)
                if not n:
                    self.nc.set_numrecs(len(grid[dim]))
                var = grid[dim]

                # and add dimension variable
                self.nc.createVariable(dim, var.dtype.char, (dim,), attributes=var.attributes)

            # finally add the gird variable itself
            base_var = grid[grid.name]
            var = self.nc.createVariable(base_var.name, base_var.dtype.char, base_var.dimensions, attributes=base_var.attributes)

        # FIXME: Sequence types!

        self.headers.extend([
            ('Content-type', 'application/x-netcdf'),
            ('Content-length', self.nc.filesize),
        ])

    def __iter__(self):
        nc = self.nc

        # Hack to find the variables if they're nested in the tree
        var2id = {}
        for recvar in nc.variables.keys():
            for dstvar in walk(self.dataset, BaseType):
                if recvar == dstvar.name:
                    var2id[recvar] = dstvar.id
                    continue

        # Make a list of the non record variables to iterate over...
        input = [ get_var(self.dataset, var2id[varname]).data for varname in nc.non_recvars.keys() ]
        # ... but remove 0-d variables
        input = ifilter(lambda x: x.shape, input)
        # Make sure that all elements of the list are iterators
        input = [ i if isinstance(i, Iterator) else iter(i) for i in input ]
        # chain iterators together for the final response
        input = chain(*input)

        # Create an generator for the record variables
        recvars = nc.recvars.keys()
        def record_generator(nc, dst, table):
            vars = [ get_var(dst, table[varname]) for varname in nc.recvars.keys() ]
            for i in range(nc._recs):
                for var in vars:
                    yield var.data[i]

        more_input = record_generator(nc, self.dataset, var2id)

        # Create a single pipeline which includes the non-record and record variables
        pipeline = nc_generator(nc, chain(input, more_input))

        # Generate the netcdf stream
        for block in pipeline:
            yield block
