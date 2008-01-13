from distutils.core import setup
setup(name="wildcatting",
      version="1.3",
      url="http://teichman.org/~peter/wildcatting/",
      author="Original Wildcatter",
      author_email="unknown@example.org",
      scripts=["go-wildcatting", "test/suite"],
      packages=["wildcatting",
                "wildcatting.model",
                "wildcatting.theme",
                "wildcatting.view"],
      )
