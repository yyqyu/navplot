from distutils.core import setup
try:
    import py2exe
except ImportError:
    pass

packages = ["navplot"]

package_data = {"navplot": ["data/map.dat",
                            "data/navplot.xpm"]}

scripts=["bin/eadplot", "bin/gnavplot"]

setup(name="navplot",
      version="0.5.3",
      url="http://www.freeflight.org.uk/",
      author="Alan Sparrow",
      author_email="software@freeflight.org.uk",
      packages=packages,
      package_data=package_data,
      scripts=scripts)
