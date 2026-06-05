from __future__ import annotations

from harnessable.core.errors import NotFoundError

from .base import HarnessDetector
from .computational import AlwaysAllowDetector, FakeStreamingInferentialDetector, RegexDetector, RequiredFieldDetector
from .consequence import (
    ClaimEvidenceDetector,
    ContextGapDetector,
    OfferDisclosureDetector,
    MisreadSimulator,
    PowerAsymmetryDetector,
    ProvenanceMetadataDetector,
    ReleasePressureDetector,
    RollbackReadinessDetector,
    ScannerCoverageDetector,
    ScannerResultDetector,
    StakeholderHarmDetector,
)


class DetectorRegistry:
    def __init__(self) -> None:
        self._detectors: dict[str, HarnessDetector] = {}
        self.register(AlwaysAllowDetector())
        self.register(FakeStreamingInferentialDetector())
        self.register(ContextGapDetector())
        self.register(StakeholderHarmDetector())
        self.register(MisreadSimulator())
        self.register(PowerAsymmetryDetector())
        self.register(ReleasePressureDetector())
        self.register(ClaimEvidenceDetector())
        self.register(OfferDisclosureDetector())
        self.register(ProvenanceMetadataDetector())
        self.register(ScannerCoverageDetector())
        self.register(ScannerResultDetector())
        self.register(RollbackReadinessDetector())

    def register(self, detector: HarnessDetector) -> None:
        self._detectors[detector.detector_id] = detector

    def get(self, detector_id: str) -> HarnessDetector:
        try:
            return self._detectors[detector_id]
        except KeyError as exc:
            raise NotFoundError(f"detector not found: {detector_id}") from exc

    def create_from_config(self, config: dict) -> HarnessDetector:
        kind = config.get("type") or config.get("implementation") or "always_allow"
        if kind == "regex":
            return RegexDetector(config["field"], config["pattern"])
        if kind == "required_field":
            return RequiredFieldDetector(config["field"])
        if kind == "context_gap_detector":
            return ContextGapDetector(config.get("required_fields"))
        if kind in self._detectors:
            return self._detectors[kind]
        if kind == "inferential":
            return self._detectors["fake_inferential"]
        return self._detectors["always_allow"]
