#!/usr/bin/env python

import os, sys
import glob
import unittest

def get_tests(dir):
    ret = []

    pattern = os.path.join(dir, "test_*.py")
    for file in glob.glob(pattern):
        filename = os.path.basename(file)
        filename = filename[:-3]
        ret.append(filename)

    return ret
    
if __name__ == "__main__":
    cwd = os.getcwd()
    if not os.path.exists(os.path.join(cwd, "go-wildcatting")):
        print "Please run me from the toplevel of a Wildcatting tree."
        sys.exit(1)

    wildcatdir = cwd
    testdir = os.path.join(wildcatdir, "test")

    for dir in (wildcatdir, testdir):
        if dir not in sys.path:
            sys.path[-1] = cwd

    modules = get_tests(testdir)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(modules)
    
    unittest.TextTestRunner(verbosity=2).run(suite)
