"""
Setup script for Cython compilation of license module
======================================================
Compiles license.py to binary .pyd (Windows) or .so (Linux)
to prevent reverse engineering.

Usage:
    python setup_cython.py build_ext --inplace

Output:
    - license.cp311-win_amd64.pyd (Windows)
    - license.cpython-311-x86_64-linux-gnu.so (Linux)
    
The compiled module replaces the original Python file,
making it much harder to reverse engineer.
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

# Extensions to compile
extensions = [
    Extension(
        "src.utils.license",
        ["src/utils/license.py"],
        # Optimization flags
        extra_compile_args=['-O3'],
        # Include directories (if needed)
        include_dirs=[np.get_include()],
    )
]

setup(
    name="ArtNetController License Module",
    version="1.0.0",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': "3",
            'embedsignature': True,
            'boundscheck': False,
            'wraparound': False,
            'cdivision': True,
            'optimize.use_switch': True,
            'optimize.unpack_method_calls': True,
        },
        build_dir="build",
    ),
    zip_safe=False,
)
