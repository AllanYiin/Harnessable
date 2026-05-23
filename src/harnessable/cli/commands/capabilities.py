from harnessable import HarnessProject


def run(args) -> int:
    project = HarnessProject.open(args.project)
    for file in sorted((project.path / "capabilities").glob("*.y*ml")):
        print(file.name)
    return 0
