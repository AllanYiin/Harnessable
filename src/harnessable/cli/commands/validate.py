from harnessable import HarnessProject


def run(args) -> int:
    project = HarnessProject.open(args.path)
    print(f"{project.manifest.name}:{project.manifest.status.value}:{project.path.resolve()}")
    return 0
