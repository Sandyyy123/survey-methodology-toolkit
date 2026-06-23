"""
Rule-based survey-question bias auditor.

Screens each question against common bias types and returns concrete findings.
This is a transparent, explainable first pass (not a black box) that a
methodologist then reviews -- it catches the mechanical issues so human time
goes to judgment calls.

Bias types covered: leading/loaded wording, double-barreled, absolute terms,
unbalanced/agree-only scales, assumptive framing, jargon, and missing
non-substantive option (Don't know / N/A).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

LEADING_WORDS = [
    "easy", "easy-to-use", "amazing", "excellent", "great", "wonderful",
    "best", "love", "enjoy", "favorite", "convenient", "delicious",
    "high-quality", "superior", "fantastic",
]
LOADED_PHRASES = [
    "don't you agree", "wouldn't you say", "isn't it true",
    "as you know", "obviously", "everyone knows",
]
ABSOLUTE_TERMS = ["always", "never", "all", "none", "every", "everyone", "nobody"]
DOUBLE_BARRELED = re.compile(r"\b(\w+)\s+and\s+(\w+)\b", re.IGNORECASE)
ASSUMPTIVE = ["how often do you", "how much do you", "when did you stop"]
JARGON = ["synergy", "leverage", "omnichannel", "paradigm", "utilize", "ideate"]


@dataclass
class Finding:
    bias_type: str
    severity: str  # high | medium | low
    detail: str
    suggestion: str


@dataclass
class QuestionAudit:
    question: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not self.findings

    def report(self) -> str:
        if self.is_clean:
            return f"[CLEAN] {self.question}"
        lines = [f"[{len(self.findings)} ISSUE(S)] {self.question}"]
        for f in self.findings:
            lines.append(f"   - ({f.severity}) {f.bias_type}: {f.detail}")
            lines.append(f"     -> {f.suggestion}")
        return "\n".join(lines)


def audit_question(question: str, scale_options: list[str] | None = None) -> QuestionAudit:
    q = question.lower()
    audit = QuestionAudit(question=question)

    for w in LEADING_WORDS:
        if re.search(rf"\b{re.escape(w)}\b", q):
            audit.findings.append(Finding(
                "leading/loaded", "high",
                f"positive descriptor '{w}' steers the respondent",
                "remove the descriptor; use a neutral, balanced phrasing"))
            break
    for phrase in LOADED_PHRASES:
        if phrase in q:
            audit.findings.append(Finding(
                "loaded framing", "high", f"'{phrase}' pressures agreement",
                "delete the framing; ask the question plainly"))
    if DOUBLE_BARRELED.search(q) and any(
            t in q for t in ["service", "fast", "friendly", "quality", "price"]):
        audit.findings.append(Finding(
            "double-barreled", "high", "asks about two attributes at once",
            "split into two separate questions"))
    for t in ABSOLUTE_TERMS:
        if re.search(rf"\b{t}\b", q):
            audit.findings.append(Finding(
                "absolute term", "medium", f"'{t}' forces an extreme answer",
                "soften to a frequency scale (e.g. Never..Always)"))
            break
    for phrase in ASSUMPTIVE:
        if phrase in q:
            audit.findings.append(Finding(
                "assumptive framing", "medium",
                f"'{phrase}' presumes the behavior occurs",
                "add a filter question to establish the behavior first"))
            break
    for j in JARGON:
        if j in q:
            audit.findings.append(Finding(
                "jargon", "low", f"'{j}' may not be understood by all",
                "replace with plain language"))

    if scale_options:
        opts = [o.lower() for o in scale_options]
        if all("agree" in o or "disagree" in o for o in opts):
            pos = sum("agree" in o and "disagree" not in o for o in opts)
            neg = sum("disagree" in o for o in opts)
            if pos != neg:
                audit.findings.append(Finding(
                    "unbalanced scale", "high",
                    f"{pos} positive vs {neg} negative points",
                    "balance the scale symmetrically around a neutral midpoint"))
        if not any(o in ("don't know", "not applicable", "n/a", "prefer not to say")
                   for o in opts):
            audit.findings.append(Finding(
                "missing non-substantive option", "low",
                "no 'Don't know / N/A' offered",
                "add a non-substantive option to avoid forced false answers"))
    return audit


def audit_survey(questions: list[dict]) -> list[QuestionAudit]:
    return [audit_question(q["text"], q.get("scale")) for q in questions]


if __name__ == "__main__":
    survey = [
        {"text": "How much did you enjoy our easy-to-use product?"},
        {"text": "Was the service fast and friendly?"},
        {"text": "How would you rate your overall experience?",
         "scale": ["Strongly agree", "Agree", "Somewhat agree", "Disagree"]},
        {"text": "How often do you skip breakfast?"},
        {"text": "How would you rate the speed of service?",
         "scale": ["Very poor", "Poor", "Neutral", "Good", "Very good", "N/A"]},
    ]
    results = audit_survey(survey)
    clean = sum(r.is_clean for r in results)
    print(f"Audited {len(results)} questions -- {clean} clean, "
          f"{len(results) - clean} flagged\n")
    for r in results:
        print(r.report(), "\n")
