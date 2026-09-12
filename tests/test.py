import config
import argparse

print(config.PROJECTS)
parser = argparse.ArgumentParser(description=config.APP_NAME)
print(parser)
parser.add_argument('--project-key', choices=config.PROJECTS)
print(parser)
parser.add_argument('--object-type', type=int, choices=config.OBJECT_TYPES, default=12)
print(parser)
args = parser.parse_args()
print(args)
project_key = args.project_key
print(args.project_key)