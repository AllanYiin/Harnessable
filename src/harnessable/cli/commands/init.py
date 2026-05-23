from harnessable import HarnessProject


def run(args) -> int:
    project = HarnessProject.create(args.path, args.name)
    print(project.path)
    return 0
