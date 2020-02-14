from setuptools import setup, find_packages

packages = find_packages()

setup(name = 'cddm',
      version = "0.0.1.dev0",
      description = 'Tools for cross-differential dynamic microscopy',
      author = 'Andrej Petelin',
      author_email = 'andrej.petelin@gmail.com',
      url="https://github.com/pypa/sampleproject",
      packages = packages,
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",],
      python_requires='=3.7',
      )
