"""Scheme Pack Execution Engine (ARCHITECTURE_V2 §7).

Executes declarative scheme packs using the 9 closed primitives in pure Python
without dynamic evaluation (zero eval/exec).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from docuready.domain.enums import (
    EvidenceState,
    MatchGrade,
    MaxSeverity,
    Raw,
    Readiness,
    ReasonCode,
    Status,
)
from docuready.domain.models import (
    AuditResult,
    DocumentType,
    EvidenceProvenance,
    ExtractedDocument,
    ExtractedField,
    Finding,
    FindingStatus,
    Severity,
)
from docuready.outcome.resolver import resolve_outcome, resolve_readiness, weakest_evidence
from docuready.rules.loader import load_pack
from docuready.rules.primitives import (
    PRIMITIVE_REGISTRY,
    ExecutionContext,
    PrimitiveResult,
    get_document,
    get_field_from_doc,
    parse_field_spec,
    resolve_doc_type,
)
from docuready.rules.schema import (
    PackManifest,
    ParameterDeclaration,
    RuleDefinition,
    SourceDefinition,
    SourceManifest,
)
from docuready.rules.slot_validator import validate_packet_slots


def _resolve_param_val(val: Any, parameters: Dict[str, Any]) -> Any:
    """Recursively resolve $param references from pack parameter declarations."""
    if isinstance(val, str) and val.startswith("$") and not val.startswith("$$"):
        param_name = val[1:]
        if param_name in parameters:
            p_obj = parameters[param_name]
            if isinstance(p_obj, ParameterDeclaration):
                return p_obj.value
            if isinstance(p_obj, dict) and "value" in p_obj:
                return p_obj.get("value")
            return p_obj
        return val
    if isinstance(val, list):
        return [_resolve_param_val(item, parameters) for item in val]
    if isinstance(val, dict):
        return {k: _resolve_param_val(v, parameters) for k, v in val.items()}
    return val


class PackExecutionEngine:
    """Deterministic, explainable execution engine for scheme packs."""

    def __init__(
        self,
        pack: Union[PackManifest, Path, str],
        sources: Optional[Union[SourceManifest, Path, str]] = None,
        allow_draft: bool = True,
    ):
        if isinstance(pack, (Path, str)):
            pack_dir = Path(pack)
            loaded_pack, loaded_sources = load_pack(pack_dir)
            self.pack = loaded_pack
            self.sources = loaded_sources
            self.pack_dir: Optional[Path] = pack_dir
        else:
            self.pack = pack
            self.sources = sources if isinstance(sources, SourceManifest) else None
            self.pack_dir = None

        self._source_map: Dict[str, SourceDefinition] = {}
        if self.sources and hasattr(self.sources, "sources"):
            for s in self.sources.sources:
                self._source_map[s.id] = s

    def _format_statutory_reference(self, rule: RuleDefinition) -> str:
        """Format citation reference into human-readable statutory reference string."""
        src_id = rule.citation.source
        src_def = self._source_map.get(src_id)
        clause = rule.citation.clause or (src_def.clause if src_def else "")

        if src_def:
            title = src_def.title
            if clause:
                return f"{title}, {clause}"
            return title
        if clause:
            return f"Citation {src_id}, {clause}"
        return f"Citation {src_id}"

    def _format_remediation(self, rule: RuleDefinition) -> str:
        """Format remediation metadata into action guidance."""
        rem = rule.remediation
        if rem.steps:
            return " ".join(rem.steps)
        if rem.replacement_document:
            return f"Obtain and upload a valid {rem.replacement_document} from {rem.authority}."
        return f"Verify document credentials with {rem.authority}."

    def _evaluate_exempt_when(
        self,
        exempt_when: Dict[str, Any],
        documents: Dict[Any, ExtractedDocument],
    ) -> Tuple[bool, Optional[EvidenceState]]:
        """Evaluate exempt_when clause against applicant evidence.

        Returns (is_exempt, evidence_state).
        """
        fact = exempt_when.get("fact", "")
        in_values = exempt_when.get("in", [])
        if isinstance(in_values, (str, int, float)):
            in_values = [str(in_values)]
        allowed_set = {str(v).strip().upper() for v in in_values}

        doc_name, f_name = parse_field_spec(fact, ["APPLICATION_FORM", "CASTE_CERT"])
        candidate_docs = [doc_name] if doc_name else ["APPLICATION_FORM", "CASTE_CERT"]

        for d_name in candidate_docs:
            doc = get_document(documents, d_name)
            if doc and doc.status == "VALID":
                f = get_field_from_doc(doc, f_name)
                if f and f.raw_value:
                    val = f.raw_value.strip().upper()
                    # Check substring or token match (e.g. SC in "SCHEDULED CASTE (SC)")
                    is_match = any(
                        target in val or val in target for target in allowed_set
                    )
                    if is_match:
                        ev_state = (
                            EvidenceState.UNCERTAIN
                            if f.is_uncertain
                            else EvidenceState.VERIFIED
                        )
                        return True, ev_state

        return False, None

    def validate_packet(
        self,
        packet_id: str,
        documents: Dict[Any, ExtractedDocument],
        as_of: Optional[date] = None,
        audit_date: Optional[date] = None,
        timestamp: Optional[str] = None,
    ) -> AuditResult:
        """Execute the pack's declarative rules against an applicant document packet."""
        effective_as_of = as_of or audit_date or date(2026, 11, 13)
        context = ExecutionContext(as_of=effective_as_of, scheme_name=self.pack.pack_id)

        findings: List[Finding] = []

        # 1. Slot validation (check required slots per pack manifest)
        req_doc_types: List[DocumentType] = []
        if self.pack.doc_slots:
            for s_name, s_def in self.pack.doc_slots.items():
                if s_def.required:
                    dt = resolve_doc_type(s_name)
                    if dt:
                        req_doc_types.append(dt)

        slot_findings, mismatched_slots = validate_packet_slots(
            documents, req_doc_types, emit_for_unreadable=False
        )
        for sf in slot_findings:
            findings.append(sf)

        # 2. Declarative Rule Execution
        parameters = self.pack.parameters or {}

        for rule in self.pack.rules:
            # Check primitive existence in closed registry
            if rule.primitive not in PRIMITIVE_REGISTRY:
                raise ValueError(
                    f"Unknown or unregistered primitive '{rule.primitive}' in rule '{rule.id}'"
                )

            # Resolve parameters
            resolved_inputs = _resolve_param_val(rule.inputs, parameters)
            resolved_params = _resolve_param_val(rule.params, parameters)

            # Check exemption
            is_exempt = False
            exempt_ev_state = None
            if rule.exempt_when:
                is_exempt, exempt_ev_state = self._evaluate_exempt_when(
                    rule.exempt_when, documents
                )

            if is_exempt:
                if exempt_ev_state is EvidenceState.UNCERTAIN:
                    # Uncertain category evidence must abstain to REVIEW
                    raw_result = Raw.INDETERMINATE
                    match_grade = MatchGrade.AMBIGUOUS
                    weakest = EvidenceState.UNCERTAIN
                    finding_msg = f"Potential exemption under {rule.id}, but category evidence is uncertain. Verification required."
                    ev_list = []
                else:
                    raw_result = Raw.EXEMPT
                    match_grade = None
                    weakest = EvidenceState.VERIFIED
                    finding_msg = (
                        f"Candidate satisfies scheme criteria: exempt under statutory guidelines."
                    )
                    ev_list = []
                field_name = rule.inputs.get("field", "EXEMPTION").upper()
                docs_involved = [
                    (resolve_doc_type(d).value if resolve_doc_type(d) else d)
                    for d in rule.inputs.get("docs", [])
                ]
            else:
                eval_fn = PRIMITIVE_REGISTRY[rule.primitive]
                prim_res: PrimitiveResult = eval_fn(
                    documents, resolved_inputs, resolved_params, context
                )
                raw_result = prim_res.raw
                match_grade = prim_res.match_grade
                weakest = prim_res.evidence_state or EvidenceState.VERIFIED
                finding_msg = prim_res.message or f"Rule {rule.id} evaluation completed."
                ev_list = prim_res.evidence
                field_name = prim_res.field_name or rule.inputs.get("field", "GENERAL").upper()
                docs_involved = prim_res.documents_involved

            stat_ref = self._format_statutory_reference(rule)
            remediation = self._format_remediation(rule)

            # Resolve outcome using canonical truth table
            resolved = resolve_outcome(
                raw=raw_result,
                weakest_evidence=weakest,
                max_severity=rule.max_severity,
                match_grade=match_grade,
                exemption_reason="CATEGORY_EXEMPTION",
            )

            # Map to legacy severity / penalty
            if resolved.status is Status.FAIL:
                sev = Severity.FATAL if rule.max_severity is MaxSeverity.FAIL and raw_result is Raw.DOC_ABSENT else Severity.CRITICAL
                pen = 35 if sev is Severity.FATAL else 25
                legacy_stat = FindingStatus.FAIL
            elif resolved.status is Status.WARN:
                sev = Severity.WARNING
                pen = 5
                legacy_stat = FindingStatus.REVIEW
            elif resolved.status is Status.REVIEW:
                sev = Severity.REVIEW
                pen = 10
                legacy_stat = FindingStatus.REVIEW
            elif resolved.status is Status.MISSING:
                sev = Severity.FATAL
                pen = 35
                legacy_stat = FindingStatus.FAIL
            elif resolved.status is Status.NOT_APPLICABLE:
                sev = Severity.INFO
                pen = 0
                legacy_stat = FindingStatus.PASS
            else:
                sev = Severity.INFO
                pen = 0
                legacy_stat = FindingStatus.PASS

            finding = Finding(
                rule_id=rule.id,
                rule_name=rule.id,
                status=legacy_stat,
                severity=sev,
                penalty=pen,
                field=field_name,
                documents_involved=docs_involved,
                message=finding_msg,
                evidence=ev_list,
                remediation=remediation,
                statutory_reference=stat_ref,
                match_grade=match_grade,
            )
            finding.set_resolution(
                raw=raw_result,
                status=resolved.status,
                reason_code=resolved.reason_code,
                match_grade=match_grade,
            )
            findings.append(finding)

        # 3. Overall Readiness and Score
        score = 100 - sum(f.penalty for f in findings)
        score = max(0, min(100, score))

        legacy_statuses = [f.legacy_status_snapshot for f in findings]
        summary_counts = {
            FindingStatus.PASS.value: sum(1 for s in legacy_statuses if s == FindingStatus.PASS.value),
            FindingStatus.REVIEW.value: sum(1 for s in legacy_statuses if s == FindingStatus.REVIEW.value),
            FindingStatus.FAIL.value: sum(1 for s in legacy_statuses if s == FindingStatus.FAIL.value),
            FindingStatus.UNKNOWN.value: sum(1 for s in legacy_statuses if s == FindingStatus.UNKNOWN.value),
        }

        has_unreadable = summary_counts[FindingStatus.UNKNOWN.value] > 0
        has_fatal = any(
            f.severity == Severity.FATAL and f.legacy_status_snapshot == FindingStatus.FAIL.value
            for f in findings
        )
        has_fail = summary_counts[FindingStatus.FAIL.value] > 0
        has_review = summary_counts[FindingStatus.REVIEW.value] > 0

        if has_unreadable:
            overall_status = "UNREADABLE_PACKET"
        elif has_fatal:
            overall_status = "REJECT_PRECHECK"
        elif has_fail:
            overall_status = "ACTION_REQUIRED"
        elif has_review:
            overall_status = "REVIEW_RECOMMENDED"
        else:
            overall_status = "READY_TO_SUBMIT"

        audit_ts = timestamp or f"{effective_as_of.isoformat()}T00:00:00"
        return AuditResult(
            packet_id=packet_id,
            scheme_name=self.pack.pack_id,
            readiness_score=score,
            overall_status=overall_status,
            findings=findings,
            summary_counts=summary_counts,
            execution_time_ms=0.0,
            timestamp=audit_ts,
            as_of=effective_as_of.isoformat(),
            legacy_readiness_score_snapshot=score,
        )
