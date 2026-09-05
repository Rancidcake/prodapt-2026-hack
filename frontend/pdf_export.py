"""Renders a generated quiz into a downloadable PDF — questions first, then a
separated answer key (the standard teacher-handout format, so the questions
section alone can be handed to students)."""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

_STYLES = getSampleStyleSheet()

_TITLE = ParagraphStyle("QuizTitle", parent=_STYLES["Title"], fontSize=20, spaceAfter=4)
_META = ParagraphStyle(
    "QuizMeta", parent=_STYLES["Normal"], fontSize=10, textColor=colors.HexColor("#555555"), spaceAfter=16
)
_QUESTION = ParagraphStyle(
    "Question", parent=_STYLES["Normal"], fontSize=11, spaceBefore=12, spaceAfter=4, fontName="Helvetica-Bold"
)
_OPTION = ParagraphStyle("Option", parent=_STYLES["Normal"], fontSize=10, leftIndent=16, spaceAfter=2)
_TAG = ParagraphStyle("Tag", parent=_STYLES["Normal"], fontSize=8, textColor=colors.HexColor("#888888"), spaceAfter=4)
_SECTION = ParagraphStyle("Section", parent=_STYLES["Heading2"], fontSize=14, spaceBefore=8, spaceAfter=8)
_ANSWER = ParagraphStyle(
    "Answer", parent=_STYLES["Normal"], fontSize=10, leftIndent=16, textColor=colors.HexColor("#1a5d1a")
)

_LETTERS = "ABCDEFGHIJ"


def build_quiz_pdf(*, quiz: dict, teaching_context: dict, topic: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm
    )

    meta_bits = [teaching_context.get("subject", ""), teaching_context.get("grade", "")]
    if teaching_context.get("board"):
        meta_bits.append(teaching_context["board"])

    story = [
        Paragraph(f"Quiz — {topic}", _TITLE),
        Paragraph(" · ".join(b for b in meta_bits if b), _META),
    ]

    for i, q in enumerate(quiz["questions"], start=1):
        story.append(Paragraph(f"{i}. {q['stem']}", _QUESTION))
        for j, option in enumerate(q.get("options") or []):
            story.append(Paragraph(f"{_LETTERS[j]}. {option}", _OPTION))
        tag_bits = [f"Objective: {q['objective_id']}", f"Difficulty: {q['difficulty']}"]
        if not q.get("is_grounded", True):
            tag_bits.append("UNGROUNDED — verify before use")
        story.append(Paragraph(" &middot; ".join(tag_bits), _TAG))

    story.append(PageBreak())
    story.append(Paragraph("Answer Key", _SECTION))
    for i, q in enumerate(quiz["questions"], start=1):
        story.append(Paragraph(f"{i}. {q['correct_answer']}", _ANSWER))

    if quiz.get("uncovered_objective_ids"):
        story.append(Spacer(1, 16))
        story.append(
            Paragraph(
                "Objectives with no question: " + ", ".join(quiz["uncovered_objective_ids"]),
                _META,
            )
        )

    doc.build(story)
    return buffer.getvalue()
