from pathlib import Path

from harnessable import HarnessProject


def run(args) -> int:
    project = HarnessProject.open(args.project)
    if args.rules_command == "list":
        for file in sorted((project.path / "rules").glob("*.y*ml")):
            print(file.name)
        return 0
    if args.rules_command == "add":
        preview = project.import_bundle_preview(args.source)
        print(preview.preview_id)
        if not args.preview:
            result = project.apply_import(preview.preview_id)
            print(result.target_path)
        return 0
    if args.rules_command == "apply":
        result = project.apply_import(args.preview_id)
        print(result.target_path if result.applied else ";".join(result.errors))
        return 0 if result.applied else 1
    return 1
