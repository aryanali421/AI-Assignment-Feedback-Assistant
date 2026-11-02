
import os
import io
import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Markwise | Assignment Feedback",
    page_icon="✳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# DESIGN SYSTEM
# --------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #0A0D12;
    --panel: #121720;
    --panel2: #171F2B;
    --border: #263140;
    --text: #E7EBF2;
    --muted: #8995A6;
    --gold: #FFC233;
    --green: #86D6B0;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: var(--panel);
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

#MainMenu, footer {
    visibility: hidden;
}

.brand {
    font-family: 'DM Mono', monospace;
    font-size: 14px;
    letter-spacing: 2px;
    color: var(--gold);
    font-weight: 500;
}

.hero-title {
    font-size: clamp(34px, 5vw, 54px);
    font-weight: 800;
    letter-spacing: -2px;
    line-height: 1.1;
    margin-top: 24px;
    margin-bottom: 12px;
}

.hero-sub {
    color: var(--muted);
    font-size: 15px;
    line-height: 1.7;
    max-width: 620px;
}

.section-heading {
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 5px;
}

.section-caption {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 18px;
}

.panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 18px;
}

.step-label {
    color: var(--gold);
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
}

div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    background: #0D131C !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 9px !important;
    font-family: 'DM Sans', sans-serif !important;
}

div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextInput"] input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 1px var(--gold) !important;
}

div[data-testid="stSelectbox"] > div > div {
    background: #0D131C;
    border-color: var(--border);
    color: var(--text);
    border-radius: 9px;
}

.stButton > button {
    background: var(--gold) !important;
    color: #151515 !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 800 !important;
    padding: 12px 22px !important;
    transition: all .2s ease;
}

.stButton > button:hover {
    background: #FFD36A !important;
    transform: translateY(-2px);
}

.stDownloadButton > button {
    background: var(--panel2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 9px !important;
}

hr {
    border-color: var(--border);
    margin-top: 28px;
    margin-bottom: 28px;
}

div[data-testid="stFileUploader"] {
    background: #0D131C;
    border: 1px dashed #38475A;
    border-radius: 10px;
    padding: 12px;
}

div[data-testid="stAlert"] {
    border-radius: 10px;
}

.result-label {
    color: var(--gold);
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 1.5px;
    margin-bottom: 12px;
}

.result-panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 25px;
}

[data-testid="stMarkdownContainer"] {
    color: var(--text);
}

[data-testid="stExpander"] {
    border-color: var(--border);
    border-radius: 10px;
}

.small-note {
    color: var(--muted);
    font-size: 12px;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# GROQ CONFIGURATION
# --------------------------------------------------

def get_api_key():
    key = os.getenv("GROQ_API_KEY")

    if not key:
        try:
            key = st.secrets.get("GROQ_API_KEY")
        except Exception:
            key = None

    return key


# --------------------------------------------------
# DOCUMENT EXTRACTION
# --------------------------------------------------

def extract_document(uploaded_file):
    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()
    content = uploaded_file.getvalue()

    try:
        if file_name.endswith(".txt"):
            return content.decode("utf-8", errors="replace")

        elif file_name.endswith(".pdf"):
            pdf = PdfReader(io.BytesIO(content))
            return "\n".join(
                page.extract_text() or ""
                for page in pdf.pages
            )

        elif file_name.endswith(".docx"):
            doc = Document(io.BytesIO(content))
            return "\n".join(
                paragraph.text
                for paragraph in doc.paragraphs
                if paragraph.text.strip()
            )

        else:
            return ""

    except Exception as error:
        st.error(f"Could not read document: {error}")
        return ""


# --------------------------------------------------
# FEEDBACK GENERATION
# --------------------------------------------------

def generate_feedback(
    rubric,
    student_work,
    assignment,
    subject,
    grade_level,
    feedback_tone,
    teacher_focus,
    include_scores
):
    api_key = get_api_key()

    if not api_key:
        raise ValueError(
            "Groq API key not found. Add GROQ_API_KEY to Streamlit secrets."
        )

    client = Groq(api_key=api_key)

    scoring_instruction = (
        "Provide a suggested score for every criterion, using the "
        "rubric's stated maximum marks and weighting. Explain the "
        "reasoning for each suggested score. Do not invent a scoring "
        "scale if the rubric does not provide one."
        if include_scores else
        "Do not assign numerical marks or grades. Focus on qualitative feedback."
    )

    system_prompt = """
You are an experienced educational assessment assistant.

Your job is to help teachers evaluate student work fairly and
consistently using the rubric they provide.

IMPORTANT RULES:

1. Follow the supplied rubric closely.
2. Evaluate every criterion separately.
3. Base your observations ONLY on the student's submitted work.
4. Never invent evidence, quotes, achievements or mistakes.
5. Distinguish between what the student actually demonstrated
   and what is missing.
6. Do not reward writing length instead of quality.
7. Be constructive, specific and educational.
8. Do not make unsupported assumptions about the student.
9. If information is insufficient, explicitly say so.
10. Never claim that the feedback is a final teacher grade.
11. Avoid generic AI-sounding expressions and repetitive praise.
12. Do not use exaggerated language.
13. Keep feedback natural, direct and useful.

The teacher makes the final assessment decision.
"""

    user_prompt = f"""
ASSESSMENT DETAILS

Subject: {subject}
Grade / Level: {grade_level}
Assignment: {assignment}
Feedback tone: {feedback_tone}

TEACHER'S FOCUS:
{teacher_focus if teacher_focus.strip() else "No additional focus specified."}

ASSESSMENT RUBRIC:
{rubric}

STUDENT SUBMISSION:
{student_work}

SCORING INSTRUCTIONS:
{scoring_instruction}

Write the feedback in this exact structure:

# Assignment Feedback

## 1. Overall Assessment
A concise overview of the student's performance.

## 2. Criterion-by-Criterion Evaluation

For EACH criterion in the supplied rubric, provide:

### [Criterion Name]

**What worked:**
Specific evidence from the submission.

**What needs improvement:**
Specific weaknesses or missing elements.

**How to improve:**
One or more actionable suggestions.

**Suggested score:**
Include only when numerical scoring is enabled and the rubric
provides enough information to calculate it.

## 3. Strengths
List the most meaningful demonstrated strengths.

## 4. Priority Improvements
Identify the three most important areas to work on.

## 5. Feedback for the Student
Write a short, natural paragraph addressed directly to the student.

## 6. Teacher Review Notes
Mention any ambiguity in the rubric, insufficient evidence,
or areas that need human judgment.

Keep the feedback tied to the actual submission.
Do not add criteria that are not in the rubric.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.25,
        max_tokens=5000
    )

    return response.choices[0].message.content


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    '<div class="brand">✳ MARKWISE / EDUCATOR WORKSPACE</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="hero-title">Better feedback.<br>'
    '<span style="color:#FFC233">More meaningful learning.</span></div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="hero-sub">'
    'Evaluate student submissions against your assessment rubric. '
    'Get structured, criterion-specific feedback that you can review, '
    'edit and share.'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------
# MAIN INPUT AREA
# --------------------------------------------------

left, right = st.columns([1, 1], gap="large")

with left:

    st.markdown(
        '<div class="step-label">01 / ASSESSMENT DETAILS</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-heading">Assignment information</div>',
                unsafe_allow_html=True)

    st.markdown(
        '<div class="section-caption">Set the context for the evaluation.</div>',
        unsafe_allow_html=True
    )

    subject = st.text_input(
        "Subject",
        placeholder="e.g. Computer Science"
    )

    assignment = st.text_input(
        "Assignment title",
        placeholder="e.g. Introduction to Machine Learning"
    )

    grade_level = st.text_input(
        "Grade / Education level",
        placeholder="e.g. Undergraduate, Year 1"
    )

    feedback_tone = st.selectbox(
        "Feedback style",
        [
            "Balanced and constructive",
            "Direct and detailed",
            "Encouraging and supportive",
            "Formal and academic"
        ]
    )

    teacher_focus = st.text_area(
        "Additional teacher instructions (optional)",
        placeholder="e.g. Pay particular attention to originality, "
                    "technical accuracy and critical thinking.",
        height=105
    )

with right:

    st.markdown(
        '<div class="step-label">02 / ASSESSMENT RUBRIC</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-heading">Define your criteria</div>',
                unsafe_allow_html=True)

    st.markdown(
        '<div class="section-caption">Paste your rubric, including criteria, '
        'descriptions and marks.</div>',
        unsafe_allow_html=True
    )

    rubric = st.text_area(
        "Assessment rubric",
        placeholder="""Example:

1. Understanding of concepts (30 marks)
   - Demonstrates accurate understanding.
   - Explains important concepts clearly.

2. Research and evidence (25 marks)
   - Uses relevant and credible sources.
   - Supports arguments with evidence.

3. Critical thinking (25 marks)
   - Analyses information.
   - Develops independent arguments.

4. Presentation (20 marks)
   - Clear structure and organization.
   - Appropriate academic writing.""",
        height=310
    )

    include_scores = st.toggle(
        "Include suggested numerical scores",
        value=True
    )

    st.caption(
        "Scores are suggestions only. The rubric determines the scoring scale."
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# --------------------------------------------------
# STUDENT SUBMISSION
# --------------------------------------------------

st.markdown(
    '<div class="step-label">03 / STUDENT SUBMISSION</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-heading">Student work</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-caption">Paste the submission or upload a document.</div>',
    unsafe_allow_html=True
)

upload_col, text_col = st.columns([0.85, 1.15], gap="large")

with upload_col:

    uploaded_file = st.file_uploader(
        "Upload student submission",
        type=["pdf", "docx", "txt"],
        help="Supported formats: PDF, DOCX and TXT."
    )

    if uploaded_file:
        st.success(f"Attached: {uploaded_file.name}")

        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("Please upload a file smaller than 10 MB.")
            uploaded_file = None

with text_col:

    student_work = st.text_area(
        "Paste student submission",
        placeholder="The student's assignment will appear here...",
        height=180
    )

    st.caption("You can use either a document upload or pasted text.")

# --------------------------------------------------
# GENERATION
# --------------------------------------------------

st.markdown("<br>", unsafe_allow_html=True)

generate_col, info_col = st.columns([1, 1])

with generate_col:

    generate = st.button(
        "✳  Evaluate student work",
        use_container_width=True
    )

with info_col:

    st.markdown(
        '<p class="small-note" style="padding-top:10px">'
        'Feedback is generated for teacher review. '
        'No grades are submitted automatically.</p>',
        unsafe_allow_html=True
    )

# --------------------------------------------------
# PROCESS SUBMISSION
# --------------------------------------------------

if generate:

    extracted_text = ""

    if uploaded_file:
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("File exceeds the 10 MB upload limit.")
            st.stop()

        extracted_text = extract_document(uploaded_file)

    final_student_work = "\n\n".join(
        part for part in [student_work.strip(), extracted_text.strip()]
        if part
    )

    if not rubric.strip():
        st.error("Please provide an assessment rubric.")

    elif not final_student_work.strip():
        st.error("Please paste or upload the student's work.")

    elif len(final_student_work) > 60000:
        st.error(
            "The submission is too long. Please shorten it to "
            "60,000 characters or less."
        )

    else:

        try:
            with st.spinner(
                "Reviewing the submission against your rubric..."
            ):

                result = generate_feedback(
                    rubric=rubric,
                    student_work=final_student_work,
                    assignment=assignment,
                    subject=subject,
                    grade_level=grade_level,
                    feedback_tone=feedback_tone,
                    teacher_focus=teacher_focus,
                    include_scores=include_scores
                )

            st.session_state["feedback_result"] = result

        except Exception as error:
            st.error(f"Unable to generate feedback: {error}")


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

if st.session_state.get("feedback_result"):

    st.markdown("---")

    st.markdown(
        '<div class="step-label">04 / EVALUATION REPORT</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-heading">Your feedback report</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Review the suggestions before sharing them with the student.'
        '</div>',
        unsafe_allow_html=True
    )

    result = st.session_state["feedback_result"]

    st.markdown('<div class="result-panel">', unsafe_allow_html=True)

    st.markdown(result)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    download_col, clear_col = st.columns([1, 1])

    with download_col:

        st.download_button(
            "↓  Download feedback report",
            data=result,
            file_name="assignment_feedback.txt",
            mime="text/plain",
            use_container_width=True
        )

    with clear_col:

        if st.button(
            "Clear report",
            use_container_width=True
        ):
            del st.session_state["feedback_result"]
            st.rerun()

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.markdown(
    """
    <div style="text-align:center;padding:15px 0;">
        <div class="brand">MARKWISE</div>
        <p class="small-note">
            Thoughtful assessment starts with meaningful feedback.
            <br><br>
            AI-assisted evaluation · Teacher-led decisions
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
