import streamlit as st
import random
from supabase import create_client
import time

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

# --- Load Scenarios: Patient Names ---
@st.cache_data(ttl=600)
def load_all_patient_names():
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = client.table("patient_questions").select("patient_name").execute()
        patient_names = list({row["patient_name"] for row in response.data})
        return sorted(patient_names)
    except Exception as e:
        st.error(f"Error loading patient names: {e}")
        return []

# --- Load Questions ---
@st.cache_data(ttl=600)
def load_all_questions(patient_name):
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = client.table("patient_questions")\
            .select("*")\
            .eq("patient_name", patient_name)\
            .order("id", desc=True)\
            .limit(20)\
            .execute()
    
            # Get 20 questions between fixed id limits
            # .gte("id", 100)\
            # .lte("id", 200)\
            # .order("id", desc=True)\
            # .limit(20)\
            # .execute()
        question_list = []

        for row in response.data:
            raw_options = [row["opt1"], row["opt2"], row["opt3"], row["opt4"]]
            clean_options = []
            correct_index = row["correct_index"]  # 1-based in DB

            for i, opt in enumerate(raw_options):
                if opt.strip():
                    clean_options.append(opt)

            if correct_index < 1 or correct_index > len(raw_options) or not raw_options[correct_index - 1].strip():
                correct_index = 1

            question_list.append({
                "id": row["id"],
                "prompt": row["prompt"],
                "options": clean_options,
                "correct_index": correct_index - 1 
            })

        return question_list

    except Exception as e:
        st.error(f"Error loading questions from Supabase: {e}")
        return []
    
# --- Load Post Quiz Questions ---
@st.cache_data(ttl=600)
def load_post_quiz_questions():
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = client.table("post_quiz_questions")\
            .select("*")\
            .order("id", desc=True)\
            .execute()
    
        question_list = []

        for row in response.data:
            

            question_list.append({
                "id": row["id"],
                "question": row["question"]
            })

        return question_list

    except Exception as e:
        st.error(f"Error loading questions from Supabase: {e}")
        return []

# --- Page Routing ---
if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    st.title("DSR System Quiz")
    patient_names = load_all_patient_names()
    selected_patient = st.selectbox("Select a patient scenario", patient_names)
    username = st.text_input("Enter your name")

    if st.button("Start Quiz") and username.strip():
        st.session_state.page = "quiz"
        st.session_state["patient_name"] = selected_patient
        st.session_state["username"] = username.strip()
        st.session_state["quiz_start_time"] = time.time()
        st.rerun()

# elif st.session_state.page == "quiz":
#     # --- Session State Initialization ---
#     if "shuffled_questions" not in st.session_state:
#         all_qs = load_all_questions(st.session_state["patient_name"])
#         random.shuffle(all_qs)

#         st.session_state["shuffled_questions"] = all_qs
#         st.session_state["options_shuffled"] = {}
#         st.session_state["shuffled_to_original_map"] = {}

#         for q in all_qs:
#             original_opts = q["options"]
#             shuffled_opts = original_opts.copy()
#             random.shuffle(shuffled_opts)

#             # Map each shuffled option to its original index (0-based)
#             mapping = {shuffled_opt: original_opts.index(shuffled_opt) for shuffled_opt in shuffled_opts}

#             st.session_state["options_shuffled"][q["id"]] = shuffled_opts
#             st.session_state["shuffled_to_original_map"][q["id"]] = mapping

#         st.session_state["answers"] = {q["id"]: None for q in all_qs}
#         st.session_state["submitted"] = False

#     # --- Answer Change Callback ---
#     def on_option_change(qid):
#         st.session_state["answers"][qid] = st.session_state.get(f"q_{qid}", None)

#     # --- Main UI Before Submission ---
#     if not st.session_state["submitted"]:
#         st.title("DSR System Quiz")
#         st.markdown(f"**User:** {st.session_state['username']}")
#         st.write("---")
#         # Render each question in the shuffled order
#         for idx, q in enumerate(st.session_state["shuffled_questions"]):
#             qid = q["id"]
#             prompt = q["prompt"]
#             opts = st.session_state["options_shuffled"][qid]
#             st.markdown(f"**Q{idx+1}. {prompt}**")
#             st.radio(
#                 label = f"**Q{idx+1}. {prompt}**",
#                 label_visibility = "collapsed",
#                 options=opts,
#                 index=None,
#                 key=f"q_{qid}",
#                 on_change=lambda qid=qid: on_option_change(qid),
#             )
#             st.markdown("")


#         st.write("---")
        
#         # Answer count
#         num_answered = sum(ans is not None for ans in st.session_state["answers"].values())
#         total_qs = len(st.session_state["shuffled_questions"])
#         st.info(f"**{num_answered} out of {total_qs}** questions answered.")

#         # Submission
#         if st.button("Submit"):
#             if not st.session_state["username"].strip():
#                 st.warning("Please enter your name before submitting.")
#             else:
#                 st.session_state["submitted"] = True
#                 st.rerun()

#     else:
#         username = st.session_state.get("username", "anonymous")
#         answers = st.session_state["answers"]
#         shuffled_qs = st.session_state["shuffled_questions"]
#         supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

#         def write_submissions(username, answers, shuffled_qs):
#             all_questions = {q["id"]: q for q in load_all_questions(st.session_state["patient_name"])}
#             records = []

#             quiz_duration_sec = int(time.time() - st.session_state.get("quiz_start_time", time.time()))

#             for q in shuffled_qs:
#                 qid = q["id"]
#                 chosen = answers.get(qid)
#                 if chosen is None:
#                     chosen_str = None
#                     is_corr = False
#                 else:
#                     # Use original option mapping to determine correctness
#                     original_index = st.session_state["shuffled_to_original_map"][qid].get(chosen, -1)
#                     correct_index = all_questions[qid]["correct_index"]
#                     correct_option = all_questions[qid]["options"][correct_index]

#                     chosen_str = chosen
#                     is_corr = (original_index == correct_index)

#                 records.append({
#                     "username": username,
#                     "question_id": qid,
#                     "chosen_option": chosen_str,
#                     "is_correct": is_corr,
#                     "patient_name": st.session_state["patient_name"],
#                     "quiz_time": quiz_duration_sec
#                 })

#             try:
#                 response = supabase.table("patient_submissions").insert(records).execute()
#                 st.success("Results submitted successfully.")
#             except Exception as e:
#                 st.error(f"Failed to save results: {e}")

#         write_submissions(username, answers, shuffled_qs)

#         st.session_state.page = "quiz_submission"
#         st.rerun()

elif st.session_state.page == "quiz":
    import uuid
    from datetime import datetime

    if "shuffled_questions" not in st.session_state:
        st.session_state["quiz_start_time"] = time.time()
        all_qs = load_all_questions(st.session_state["patient_name"])
        random.shuffle(all_qs)

        st.session_state["shuffled_questions"] = all_qs
        st.session_state["options_shuffled"] = {}
        st.session_state["shuffled_to_original_map"] = {}

        for q in all_qs:
            original_opts = q["options"]
            shuffled_opts = original_opts.copy()
            random.shuffle(shuffled_opts)
            mapping = {shuffled_opt: original_opts.index(shuffled_opt) for shuffled_opt in shuffled_opts}
            st.session_state["options_shuffled"][q["id"]] = shuffled_opts
            st.session_state["shuffled_to_original_map"][q["id"]] = mapping

        st.session_state["answers"] = {q["id"]: None for q in all_qs}
        st.session_state["question_start_times"] = {}  # qid → when displayed
        st.session_state["question_times"] = {}        # qid → time taken
        st.session_state["question_submit_times"] = {}
        st.session_state["answer_order"] = []

        st.session_state["submitted"] = False

    def on_option_change(qid):
        now = time.time()

        # First answer for this question
        if qid not in st.session_state["question_submit_times"]:
            st.session_state["question_submit_times"][qid] = now
            st.session_state["answer_order"].append(qid)

            if len(st.session_state["answer_order"]) == 1:
                # First question answered → use render time
                q_start = st.session_state["question_start_times"].get(qid, st.session_state["quiz_start_time"])
            else:
                # Get time of previous answered question
                prev_qid = st.session_state["answer_order"][-2]
                q_start = st.session_state["question_submit_times"][prev_qid]

            elapsed = now - q_start
            st.session_state["question_times"][qid] = elapsed

        # Save the selected option
        st.session_state["answers"][qid] = st.session_state.get(f"q_{qid}", None)


    if not st.session_state["submitted"]:
        st.title("DSR System Quiz")
        st.markdown(f"**User:** {st.session_state['username']}")
        st.write("---")

        for idx, q in enumerate(st.session_state["shuffled_questions"]):
            qid = q["id"]
            prompt = q["prompt"]
            opts = st.session_state["options_shuffled"][qid]

            # record first render time
            if qid not in st.session_state["question_start_times"]:
                st.session_state["question_start_times"][qid] = time.time()

            st.markdown(f"**Q{idx+1}. {prompt}**")
            st.radio(
                label=f"Q{idx+1}. {prompt}",
                label_visibility="collapsed",
                options=opts,
                index=None,
                key=f"q_{qid}",
                on_change=lambda qid=qid: on_option_change(qid),
            )
            st.markdown("")

        st.write("---")

        num_answered = sum(ans is not None for ans in st.session_state["answers"].values())
        total_qs = len(st.session_state["shuffled_questions"])
        st.info(f"**{num_answered} out of {total_qs}** questions answered.")

        if st.button("Submit"):
            st.session_state["submitted"] = True
            st.rerun()

    else:
        username = st.session_state.get("username", "anonymous")
        answers = st.session_state["answers"]
        shuffled_qs = st.session_state["shuffled_questions"]
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        quiz_log_id = str(uuid.uuid4())
        started_at = datetime.fromtimestamp(st.session_state["quiz_start_time"]).isoformat()
        submitted_at = datetime.now().isoformat()

        # Prepare answered_times JSON
        answered_times = [
            {
                "qid": q["id"],
                "time_taken": st.session_state["question_times"].get(q["id"], None)
            }
            for q in shuffled_qs
        ]

        # Write to quiz_logs table
        quiz_log = {
            "quiz_log_id": quiz_log_id,
            "username": username,
            "patient_name": st.session_state["patient_name"],
            "started_at": started_at,
            "submitted_at": submitted_at,
            "answered_times": answered_times
        }

        try:
            supabase.table("quiz_logs").insert([quiz_log]).execute()
            st.success("Quiz log recorded.")
        except Exception as e:
            st.error(f"Failed to save quiz log: {e}")

        # Write to patient_submissions table
        def write_submissions(username, answers, shuffled_qs, quiz_log_id):
            all_questions = {q["id"]: q for q in load_all_questions(st.session_state["patient_name"])}
            records = []

            for q in shuffled_qs:
                qid = q["id"]
                chosen = answers.get(qid)
                if chosen is None:
                    chosen_str = None
                    is_corr = False
                else:
                    original_index = st.session_state["shuffled_to_original_map"][qid].get(chosen, -1)
                    correct_index = all_questions[qid]["correct_index"]
                    chosen_str = chosen
                    is_corr = (original_index == correct_index)

                records.append({
                    "quiz_time": quiz_log_id,
                    "username": username,
                    "question_id": qid,
                    "chosen_option": chosen_str,
                    "is_correct": is_corr,
                    "patient_name": st.session_state["patient_name"]
                })

            try:
                supabase.table("patient_submissions").insert(records).execute()
                st.success("Patient submissions recorded.")
            except Exception as e:
                st.error(f"Failed to save patient submissions: {e}")

        write_submissions(username, answers, shuffled_qs, quiz_log_id)

        # st.session_state.page = "quiz_submission"
        # st.rerun()

elif st.session_state.page == "quiz_submission":
    


    username = st.session_state.get("username", "anonymous")
    answers = st.session_state["answers"]
    shuffled_qs = st.session_state["shuffled_questions"]
    # Compute score
    # Score
    num_correct = 0
    for q in shuffled_qs:
        qid = q["id"]
        selected = answers.get(qid)
        if selected is None:
            continue

        # Get the original index of selected option
        original_index = st.session_state["shuffled_to_original_map"][qid].get(selected, -1)

        # Check if this original index matches correct_index
        if original_index == q["correct_index"]:
            num_correct += 1

    st.success(f"Thanks, **{username}**! You answered **{num_correct}** questions correctly.")

    st.write("---")
    # Show per-question feedback
    # Show per-question feedback
    for idx, q in enumerate(shuffled_qs):
        qid = q["id"]
        prompt = q["prompt"]
        chosen = answers.get(qid)
        
        st.markdown(f"**Q{idx + 1}. {prompt}**")

        if chosen is None:
            st.markdown("<span style='color:gray;'>No answer selected.</span>", unsafe_allow_html=True)
            continue

        original_index = st.session_state["shuffled_to_original_map"][qid].get(chosen, -1)
        is_correct = original_index == q["correct_index"]

        color = "green" if is_correct else "red"
        status = "Correct" if is_correct else "Incorrect"

        st.markdown(
            f"<span style='color:{color};'><b>Your answer:</b> {chosen}</span><br>"
            f"<span style='color:{color};'><i>{status}</i></span>",
            unsafe_allow_html=True
        )


    if st.button("Go To Survey"):
        st.session_state.page = "post_quiz"
        st.rerun()

elif st.session_state.page == "post_quiz":
    username = st.session_state.get("username", "anonymous")
    st.markdown("### Post Quiz Survey")
    st.markdown("---")

    st.write(f"Hello, {username}")
    opts = list(range(1,8))
    likert_labels = {
        1: "Strongly Disagree",
        2: "Disagree",
        3: "Somewhat Disagree",
        4: "Neutral",
        5: "Somewhat Agree",
        6: "Agree",
        7: "Strongly Agree"
    }
    if opts[-1] == 5:
        likert_labels = {
            1: "Strongly Disagree",
            2: "Disagree",
            3: "Neutral",
            4: "Agree",
            5: "Strongly Agree"
        }

        
    st.write("#### 📝 Please complete the following survey")
    st.markdown(
        """This survey helps us understand how well the AI explanations supported your trust in the system and your ability to choose the next steps for the patient's care in the given scenario. Your feedback will help us improve the clarity and usefulness of the explanations for future users."""
    )
    
    st.write("---")

    if "post_quiz_questions" not in st.session_state:        
        post_quiz_questions = load_post_quiz_questions()

        random.shuffle(post_quiz_questions)

        st.session_state.post_quiz_questions = post_quiz_questions
        st.session_state.post_quiz_answers = {q["id"]: None for q in post_quiz_questions}
    
    def post_quiz_on_option_change(qid):
            st.session_state["post_quiz_answers"][qid] = st.session_state.get(f"q_{qid}", None)
    
    for idx,q in enumerate (st.session_state.post_quiz_questions):

        question = q["question"]
        qid = q["id"]
        
        st.markdown(f"**Q{idx+1}. {question}**")
        col1,col2,col3 = st.columns([2.5, 6, 2])
        with col1:
            st.markdown("""
            <div style='display:flex; align-items:center; height:100%; padding-top:0.5rem'>
                Strongly Disagree
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.radio(
                label=f"Q{idx+1}. {question}",
                label_visibility = "collapsed",
                options=opts,
                index=None,
                key=f"q_{qid}",
                horizontal = True,
                on_change = lambda qid=qid:post_quiz_on_option_change(qid)
            )
        with col3:
            st.markdown("""
            <div style='display:flex; align-items:center; height:100%; padding-top:0.5rem'>
                Strongly Agree
            </div>
            """, unsafe_allow_html=True)
        st.markdown("")
    
    if st.button("Submit"):
        unanswered = [qid for qid, ans in st.session_state.post_quiz_answers.items() if ans is None]

        if unanswered:
            st.error("Please answer all questions before submitting.")
        else:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            def write_post_quiz_submissions(username, questions, answers):
                records =[]
                for question in questions:
                    q = question["question"]
                    qid = question["id"]
                    answer = answers[qid]

                    records.append({
                            "question_id":qid,
                            "question":q,
                            "username":username,
                            "answer":answer,
                            "patient_name": st.session_state["patient_name"]})
                    
                try:
                    response = supabase.table("post_quiz_submissions").insert(records).execute()
                    st.success("Post Quiz Survey submitted successfully.")
                except Exception as e:
                    st.error(f"Failed to save post quiz results: {e}")
            
            write_post_quiz_submissions(username, st.session_state.post_quiz_questions, st.session_state.post_quiz_answers)
        
    st.stop()

