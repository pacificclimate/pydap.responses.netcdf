import os
import tempfile

import pytest
import netCDF4


@pytest.mark.timeout(2, method='signal')
def test_no_recvars(handler):
    env = {
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': 'tiny_bccaq2_wo_recvars.nc.nc'
    }
    resp = handler(environ=env, start_response = lambda x, y: x)
    with tempfile.NamedTemporaryFile('wb', delete=False, suffix='.nc') as tmp:
        for block in iter(resp):
            tmp.write(block)
    with netCDF4.Dataset(tmp.name) as dst:
        assert 'pr' in dst.variables
    os.remove(tmp.name)
