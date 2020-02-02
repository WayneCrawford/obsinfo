import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="obsinfo",
    version="0.102",
    author="Wayne Crawford",
    author_email="crawford@ipgp.fr",
    description="Tools for documenting ocean bottom seismometer experiments and creating meta/data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/obsinfo",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
          'obspy',
          'pyyaml',
          'jsonschema'
      ],
    python_requires='>=3',
    classifiers=(
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience : Science/Research",
        "Intended Audience : Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language::English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics"
    ),
    keywords='seismology OBS'
)