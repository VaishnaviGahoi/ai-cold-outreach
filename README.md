# ✉️ AI Cold Outreach Personalizer

> Day 3 of 7 — by Vaishnavi Gahoi

Generate fully drafted, hyper-personalised cold emails and LinkedIn DMs for any prospect list — in seconds.

---

## 🚀 Features

- Upload prospects as **CSV or Excel** (Name, Company, Role)
- Choose output: **Cold Email** (Subject + Body) or **LinkedIn DM**
- Set your **goal**: get a meeting, sell, or explore a partnership
- Control **tone** via dropdown + free-text override
- Fill in your sender profile once — structured fields + free text overflow
- **Edit messages** inline before exporting
- **Download** all results as CSV or Excel

---

## 🛠️ Stack

| Layer | Tool |
|-------|------|
| LLM | Groq API — `llama-3.1-8b-instant` (free) |
| UI | Streamlit |
| Data | Pandas, openpyxl |
| Export | CSV + Excel (built-in) |

---

## ⚡ Quickstart

### 1. Clone / download this folder

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your Groq API key
Create a file at `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "gsk_your_key_here"
```
Get a free key at: https://console.groq.com

### 4. Run
```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
ai-cold-outreach/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
├── sample_prospects.csv    # Sample input file to test with
├── .streamlit/
│   └── secrets.toml        # Your Groq API key (create this)
└── README.md
```

---

## 📋 Input File Format

Your CSV or Excel must have these columns:

| Name | Company | Role |
|------|---------|------|
| Rahul Sharma | Zepto | Head of Operations |
| Priya Mehta | Razorpay | Product Manager |

`Role` column is optional — app works without it.

---

## 🌐 Deploy to Streamlit Cloud (free)

1. Push this folder to a GitHub repo
2. Go to https://streamlit.io/cloud → New app
3. Add `GROQ_API_KEY` under **Secrets** in app settings
4. Deploy ✅

---

## 💡 LinkedIn Post Angle

> "Every founder writes the same cold email 50 times. I built a tool that drafts a fully personalised message per prospect — cold email or LinkedIn DM, any goal, any tone. Upload your list, describe yourself, hit generate. Day 3 of 7."

---

Built with ❤️ using Groq + Streamlit
