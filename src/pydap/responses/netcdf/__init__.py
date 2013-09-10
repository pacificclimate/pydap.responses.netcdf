from pydap.model import *
from pydap.lib import walk, get_var
from pydap.responses.lib import BaseResponse
from itertools import chain, ifilter
from numpy.compat import asbytes
from collections import Iterator
from logging import debug
from datetime import datetime

from pupynere import netcdf_file, nc_generator
import numpy

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

                n = None if dim == unlim_dim else grid[dim].data.shape[0]
                self.nc.createDimension(dim, n)
                if not n:
                    self.nc.set_numrecs(grid[dim].data.shape[0])
                var = grid[dim]

                # and add dimension variable
                self.nc.createVariable(dim, var.dtype.char, (dim,), attributes=var.attributes)

            # finally add the grid variable itself
            base_var = grid[grid.name]
            var = self.nc.createVariable(base_var.name, base_var.dtype.char, base_var.dimensions, attributes=base_var.attributes)

        # Sequence types!
        for seq in walk(dataset, SequenceType):

            self.nc.createDimension(seq.name, None)
            self.nc.set_numrecs(len(seq))

            dim = seq.name,

            for child in seq.children():
                # detect the dtype
                if child.dtype.char == 'O':
                    raise Exception()
                    # is it a date?
                    if type([x for x in child.data[0]][0]) == datetime:
                        child.dtype = numpy.datetime64
                    else:
                        raise TypeError("Don't know how to handle numpy type {0}".format(child.dtype))
                        
                var = self.nc.createVariable(child.name, child.dtype.char, dim, attributes=child.attributes)

        self.headers.extend([
            ('Content-type', 'application/x-netcdf')
        ])
        # Optionally set the filesize header if possible
        try:
            self.headers.extend([('Content-length', self.nc.filesize)])
        except ValueError:
            pass

    def __iter__(self):
        nc = self.nc

        # Hack to find the variables if they're nested in the tree
        var2id = {}
        for recvar in nc.variables.keys():
            for dstvar in walk(self.dataset, BaseType):
                if recvar == dstvar.name:
                    var2id[recvar] = dstvar.id
                    continue

        def nonrecord_input():
            for varname in nc.non_recvars.keys():
                debug("Iterator for %s", varname)
                dst_var = get_var(self.dataset, var2id[varname]).data
                # skip 0-d variables
                if not dst_var.shape:
                    continue
                # Make sure that all elements of the list are iterators
                if isinstance(dst_var, Iterator):
                    yield dst_var
                else:
                    yield iter(dst_var)
            debug("Done with nonrecord input")

        # Create an generator for the record variables
        recvars = nc.recvars.keys()
        def record_generator(nc, dst, table):
            debug("record_generator() for dataset %s", dst)
            vars = [ iter(get_var(dst, table[varname])) for varname in nc.recvars.keys() ]
            while True:
                for var in vars:
                    try:
                        yield var.next()
                    except StopIteration:
                        raise

        more_input = record_generator(nc, self.dataset, var2id)

        # Create a single pipeline which includes the non-record and record variables
        pipeline = nc_generator(nc, chain(nonrecord_input(), more_input))

        # Generate the netcdf stream
        for block in pipeline:
            yield block
