import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

version = {}
with open("obsinfo/version.py") as fp:
    exec(fp.read(), version)

setuptools.setup(
    name="obsinfo",
    version=version['__version__'],
    author="Wayne Crawford",
    author_email="crawford@ipgp.fr",
    description="Tools for documenting ocean bottom seismometer experiments "
                "and creating meta/data",
    long_description=long_description,
    long_description_content_type="text/x-rst; charset=UTF-8",
    url="https://github.com/WayneCrawford/obsinfo",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
          'obspy>=1.1',
          'pyyaml>=5.0',
          'jsonschema>=2.6',
          'jsonref>=0.2'
      ],
    entry_points={
        'console_scripts': [
            'obsinfo-validate=obsinfo.misc.info_files:_validate_script',
            'obsinfo-print=obsinfo.misc.print:_print_script',
            'obsinfo-makeSTATIONXML=obsinfo.network:_make_stationXML_script',
            'obsinfo-makescripts_SDPCHAIN=obsinfo.addons.SDPCHAIN:_console_script',
            'obsinfo-makescripts_LCHEAPO=obsinfo.addons.LCHEAPO:_console_script',
            'obsinfo-makescripts_LC2SDS=obsinfo.addons.LC2SDS:_console_script'
        ]
    },
    python_requires='>=3',
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    classifiers=(
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics"
    ),
    keywords='seismology OBS'
)
