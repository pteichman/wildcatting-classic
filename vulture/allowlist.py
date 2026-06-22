# vulture allowlist — names referenced dynamically or via framework introspection

from wildcatting.cmdparse import Command

# OptionParser overrides: called polymorphically by the parent class
Command("").set_usage(None)
Command("").get_usage()
