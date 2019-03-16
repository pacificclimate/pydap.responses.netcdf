from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.rst')).read()

version = '0.5.4'

install_requires = [
    'numpy',
    'pupynere_pdp >=1.1.4',
    'pydap_pdp >=3.2.1'
]

setup(name='pydap.responses.netcdf',
    version=version,
    description="Pydap response that returns a NetCDF representation of the dataset",
    long_description=README + '\n\n' + NEWS,
    classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords='netcdf pydap opendap dods',
    author='James Hiebert',
    author_email='james@hiebert.name',
    license='MIT',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    package_data={'': ['test_data/*']},
    namespace_packages = ['pydap', 'pydap.responses'],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    entry_points="""
        [pydap.response]
        nc = pydap.responses.netcdf:NCResponse
    """,
)
