import setuptools

packages=setuptools.find_packages()

setuptools.setup(
    name='pySCS',
    version='0.1',
    packages=['pySCS'],
    summary='A Python-based framework for automated security control selection.',
    long_description=open('README.md').read(),
    license='MIT License',
    url="https://github.com/davevs/pySCS",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
	"Environment :: Console",
	"Intended Audience :: Developers",
	"Topic :: Security",
    ],
    python_requires='>=3',
    include_package_data=True
)
