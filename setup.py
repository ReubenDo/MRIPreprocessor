#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages



requirements = [
    'antspyx',
    'nibabel',
    'scipy',
    'SimpleITK<2',
    'HD-BET @ git+https://github.com/ReubenDo/HD-BET#egg=HD-BET',
]

setup(
    author="Reuben Dorent",
    author_email='reuben.dorent@kcl.ac.uk',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description=(
        "Simple preprocessor for coregistration and skull-stripping"
    ),
    install_requires=requirements,
    license="MIT license",
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='MRIPreprocessor',
    name='MRIPreprocessor',
    packages=find_packages(include=['MRIPreprocessor']),
    setup_requires=[],
    tests_require=[],
    url='https://github.com/ReubenDo/MRIPreprocessor',
    version='0.0.4',
    zip_safe=False,
)
