import argparse

parser = argparse.ArgumentParser(description='A package for handling sensys speed camera')

parser.add_argument('--SetconfigFile', action="store", dest="config_file")

args = parser.parse_args()
print(args)