from distutils.core import setup
setup(name="wildcatting",
      version="0.1",
      scripts=["go-wildcatting", "test/suite"],
      packages=["wildcatting",
                "wildcatting.model",
                "wildcatting.theme",
                "wildcatting.view"],
      )
