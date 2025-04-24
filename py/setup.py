from setuptools import setup, find_packages

setup(
    name="arcalyzer",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["main", "serial_reader", "frame"],
    install_requires=[
        "PyQt5",
        "pyqtgraph",
        "numpy",
        "pyserial",
    ],
    entry_points={
        "console_scripts": [
            "arcalyzer=main:main",
        ],
    },
    description="Arc analysis tool for ADC/GPIO signals",
    author="Your Name",
    author_email="your.email@example.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
