import streamlit as st
import pandas as pd
import csv
import io
import time
from groq import Groq

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Cold Outreach Personalizer",
    page_icon="✉️",
    layout="wide"
)

st.title("✉️ AI Cold Outreach Personalizer")
st.caption("Paste your prospect list → fill in your details → get fully drafted, personalised messages in seconds.")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Session State ────────────────────────────────────────────────────────────
if "prospects_df" not in st.session_state:
    st.session_state.prospects_df = None

if "results" not in st.session_state:
    st.session_state.results = []

if "history" not in st.session_state:
    st.session_state.history = []

if "last_uploaded_filename" not in st.session_state:
    st.session_state.last_uploaded_filename = None

# ── Sidebar — Sender Profile ────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 About You")

    sender_name = st.text_input("Your Name", placeholder="Vaishnavi Gahoi")
    sender_company = st.text_input("Your Company / Product", placeholder="e.g. Acme AI")
    sender_role = st.text_input("Your Role", placeholder="e.g. Founder, Sales Lead")
    what_you_offer = st.text_input(
        "What you offer (one line)",
        placeholder="e.g. AI automation that cuts ops time by 30%"
    )
    why_reach_out = st.text_area(
        "Why are you reaching out to these people?",
        placeholder="e.g. They run D2C brands doing 1Cr+ GMV and would benefit from automated customer support.",
        height=80
    )
    extra_context = st.text_area(
        "Anything else? (optional free text)",
        placeholder="e.g. We just launched, I admire their recent Series A, etc.",
        height=70
    )

    st.divider()
    st.header("⚙️ Message Settings")

    output_format = st.selectbox("Output Format", ["Cold Email (Subject + Body)", "LinkedIn DM"])
    goal = st.selectbox("Goal of Outreach", ["Get a meeting / demo call", "Sell a product or service", "Explore a partnership"])
    tone = st.selectbox("Tone", ["Friendly", "Formal", "Direct", "Conversational"])
    tone_override = st.text_input("Override tone (optional)", placeholder="e.g. casual but confident, no buzzwords")

    st.divider()
    if st.button("🧹 Clear Current Results"):
        st.session_state.results = []
        st.rerun()

    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.rerun()

# ── Main — Prospect Upload ──────────────────────────────────────────────────
st.subheader("📋 Upload Your Prospect List")
st.markdown("Upload a **CSV or Excel** file with columns: `Name`, `Company`, `Role` *(Role is optional)*")

uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])

if uploaded_file:
    # Only re-read if a new file is uploaded
    if st.session_state.last_uploaded_filename != uploaded_file.name:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Normalize column names
            df.columns = [c.strip().title() for c in df.columns]

            if "Name" not in df.columns or "Company" not in df.columns:
                st.error("❌ File must have at least 'Name' and 'Company' columns.")
                st.session_state.prospects_df = None
            else:
                if "Role" not in df.columns:
                    df["Role"] = ""
                df = df[["Name", "Company", "Role"]].fillna("")

                st.session_state.prospects_df = df
                st.session_state.last_uploaded_filename = uploaded_file.name

        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.session_state.prospects_df = None

df = st.session_state.prospects_df

if df is not None:
    st.success(f"✅ {len(df)} prospects loaded.")
    st.dataframe(df, use_container_width=True)

# ── Prompt Builder ───────────────────────────────────────────────────────────
def build_prompt(name, company, role, sender_name, sender_company, sender_role,
                 what_you_offer, why_reach_out, extra_context,
                 output_format, goal, tone, tone_override):

    effective_tone = tone_override.strip() if tone_override.strip() else tone
    role_line = f" — {role}" if role.strip() else ""
    is_email = "Cold Email" in output_format

    tone_guides = {
        "Friendly": """
TONE RULES — FRIENDLY:
- Write like you're messaging a warm acquaintance, not a stranger
- Use contractions (I'm, you've, we're)
- Include one genuine compliment about their work or company
- End with something warm like "Would love to chat!" or "Hope to connect!"
- Forbidden: formal salutations, corporate jargon, passive voice
- Example opener style: Reference something specific they built or achieved — be curious, not flattering. Never use the phrase "the results speak for themselves."
""",
        "Formal": """
TONE RULES — FORMAL:
- Write like a senior business professional addressing a peer
- No contractions, no slang, no casual phrases
- Use full sentences, precise language, professional salutation
- Structure: context → value proposition → clear ask → professional close
- Forbidden: exclamation marks, emojis, casual phrases like "Hey" or "Hope you're doing well"
- Example opener: "I am reaching out regarding a potential collaboration that may be of interest to [Company]."
""",
        "Direct": """
TONE RULES — DIRECT:
- Get to the point in the first sentence — no warm-up
- Short sentences. One idea per sentence. No filler.
- State exactly what you want and why in under 3 lines
- CTA must be a specific ask with a specific time (e.g. "15 mins this week?")
- Forbidden: long intros, pleasantries, anything that doesn't add value
- Example opener: "I help [type of company] do [specific result]. Thought [Company] could use this."
""",
        "Conversational": """
TONE RULES — CONVERSATIONAL:
- Write exactly how you'd speak out loud to someone at a coffee meeting
- Use incomplete sentences if natural. Ask a question early.
- Show genuine curiosity about their work
- Be a little vulnerable or self-aware ("I know everyone's inbox is flooded, so I'll keep this short")
- Forbidden: anything that sounds like a template, bullet points, formal sign-offs
- Example opener: "Quick question — are you still handling [X] manually at [Company]?"
"""
    }

    tone_instruction = tone_guides.get(effective_tone, f"Tone: {effective_tone}. Write naturally in this tone throughout.")

    format_instruction = (
        """FORMAT — COLD EMAIL:
Subject: One punchy line. No clickbait. Max 8 words. Make it feel personal, not promotional.
Body:
- Line 1: Something specific about THEM — their company, a recent move, their industry. NOT about you.
- Line 2-3: What you do and why it's specifically relevant to their situation.
- Line 4: One clear CTA — specific ask, low commitment (e.g. "Worth a 15-min call this week?")
- Sign off: Natural, matches tone.
No placeholders. Fill every detail in."""
    ) if is_email else (
        """FORMAT — LINKEDIN DM:
- 4-6 sentences MAX. If it's longer, cut it.
- No subject line.
- Open with something specific about them or their company (not a compliment on their "impressive profile")
- One sentence on what you do
- One sentence on why you're reaching out to THEM specifically
- One CTA: simple, low pressure
- No bullet points. No formatting. Just natural flowing text."""
    )

    goal_instruction = {
        "Get a meeting / demo call": "The ONE goal is to get them to agree to a short call. Everything else is secondary. Don't oversell — just get the meeting.",
        "Sell a product or service": "Lead with the problem they likely have, then position your product as the obvious solution. Include a specific result or number if possible.",
        "Explore a partnership": "Frame this as mutually beneficial. Show you've thought about what THEY get out of it, not just what you want."
    }.get(goal, goal)

    return f"""You are an expert cold outreach writer. Your messages consistently get 30%+ reply rates.

PROSPECT:
- Name: {name}
- Company: {company}{role_line}

SENDER:
- Name: {sender_name}
- Company/Product: {sender_company}
- Role: {sender_role}
- What they offer: {what_you_offer}
- Why reaching out to this person specifically: {why_reach_out}
- Extra context: {extra_context if extra_context.strip() else 'None'}

GOAL: {goal_instruction}

{tone_instruction}

{format_instruction}

HARD RULES (non-negotiable):
- NEVER open with "I hope this finds you well", "I came across your profile", "I wanted to reach out"
- NEVER use: synergy, leverage, cutting-edge, innovative, game-changing, dynamic
- Do NOT write a generic message that could be sent to anyone — this must feel written specifically for {name} at {company}
- If you don't have specific info about them, make reasonable intelligent inferences from their company name and industry
- Respect their time — every sentence must earn its place
- NEVER end with "Worth a 15-min call this week?" — vary the CTA naturally based on tone and goal
- Each message CTA must be worded differently from the others

Write the message now. Output ONLY the message, nothing else:"""

# ── Generate ────────────────────────────────────────────────────────────────
if st.button("🚀 Generate Messages", type="primary", disabled=(df is None)):
    st.session_state.results = []
    missing = [f for f, v in {
        "Your Name": sender_name,
        "Your Company": sender_company,
        "Your Role": sender_role,
        "What you offer": what_you_offer,
        "Why reach out": why_reach_out
    }.items() if not v.strip()]

    if missing:
        st.warning(f"Please fill in: {', '.join(missing)}")
    else:
        results = []
        st.session_state.results = []
        progress = st.progress(0, text="Generating messages...")
        status = st.empty()

        for i, row in df.iterrows():
            name = str(row["Name"]).strip()
            company = str(row["Company"]).strip()
            role = str(row["Role"]).strip()

            status.markdown(f"**Writing message {i+1}/{len(df)}** — {name} @ {company}")

            prompt = build_prompt(
                name, company, role,
                sender_name, sender_company, sender_role,
                what_you_offer, why_reach_out, extra_context,
                output_format, goal, tone, tone_override
            )

            try:
                import random
                cache_buster = random.randint(10000, 99999)
                prompt_with_seed = f"[Run ID: {cache_buster}]\n\n{prompt}"
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt_with_seed}],
                    temperature=0.95,
                    max_tokens=600,
                    seed=cache_buster
                )
                message = response.choices[0].message.content.strip()
            except Exception as e:
                message = f"Error: {e}"

            results.append({
                "Name": name,
                "Company": company,
                "Role": role,
                "Format": output_format,
                "Goal": goal,
                "Tone": tone_override.strip() or tone,
                "Message": message
            })

            progress.progress((i + 1) / len(df), text=f"Done {i+1}/{len(df)}")
            time.sleep(0.3)  # avoid rate limit

        status.empty()
        progress.empty()

        st.session_state.results = results

        run_record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "file_name": st.session_state.last_uploaded_filename,
            "format": output_format,
            "goal": goal,
            "tone": tone_override.strip() or tone,
            "results": results.copy()
        }
        st.session_state.history.insert(0, run_record)

        st.success(f"✅ {len(results)} messages generated!")

# ── Results & History ───────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📨 Current Results", "🕘 History"])

with tab1:
    if st.session_state.results:
        st.subheader("📨 Generated Messages")

        for idx, r in enumerate(st.session_state.results):
            with st.expander(f"**{r['Name']}** @ {r['Company']}", expanded=True):
                st.markdown(f"`{r['Format']}` · `{r['Goal']}` · Tone: `{r['Tone']}`")

                edited_message = st.text_area(
                    "Message",
                    value=r["Message"],
                    height=250,
                    key=f"msg_{idx}_{r['Name']}_{r['Company']}"
                )

                # Persist edits
                st.session_state.results[idx]["Message"] = edited_message

        st.divider()
        results_df = pd.DataFrame(st.session_state.results)

        csv_buffer = io.StringIO()
        results_df.to_csv(csv_buffer, index=False, quoting=csv.QUOTE_ALL)

        st.download_button(
            label="⬇️ Download Current Results as CSV",
            data=csv_buffer.getvalue(),
            file_name="outreach_messages.csv",
            mime="text/csv"
        )

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            results_df.to_excel(writer, index=False, sheet_name="Outreach")
        excel_buffer.seek(0)

        st.download_button(
            label="⬇️ Download Current Results as Excel",
            data=excel_buffer,
            file_name="outreach_messages.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No messages generated yet.")

with tab2:
    st.subheader("🕘 Past Runs")

    if st.session_state.history:
        for i, run in enumerate(st.session_state.history):
            title = f"{run['timestamp']} · {run['file_name']} · {len(run['results'])} messages"
            with st.expander(title, expanded=(i == 0)):
                st.markdown(
                    f"**Format:** {run['format']}  \n"
                    f"**Goal:** {run['goal']}  \n"
                    f"**Tone:** {run['tone']}"
                )

                run_df = pd.DataFrame(run["results"])
                st.dataframe(run_df, use_container_width=True)

                csv_buffer = io.StringIO()
                run_df.to_csv(csv_buffer, index=False, quoting=csv.QUOTE_ALL)

                st.download_button(
                    label=f"⬇️ Download run {i+1} as CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"outreach_history_run_{i+1}.csv",
                    mime="text/csv",
                    key=f"history_csv_{i}"
                )
    else:
        st.info("No history yet.")

# ── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.caption("Built with Groq (llama-3.1-8b-instant) + Streamlit · by Vaishnavi Gahoi")
