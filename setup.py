from distutils.core import setup
setup(name="wildcatting",
      version="0.1",
      scripts=["go-wildcatting"],
      packages=["wildcatting",
                "wildcatting.model",
                "wildcatting.theme",
                "wildcatting.view"],
      )
