from harnessable.tool_policy import (
    CODE_EXECUTION_CAPABILITY_CLASS,
    ExecutionEvidenceRequirement,
    build_execution_evidence_requirement,
    execution_policy_task_text,
    requires_code_execution_evidence,
)


def test_requires_code_execution_evidence_for_coding_and_test_tasks():
    assert requires_code_execution_evidence("請修改 Python 程式並跑測試")
    assert requires_code_execution_evidence("Implement the provider fix and run pytest")
    assert requires_code_execution_evidence("請修改")
    assert requires_code_execution_evidence("請撰寫代碼並產出可執行結果")
    assert requires_code_execution_evidence("請建立 React 原型，新增 UI 與測試")
    assert requires_code_execution_evidence("Create a Vite app prototype")


def test_does_not_require_execution_evidence_for_explanation_or_planning_only_tasks():
    assert not requires_code_execution_evidence("為何目前只會寫出代碼而不會執行?")
    assert not requires_code_execution_evidence("為何撰寫代碼的結果沒有自動執行?")
    assert not requires_code_execution_evidence("Evaluate the MXC adoption plan")
    assert not requires_code_execution_evidence("請整理這段 Python 函式的重構方向。")
    assert not requires_code_execution_evidence("請撰寫 README 文件")


def test_build_execution_evidence_requirement_is_runtime_neutral():
    requirement = build_execution_evidence_requirement(
        task_text="Fix the React component and run tests",
        enabled=True,
        code_execution_available=True,
        required_tool_names=["standard.code.container_exec"],
        surface="chat",
    )

    assert requirement is not None
    assert requirement.required_capability_classes == [CODE_EXECUTION_CAPABILITY_CLASS]
    assert requirement.to_dict()["requires_execution_evidence"] is True
    assert requirement.to_dict()["required_tool_names"] == ["standard.code.container_exec"]
    assert requirement.to_dict()["surface"] == "chat"


def test_build_execution_evidence_requirement_respects_enablement_and_availability():
    assert build_execution_evidence_requirement(task_text="run pytest", enabled=False, code_execution_available=True) is None
    assert build_execution_evidence_requirement(task_text="run pytest", enabled=True, code_execution_available=False) is None
    assert build_execution_evidence_requirement(task_text="explain the code", enabled=True, code_execution_available=True) is None


def test_execution_evidence_requirement_accepts_legacy_payload():
    requirement = ExecutionEvidenceRequirement.from_dict(
        {
            "requires_execution_evidence": True,
            "required_tool_names": ["tool.code"],
            "reason": "coding_task_requires_executable_evidence",
            "surface": "agent",
        }
    )

    assert requirement.schema_version == 1
    assert requirement.required_capability_classes == [CODE_EXECUTION_CAPABILITY_CLASS]
    assert requirement.required_tool_names == ["tool.code"]


def test_execution_policy_task_text_includes_recent_profile_history():
    task_text = execution_policy_task_text(
        "final prompt",
        tuple({"content": f"message {index}"} for index in range(8)),
        max_messages=3,
    )

    assert task_text == "message 5\nmessage 6\nmessage 7\nfinal prompt"
