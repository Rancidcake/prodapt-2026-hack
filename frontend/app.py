import streamlit as st

from api_client import generate_lesson_plan, generate_quiz

st.set_page_config(page_title="MyLesson.ai", page_icon="📘")
st.title("MyLesson.ai")
st.caption("An AI teaching assistant — draft, review, approve.")

if "lesson_plan" not in st.session_state:
    st.session_state.lesson_plan = None
if "quiz" not in st.session_state:
    st.session_state.quiz = None

with st.form("teaching_context_form"):
    st.subheader("Teaching context")
    col1, col2 = st.columns(2)
    with col1:
        grade = st.text_input("Grade/level", placeholder="e.g. Class 9")
        subject = st.text_input("Subject", placeholder="e.g. Physics")
    with col2:
        board = st.text_input("Board/curriculum (optional)", placeholder="e.g. CBSE")
        language = st.text_input("Language", value="English")

    st.subheader("Lesson request")
    topic = st.text_input("Topic", placeholder="e.g. Newton's Laws of Motion")
    duration_minutes = st.slider("Class duration (minutes)", 20, 90, 40)

    submitted = st.form_submit_button("Generate lesson plan")

if submitted:
    if not grade or not subject or not topic:
        st.error("Grade, subject, and topic are required.")
    else:
        with st.spinner("Generating lesson plan…"):
            try:
                st.session_state.lesson_plan = generate_lesson_plan(
                    teaching_context={
                        "grade": grade,
                        "subject": subject,
                        "board": board or None,
                        "language": language or None,
                    },
                    topic=topic,
                    duration_minutes=duration_minutes,
                )
                st.session_state.quiz = None
            except Exception as exc:  # noqa: BLE001 — surface any backend error to the teacher
                st.error(f"Generation failed: {exc}")

plan = st.session_state.lesson_plan
if plan:
    st.divider()
    st.header(plan["topic"])
    st.caption(f"{plan['duration_minutes']} minutes")

    st.subheader("Learning objectives")
    objectives = plan["objectives"]
    for obj in objectives:
        st.markdown(f"- **{obj['id']}** — {obj['text']}")

    st.subheader("Sections")
    for section in plan["sections"]:
        badge = "✅ grounded" if section["is_grounded"] else "⚠️ ungrounded — verify before use"
        with st.expander(f"{section['title']} ({section['timing_minutes']} min) — {badge}"):
            st.write(section["content"])
            st.markdown(f"**Checks for understanding:** {section['checks_for_understanding']}")
            st.caption(f"Objectives covered: {', '.join(section['objective_ids'])}")

    st.subheader("Differentiation notes")
    st.write(plan["differentiation_notes"])

    st.divider()
    st.subheader("Generate a quiz from these objectives")
    qcol1, qcol2 = st.columns(2)
    with qcol1:
        mcq_count = st.number_input("MCQ count", min_value=0, max_value=20, value=5)
    with qcol2:
        difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)

    if st.button("Generate quiz"):
        with st.spinner("Generating quiz…"):
            try:
                st.session_state.quiz = generate_quiz(
                    teaching_context={
                        "grade": grade,
                        "subject": subject,
                        "board": board or None,
                        "language": language or None,
                    },
                    objectives=objectives,
                    item_counts={"mcq": mcq_count},
                    difficulty=difficulty,
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Quiz generation failed: {exc}")

quiz = st.session_state.quiz
if quiz:
    st.divider()
    st.header("Quiz")
    if quiz["uncovered_objective_ids"]:
        st.warning(f"Objectives with no question: {', '.join(quiz['uncovered_objective_ids'])}")
    else:
        st.success("Every objective is covered by at least one question.")

    for i, q in enumerate(quiz["questions"], start=1):
        badge = "✅ grounded" if q["is_grounded"] else "⚠️ ungrounded"
        with st.expander(f"Q{i}. {q['stem'][:60]}… — {badge}"):
            st.write(q["stem"])
            for opt in q["options"]:
                st.write(f"- {opt}")
            st.markdown(f"**Correct answer:** {q['correct_answer']}")
            st.caption(f"Objective: {q['objective_id']} · Difficulty: {q['difficulty']}")
