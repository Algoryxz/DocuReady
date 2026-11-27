"""Scheme Pack Execution Engine (ARCHITECTURE_V2 §7).

Executes declarative scheme packs using the 9 closed primitives in pure Python
without dynamic evaluation (zero eval/exec).
"""

from __future__ import annotations

import re
from enum import Enum
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

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
from docuready.rules.lint import lint_pack
from docuready.rules.loader import PackLoadError, load_pack
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
    PackStatus,
    ParameterDeclaration,
    RuleDefinition,
    SourceDefinition,
    SourceManifest,
    SourceStatus,
)
from docuready.rules.slot_validator import validate_packet_slots


class ExemptionVerdict(str, Enum):
    """Tri-state result for category-based rule exemption."""

    EXEMPT = "EXEMPT"
    NOT_EXEMPT = "NOT_EXEMPT"
    UNCERTAIN = "UNCERTAIN"


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


def match_category_tokens(text: str, target_tokens: Set[str]) -> bool:
    """Token-aware category matching using regex word boundaries to avoid substring false positives."""
    expanded_targets = set(target_tokens)
    if "SC" in target_tokens:
        expanded_targets.add("SCHEDULED CASTE")
    if "ST" in target_tokens:
        expanded_targets.add("SCHEDULED TRIBE")

    norm_text = text.upper()
    for target in expanded_targets:
        pattern = r"\b" + re.escape(target) + r"\b"
        if re.search(pattern, norm_text):
            return True

    return False


class PackExecutionEngine:
    """Deterministic, explainable execution engine for scheme packs."""

    def __init__(
        self,
        pack: Union[PackManifest, Path, str],
        sources: Optional[Union[SourceManifest, Path, str]] = None,
        allow_draft: bool = False,
    ):
        if isinstance(pack, (Path, str)):
            pack_dir = Path(pack).resolve()
            if not pack_dir.exists() or not pack_dir.is_dir():
                raise PackLoadError(f"Pack directory does not exist or is not a directory: {pack_dir}")

            # Safe linting before execution to enforce lifecycle and contracts
            lint_result = lint_pack(pack_dir, allow_draft=allow_draft)
            if not lint_result.is_valid:
                raise PackLoadError(
                    f"Pack lint failed with {len(lint_result.errors)} errors: "
                    + "; ".join(str(e) for e in lint_result.errors)
                )

            loaded_pack, loaded_sources = load_pack(pack_dir)
            self.pack = loaded_pack
            self.sources = loaded_sources
            self.pack_dir: Optional[Path] = pack_dir
        else:
            self.pack = pack
            self.sources = sources if isinstance(sources, SourceManifest) else None
            self.pack_dir = None

        # Lifecycle contract enforcement
        if self.pack.status == PackStatus.DRAFT and not allow_draft:
            raise ValueError(
                f"Pack '{self.pack.pack_id}' is in 'draft' status and allow_draft is False. "
                "The engine refuses draft packs unless explicitly permitted with allow_draft=True."
            )

        if self.pack.status not in (
            PackStatus.DRAFT,
            PackStatus.DEMO_SNAPSHOT,
            PackStatus.VERIFIED,
        ):
            raise ValueError(
                f"Pack '{self.pack.pack_id}' has unrecognized or invalid lifecycle status '{self.pack.status}'"
            )

        self._source_map: Dict[str, SourceDefinition] = {}
        if self.sources and hasattr(self.sources, "sources"):
            for s in self.sources.sources:
                self._source_map[s.id] = s

    def _format_statutory_reference(self, rule: RuleDefinition) -> str:
        """Format citation reference into statutory reference string preserving unverified state."""
        src_id = rule.citation.source
        src_def = self._source_map.get(src_id)
        clause = rule.citation.clause or (src_def.clause if src_def else "")

        is_unverified = False
        if src_def:
            title = src_def.title
            if src_def.status != SourceStatus.VERIFIED or not getattr(src_def, "supports_rule", True):
                is_unverified = True
        else:
            title = f"Citation {src_id}"
            is_unverified = True

        ref_str = f"{title}, {clause}" if clause else title
        if is_unverified:
            ref_str = f"{ref_str} [source pending verification]"
        return ref_str

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
        mismatched_slots: Set[DocumentType],
    ) -> ExemptionVerdict:
        """Evaluate exempt_when clause against applicant evidence using tri-state verdict.

        Returns ExemptionVerdict.EXEMPT, NOT_EXEMPT, or UNCERTAIN.
        """
        fact = exempt_when.get("fact", "")
        in_values = exempt_when.get("in", [])
        if isinstance(in_values, (str, int, float)):
            in_values = [str(in_values)]
        allowed_set = {str(v).strip().upper() for v in in_values}

        doc_name, f_name = parse_field_spec(fact, ["APPLICATION_FORM", "CASTE_CERT"])
        candidate_docs = [doc_name] if doc_name else ["APPLICATION_FORM", "CASTE_CERT"]

        found_field: Optional[ExtractedField] = None
        has_doc = False

        for d_name in candidate_docs:
            doc = get_document(documents, d_name, mismatched_slots)
            if doc is None or doc.status == "MISSING":
                continue
            has_doc = True
            if doc.status in ("UNREADABLE", "CORRUPTED"):
                return ExemptionVerdict.UNCERTAIN

            f = get_field_from_doc(doc, f_name)
            if f and f.raw_value and f.raw_value.strip():
                found_field = f
                break

        if not has_doc or found_field is None:
            # Missing document or missing field -> evidence is unavailable
            return ExemptionVerdict.UNCERTAIN

        if found_field.is_uncertain or found_field.evidence_state is EvidenceState.UNCERTAIN:
            return ExemptionVerdict.UNCERTAIN

        # Token-aware category matching
        is_match = match_category_tokens(found_field.raw_value, allowed_set)
        if is_match:
            return ExemptionVerdict.EXEMPT

        return ExemptionVerdict.NOT_EXEMPT

    def validate_packet(
        self,
        packet_id: str,
        documents: Dict[Any, ExtractedDocument],
        as_of: Optional[date] = None,
        audit_date: Optional[date] = None,
        timestamp: Optional[str] = None,
    ) -> AuditResult:
        """Execute the pack's declarative rules against an applicant document packet."""
        if as_of is not None and audit_date is not None and as_of != audit_date:
            raise ValueError(
                f"Conflicting as_of ({as_of}) and audit_date ({audit_date}) provided"
            )

        effective_as_of = as_of or audit_date or date(2026, 11, 13)
        findings: List[Finding] = []

        # 1. Structural Slot Evaluation: Required vs Optional Slots
        req_doc_types: List[DocumentType] = []
        if self.pack.doc_slots:
            for s_name, s_def in self.pack.doc_slots.items():
                dt = resolve_doc_type(s_name)
                if dt:
                    if s_def.required:
                        req_doc_types.append(dt)

        # Check for missing and unreadable required documents
        for dt in req_doc_types:
            doc = documents.get(dt)
            if doc is None or doc.status == "MISSING":
                findings.append(
                    Finding(
                        rule_id="RULE-DOC-01",
                        rule_name="Mandatory Document Completeness",
                        status=FindingStatus.FAIL,
                        severity=Severity.FATAL,
                        penalty=35,
                        field="MANDATORY_DOCUMENT",
                        documents_involved=[dt.value],
                        message=f"Mandatory document '{dt.value}' is missing from the application packet.",
                        evidence=[],
                        remediation=f"Obtain and upload a valid {dt.value} before portal submission.",
                        statutory_reference="OSSP Guidelines 2024-25, Section 3.1 & NSP Common Framework",
                    )
                )
                findings[-1].set_resolution(
                    raw=Raw.DOC_ABSENT,
                    status=Status.MISSING,
                    reason_code=ReasonCode.DOC_ABSENT.value,
                )
            elif doc.status in ("UNREADABLE", "CORRUPTED"):
                findings.append(
                    Finding(
                        rule_id="RULE-DOC-02",
                        rule_name="Document Legibility & Evidence Integrity",
                        status=FindingStatus.UNKNOWN,
                        severity=Severity.CRITICAL,
                        penalty=25,
                        field="SCAN_QUALITY",
                        documents_involved=[dt.value],
                        message=f"Document '{dt.value}' is unreadable or corrupted. Clear evidence cannot be extracted.",
                        evidence=[
                            EvidenceProvenance(
                                document_type=dt.value,
                                file_name=doc.file_path,
                                raw_snippet=f"[{doc.status} SCAN / INSUFFICIENT EVIDENCE]",
                            )
                        ],
                        remediation="Re-scan the document with at least 300 DPI flatbed scanner and ensure good lighting.",
                        statutory_reference="NSP Upload Guidelines & IT Act 2000 Section 6A [source pending verification]",
                    )
                )
                findings[-1].set_resolution(
                    raw=Raw.INDETERMINATE,
                    status=Status.REVIEW,
                    reason_code=ReasonCode.INSUFFICIENT_DATA.value,
                )

        # 2. Document Slot Mismatch Detection
        slot_findings, mismatched_slots = validate_packet_slots(
            documents, req_doc_types, emit_for_unreadable=False
        )
        for sf in slot_findings:
            if getattr(sf, "_is_wrong_type", False):
                sf.set_resolution(
                    raw=Raw.VIOLATED,
                    status=Status.REVIEW,
                    reason_code=ReasonCode.WRONG_DOCUMENT_TYPE.value,
                )
            else:
                sf.set_resolution(
                    raw=Raw.INDETERMINATE,
                    status=Status.REVIEW,
                    reason_code=ReasonCode.EVIDENCE_UNCERTAIN.value,
                )
            findings.append(sf)

        context = ExecutionContext(
            as_of=effective_as_of,
            scheme_name=self.pack.pack_id,
            mismatched_slots=mismatched_slots,
        )

        # 3. Declarative Rule Execution
        parameters = self.pack.parameters or {}

        for rule in self.pack.rules:
            if rule.primitive not in PRIMITIVE_REGISTRY:
                raise ValueError(
                    f"Unknown or unregistered primitive '{rule.primitive}' in rule '{rule.id}'"
                )

            # Skip duplicate document completeness checks already evaluated structurally
            if rule.primitive == "require_document" and any(
                f.rule_id == "RULE-DOC-01" for f in findings
            ):
                continue
            if rule.primitive == "legible" and any(
                f.rule_id == "RULE-DOC-02" for f in findings
            ):
                continue

            # Resolve parameters
            resolved_inputs = _resolve_param_val(rule.inputs, parameters)
            resolved_params = _resolve_param_val(rule.params, parameters)

            # Check exemption via tri-state evaluation
            exemption_verdict = ExemptionVerdict.NOT_EXEMPT
            if rule.exempt_when:
                exemption_verdict = self._evaluate_exempt_when(
                    rule.exempt_when, documents, mismatched_slots
                )

            if exemption_verdict == ExemptionVerdict.EXEMPT:
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
            elif exemption_verdict == ExemptionVerdict.UNCERTAIN:
                # Category evidence is missing or uncertain -> abstain to REVIEW, never false FAIL
                raw_result = Raw.INDETERMINATE
                match_grade = MatchGrade.AMBIGUOUS
                weakest = EvidenceState.UNCERTAIN
                finding_msg = (
                    f"Potential category exemption under {rule.id}, but category evidence is uncertain or unavailable. Verification required."
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

            # Resolve outcome using canonical V2 truth table
            resolved = resolve_outcome(
                raw=raw_result,
                weakest_evidence=weakest,
                max_severity=rule.max_severity,
                match_grade=match_grade,
                exemption_reason="CATEGORY_EXEMPTION",
            )

            # Map to legacy severity / penalty snapshots
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

        # 4. Overall Readiness and Score
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
            pack_status=self.pack.status.value,
            legacy_readiness_score_snapshot=score,
        )
