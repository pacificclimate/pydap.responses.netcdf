from pkg_resources import resource_filename

import pytest
from netCDF4 import Dataset

from pydap.handlers.hdf5 import HDF5Handler

@pytest.fixture
def handler():
    fname = resource_filename(
        'pydap.responses.netcdf', 'test_data/tiny_bccaq2_wo_recvars.nc'
    )
    return HDF5Handler(fname)
