from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from harnessable.identity import Principal


class SecretProvider(Protocol):
    def get(self, name: str) -> str | None: ...


@dataclass(frozen=True)
class SecretAccessEnvelope:
    secret_ref: str
    provider_id: str
    purpose: str | None = None
    principal_id: str | None = None
    run_id: str | None = None
    gateway_call_id: str | None = None
    approved: bool = False
    audit_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "secret_ref": self.secret_ref,
            "provider_id": self.provider_id,
            "purpose": self.purpose,
            "principal_id": self.principal_id,
            "run_id": self.run_id,
            "gateway_call_id": self.gateway_call_id,
            "approved": self.approved,
            "audit_ref": self.audit_ref,
        }


@dataclass(frozen=True)
class StaticSecretProvider:
    values: dict[str, str] = field(default_factory=dict)

    def get(self, name: str) -> str | None:
        return self.values.get(name)


@dataclass(frozen=True)
class EnvSecretProvider:
    prefix: str = ""

    def get(self, name: str) -> str | None:
        key = f"{self.prefix}{name}" if self.prefix else name
        return os.environ.get(key)


@dataclass
class AuditedSecretProvider:
    provider: SecretProvider
    provider_id: str
    audit_log: list[SecretAccessEnvelope] = field(default_factory=list)

    def get(
        self,
        name: str,
        *,
        purpose: str | None = None,
        principal: Principal | None = None,
        principal_id: str | None = None,
        run_id: str | None = None,
        gateway_call_id: str | None = None,
        approved: bool = False,
        audit_ref: str | None = None,
    ) -> str | None:
        envelope = SecretAccessEnvelope(
            secret_ref=name,
            provider_id=self.provider_id,
            purpose=purpose,
            principal_id=principal.principal_id if principal else principal_id,
            run_id=run_id,
            gateway_call_id=gateway_call_id,
            approved=approved,
            audit_ref=audit_ref,
        )
        self.audit_log.append(envelope)
        return self.provider.get(name)
