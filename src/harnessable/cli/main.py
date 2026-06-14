from __future__ import annotations

import argparse

from harnessable.cli.commands import audit, capabilities, eval, fallback, init, replay, rules, trace, validate
from harnessable.console.server import run as run_console


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harnessable")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("path")
    init.add_argument("--name", default="Harnessable Project")
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    open_cmd = sub.add_parser("open")
    open_cmd.add_argument("path")
    rules_cmd = sub.add_parser("rules")
    rules_cmd.add_argument("--project", default=".")
    rules_sub = rules_cmd.add_subparsers(dest="rules_command", required=True)
    rules_sub.add_parser("list")
    rules_add = rules_sub.add_parser("add")
    rules_add.add_argument("source")
    rules_add.add_argument("--preview", action="store_true")
    rules_apply = rules_sub.add_parser("apply")
    rules_apply.add_argument("preview_id")
    capabilities_cmd = sub.add_parser("capabilities")
    capabilities_cmd.add_argument("--project", default=".")
    capabilities_cmd.add_argument("capabilities_command", choices=["list"])
    fallback_cmd = sub.add_parser("fallback")
    fallback_cmd.add_argument("--project", default=".")
    fallback_sub = fallback_cmd.add_subparsers(dest="fallback_command", required=True)
    fallback_sub.add_parser("validate")
    eval_cmd = sub.add_parser("eval")
    eval_cmd.add_argument("--project", default=".")
    eval_sub = eval_cmd.add_subparsers(dest="eval_command", required=True)
    eval_run = eval_sub.add_parser("run")
    eval_run.add_argument("evals")
    replay_cmd = sub.add_parser("replay")
    replay_cmd.add_argument("--project", default=".")
    replay_sub = replay_cmd.add_subparsers(dest="replay_command", required=True)
    replay_run = replay_sub.add_parser("run")
    replay_run.add_argument("run_id")
    audit_cmd = sub.add_parser("audit")
    audit_cmd.add_argument("--project", default=".")
    audit_sub = audit_cmd.add_subparsers(dest="audit_command", required=True)
    audit_export = audit_sub.add_parser("export")
    audit_export.add_argument("run_id")
    trace_cmd = sub.add_parser("trace")
    trace_cmd.add_argument("--project", default=".")
    trace_sub = trace_cmd.add_subparsers(dest="trace_command", required=True)
    trace_show = trace_sub.add_parser("show")
    trace_show.add_argument("run_id")
    trace_promote_preview = trace_sub.add_parser("promote-preview")
    trace_promote_preview.add_argument("run_id")
    trace_promote_apply = trace_sub.add_parser("promote-apply")
    trace_promote_apply.add_argument("preview_id")
    console = sub.add_parser("console")
    console.add_argument("project")
    console.add_argument("--host", default="127.0.0.1")
    console.add_argument("--port", type=int, default=8765)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "init":
        return init.run(args)
    if args.command in {"validate", "open"}:
        return validate.run(args)
    if args.command == "rules":
        return rules.run(args)
    if args.command == "capabilities":
        return capabilities.run(args)
    if args.command == "fallback":
        return fallback.run(args)
    if args.command == "eval" and args.eval_command == "run":
        return eval.run(args)
    if args.command == "replay" and args.replay_command == "run":
        return replay.run(args)
    if args.command == "audit" and args.audit_command == "export":
        return audit.run(args)
    if args.command == "trace":
        return trace.run(args)
    if args.command == "console":
        run_console(args.host, args.port)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
