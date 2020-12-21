import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sensysSpeed", # Replace with your own username
    version="0.0.1",
    author="Taher Abbasi",
    author_email="abbasi.taher@gmail.com",
    description="A package for managing data coming from sensys speed camera",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={'gui_scripts': ['omission = sensysspeed.__main__:main']},
    python_requires='>=3.6',
)