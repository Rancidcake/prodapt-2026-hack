import requests
import streamlit as st

import theme
from api_client import (
    generate_activity,
    generate_explanation,
    generate_lesson_plan,
    generate_quiz,
    generate_resources,
    list_documents,
    list_providers,
    register,
    upload_document,
    whoami,
)
from pdf_export import build_quiz_pdf

st.set_page_config(page_title="MyLesson.ai", page_icon="📘", layout="wide")

if "auth" not in st.session_state:
    st.session_state.auth = None

for key, default in [
    ("large_text", False),
    ("high_contrast", False),
    ("reduce_motion", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

theme.inject(
    large_text=st.session_state.large_text,
    high_contrast=st.session_state.high_contrast,
    reduce_motion=st.session_state.reduce_motion,
)

# --- Login / register gate ---

if st.session_state.auth is None:
    st.title("MyLesson.ai")
    theme.step_label("SIGN IN // TEACHER ACCESS")
    st.caption("Sign in to keep your uploaded material and generations private to you.")

    login_tab, register_tab = st.tabs(["Log in", "Create account"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log in"):
                try:
                    whoami((username, password))
                    st.session_state.auth = (username, password)
                    st.rerun()
                except requests.HTTPError:
                    st.error("Invalid username or password.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not reach the backend: {exc}")

    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password (min 8 characters)", type="password")
            if st.form_submit_button("Create account"):
                try:
                    register(new_username, new_password)
                    st.session_state.auth = (new_username, new_password)
                    st.rerun()
                except requests.HTTPError as exc:
                    detail = exc.response.json().get("detail", str(exc)) if exc.response is not None else str(exc)
                    st.error(f"Could not create account: {detail}")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not reach the backend: {exc}")

    st.stop()

auth = st.session_state.auth

# --- Session state ---

for key, default in [
    ("lesson_plan", None),
    ("quiz", None),
    ("resources", None),
    ("explanation", None),
    ("activity", None),
    ("documents", None),
    ("providers_info", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.documents is None:
    try:
        st.session_state.documents = list_documents(auth)
    except Exception:  # noqa: BLE001 — backend may not be up yet on first paint
        st.session_state.documents = []

if st.session_state.providers_info is None:
    try:
        st.session_state.providers_info = list_providers()
    except Exception:  # noqa: BLE001
        st.session_state.providers_info = {"default_provider": "anthropic", "models": {"anthropic": []}}

providers_info = st.session_state.providers_info

# --- Sidebar: identity, accessibility, teaching context, model, source documents ---

with st.sidebar:
    st.markdown(f"**Signed in as** `{auth[0]}`")
    if st.button("Log out"):
        st.session_state.auth = None
        st.session_state.documents = None
        st.session_state.lesson_plan = None
        st.session_state.quiz = None
        st.session_state.resources = None
        st.session_state.explanation = None
        st.session_state.activity = None
        st.rerun()

    st.divider()
    theme.step_label("ACCESSIBILITY")
    st.session_state.large_text = st.toggle("Large text", value=st.session_state.large_text)
    st.session_state.high_contrast = st.toggle("High contrast", value=st.session_state.high_contrast)
    st.session_state.reduce_motion = st.toggle("Reduce motion", value=st.session_state.reduce_motion)

    st.divider()
    theme.step_label("TEACHING CONTEXT")
    grade = st.text_input("Grade/level", placeholder="e.g. Class 9")
    subject = st.text_input("Subject", placeholder="e.g. Physics")
    board = st.text_input("Board/curriculum (optional)", placeholder="e.g. CBSE")
    language = st.text_input("Language", value="English")
    topic = st.text_input("Topic", placeholder="e.g. Newton's Laws of Motion")

    teaching_context = {
        "grade": grade,
        "subject": subject,
        "board": board or None,
        "language": language or None,
    }

    st.divider()
    theme.step_label("MODEL")
    provider_options = list(providers_info["models"].keys())
    default_provider_index = (
        provider_options.index(providers_info["default_provider"])
        if providers_info["default_provider"] in provider_options
        else 0
    )
    selected_provider = st.selectbox("Provider", provider_options, index=default_provider_index)
    model_options = providers_info["models"].get(selected_provider, [])
    selected_model = st.selectbox("Model", model_options) if model_options else None

    st.divider()
    theme.step_label("SOURCE DOCUMENTS")
    st.caption("Upload the teacher's own material to ground generation in it, with citations.")

    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded_file is not None and st.button("Ingest document"):
        with st.spinner("Parsing, chunking, and embedding…"):
            try:
                upload_document(auth, uploaded_file.name, uploaded_file.getvalue())
                st.session_state.documents = list_documents(auth)
                st.success(f"Ingested {uploaded_file.name}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Upload failed: {exc}")

    selected_document_ids: list[int] = []
    if st.session_state.documents:
        options = {f"{d['title']} ({d['chunk_count']} chunks)": d["id"] for d in st.session_state.documents}
        selected_labels = st.multiselect("Ground generation in", options=list(options.keys()))
        selected_document_ids = [options[label] for label in selected_labels]
    else:
        st.caption("No documents uploaded yet — generation will run ungrounded.")

# --- Main area ---

st.title("MyLesson.ai")
theme.ticker(
    f"TEACHER: {auth[0].upper()}",
    f"PROVIDER: {selected_provider.upper()}",
    f"MODEL: {(selected_model or 'DEFAULT').upper()}",
    f"SOURCES: {len(selected_document_ids)} SELECTED",
)

if not grade or not subject or not topic:
    st.info("Fill in Grade/level, Subject, and Topic in the sidebar to get started.")

tab_lesson, tab_quiz, tab_explain, tab_activity, tab_resources = st.tabs(
    ["📘 Lesson Plan", "📝 Quiz", "💬 Explain a Concept", "🎯 Activity Ideas", "🔗 Resources"]
)

# --- Lesson Plan tab ---

with tab_lesson:
    duration_minutes = st.slider("Class duration (minutes)", 20, 90, 40)

    if st.button("Generate lesson plan", key="btn_lesson_plan"):
        if not grade or not subject or not topic:
            st.error("Grade, subject, and topic are required (sidebar).")
        else:
            with st.spinner("Generating lesson plan…"):
                try:
                    st.session_state.lesson_plan = generate_lesson_plan(
                        auth,
                        teaching_context=teaching_context,
                        topic=topic,
                        duration_minutes=duration_minutes,
                        document_ids=selected_document_ids,
                        provider=selected_provider,
                        model=selected_model,
                    )
                    st.session_state.quiz = None
                except Exception as exc:  # noqa: BLE001
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
            badge = (
                theme.chip("GROUNDED", "accent")
                if section["is_grounded"]
                else theme.chip("UNGROUNDED — VERIFY", "ink")
            )
            with st.expander(f"{section['title']} ({section['timing_minutes']} min)"):
                theme.chips(badge)
                st.write(section["content"])
                st.markdown(f"**Checks for understanding:** {section['checks_for_understanding']}")
                st.caption(f"Objectives covered: {', '.join(section['objective_ids'])}")
                if section["citations"]:
                    st.caption(f"Citations: chunk {', '.join(section['citations'])}")

        st.subheader("Differentiation notes")
        st.write(plan["differentiation_notes"])
    else:
        objectives = None

# --- Quiz tab ---

with tab_quiz:
    plan = st.session_state.lesson_plan

    if not plan:
        st.info("Generate a lesson plan first — quiz questions are tagged to its learning objectives.")
    else:
        qcol1, qcol2 = st.columns(2)
        with qcol1:
            mcq_count = st.number_input("MCQ count", min_value=0, max_value=20, value=5)
        with qcol2:
            difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)

        if st.button("Generate quiz", key="btn_quiz"):
            with st.spinner("Generating quiz…"):
                try:
                    st.session_state.quiz = generate_quiz(
                        auth,
                        teaching_context=teaching_context,
                        objectives=plan["objectives"],
                        item_counts={"mcq": mcq_count},
                        difficulty=difficulty,
                        document_ids=selected_document_ids,
                        provider=selected_provider,
                        model=selected_model,
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Quiz generation failed: {exc}")

        quiz = st.session_state.quiz
        if quiz:
            st.divider()
            if quiz["uncovered_objective_ids"]:
                st.warning(f"Objectives with no question: {', '.join(quiz['uncovered_objective_ids'])}")
            else:
                st.success("Every objective is covered by at least one question.")

            try:
                pdf_bytes = build_quiz_pdf(
                    quiz=quiz,
                    teaching_context={"grade": grade, "subject": subject, "board": board},
                    topic=plan["topic"],
                )
                st.download_button(
                    "Download quiz (PDF)",
                    data=pdf_bytes,
                    file_name="quiz.pdf",
                    mime="application/pdf",
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not build PDF: {exc}")

            for i, q in enumerate(quiz["questions"], start=1):
                badge = theme.chip("GROUNDED", "accent") if q["is_grounded"] else theme.chip("UNGROUNDED", "ink")
                with st.expander(f"Q{i}. {q['stem'][:60]}…"):
                    theme.chips(badge)
                    st.write(q["stem"])
                    for opt in q["options"]:
                        st.write(f"- {opt}")
                    st.markdown(f"**Correct answer:** {q['correct_answer']}")
                    st.caption(f"Objective: {q['objective_id']} · Difficulty: {q['difficulty']}")
                    if q["citations"]:
                        st.caption(f"Citations: chunk {', '.join(q['citations'])}")

# --- Explain a Concept tab ---

with tab_explain:
    extra_support = st.toggle(
        "Extra support mode",
        help="For students who need additional support — dyslexia, ADHD, an intellectual "
        "disability, or English-language learners. Shorter sentences, one idea at a time, "
        "concrete examples before abstract ones, no idioms.",
    )

    if st.button("Explain", key="btn_explain"):
        if not grade or not subject or not topic:
            st.error("Grade, subject, and topic are required (sidebar).")
        else:
            with st.spinner("Explaining…"):
                try:
                    st.session_state.explanation = generate_explanation(
                        auth,
                        teaching_context=teaching_context,
                        topic=topic,
                        document_ids=selected_document_ids,
                        extra_support=extra_support,
                        provider=selected_provider,
                        model=selected_model,
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not generate explanation: {exc}")

    explanation = st.session_state.explanation
    if explanation:
        st.divider()
        badge = theme.chip("GROUNDED", "accent") if explanation["is_grounded"] else theme.chip("UNGROUNDED — VERIFY", "ink")
        theme.chips(badge)
        st.write(explanation["explanation"])

        st.subheader("Analogies")
        for a in explanation["analogies"]:
            st.markdown(f"- {a}")

        st.subheader("Common misconceptions")
        for m in explanation["common_misconceptions"]:
            st.markdown(f"- {m}")

        if explanation["citations"]:
            st.caption(f"Citations: chunk {', '.join(explanation['citations'])}")

# --- Activity Ideas tab ---

with tab_activity:
    acol1, acol2 = st.columns(2)
    with acol1:
        class_size = st.number_input("Class size", min_value=1, max_value=200, value=30)
    with acol2:
        resources_text = st.text_input("Available resources (comma-separated)", placeholder="e.g. whiteboard, chart paper")
    available_resources = [r.strip() for r in resources_text.split(",") if r.strip()] if resources_text else []

    if st.button("Generate activity", key="btn_activity"):
        if not grade or not subject or not topic:
            st.error("Grade, subject, and topic are required (sidebar).")
        else:
            with st.spinner("Designing activity…"):
                try:
                    st.session_state.activity = generate_activity(
                        auth,
                        teaching_context=teaching_context,
                        topic=topic,
                        class_size=class_size,
                        available_resources=available_resources,
                        provider=selected_provider,
                        model=selected_model,
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not generate activity: {exc}")

    activity = st.session_state.activity
    if activity:
        st.divider()
        theme.chips(theme.chip(activity["activity_type"].replace("_", " ").upper(), "outline"))
        st.header(activity["title"])
        st.caption(f"{activity['duration_minutes']} minutes")

        st.subheader("Materials")
        for m in activity["materials"]:
            st.markdown(f"- {m}")

        st.subheader("Steps")
        for i, step in enumerate(activity["steps"], start=1):
            st.markdown(f"{i}. {step}")

# --- Resources tab ---

with tab_resources:
    st.caption(
        "AI-suggested — no live web search happens here, so links are only marked GOOD LINK when "
        "the model is confident it's a real, well-known page. Anything else is a search suggestion, "
        "not a URL."
    )

    if st.button("Find learning resources", key="btn_resources"):
        if not grade or not subject or not topic:
            st.error("Grade, subject, and topic are required (sidebar).")
        else:
            with st.spinner("Finding resources…"):
                try:
                    st.session_state.resources = generate_resources(
                        auth,
                        teaching_context=teaching_context,
                        topic=topic,
                        document_ids=selected_document_ids,
                        provider=selected_provider,
                        model=selected_model,
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not find resources: {exc}")

    resources = st.session_state.resources
    if resources:
        st.divider()
        for r in resources["resources"]:
            badge = (
                theme.chip("GOOD LINK", "accent")
                if r["confidence"] == "high"
                else theme.chip("VERIFY BEFORE SHARING", "ink")
            )
            type_badge = theme.chip(r["type"].upper(), "outline")
            with st.container(border=True):
                theme.chips(badge, type_badge)
                if r["confidence"] == "high" and r["url"]:
                    st.markdown(f"**[{r['title']}]({r['url']})**")
                else:
                    st.markdown(f"**{r['title']}** _(search for this)_")
                st.caption(r["description"])
