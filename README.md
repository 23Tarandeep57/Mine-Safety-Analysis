# 🛡️ MineGuard AI: A Multi-Agent System for Proactive Mine Safety Analysis (CyberLabs IIT-ISM) 

> **An intelligent, autonomous system for monitoring, analyzing, and reporting on mine safety incidents across India — turning unstructured reports into actionable intelligence.**

---

## 🚨 The Problem

Mine safety remains a **critical challenge** in India, with hundreds of accidents occurring each year. Despite extensive reporting by the **Directorate General of Mines Safety (DGMS)** and news agencies, current data dissemination faces major issues:

- 🧾 **Unstructured & Disparate** — Reports are often published as PDFs, HTML tables, or unformatted news articles.  
- 🧩 **Difficult to Aggregate** — Manual data collection is slow, inconsistent, and error-prone.  
- 🔍 **Hard to Query** — No unified database exists for performing queries, trend analysis, or real-time insights.

This results in **information latency**, where insights that could prevent accidents are buried in paperwork and fragmented reports.

---

## 🤖 The Solution: MineGuard AI

**MineGuard AI** is a **multi-agent, AI-driven system** that automates the full lifecycle of mine safety data — from ingestion to analysis and conversational access.

It autonomously performs:

1. **Data Ingestion** — Scrapes DGMS and news reports.  
2. **Intelligent Structuring** — Converts unstructured text/PDFs into structured JSON data.  
3. **Data Enrichment** — Maps missing or vague entries to official DGMS codes using AI-powered semantic matching.  
4. **Conversational Querying** — Enables natural-language interaction for trend analysis, summaries, and Q&A.  
5. **Accident Pattern Analysis** — Uses historical data to analyze seasonal, temporal, and geographical trends in accidents.  
6. **Proactive Alert Generation** — Continuously monitors new reports to generate early alerts for high-risk patterns.  

This transforms a **reactive** manual process into a **proactive**, AI-powered safety intelligence system.

---

## 🧠 System Architecture

MineGuard AI follows a **multi-agent architecture** — a distributed, asynchronous design where each agent performs specialized tasks and communicates through a central **Message Bus**.

### ⚙️ Core Components

| Component | Role |
|------------|------|
| 🕵️‍♂️ **DGMSMonitorAgent** | Collects reports from the official DGMS website |
| ⚙️ **NewsScannerAgent** | Collects and publishes incident data from official and media sources |
| 🧩 **IncidentAnalysisAgent** | Parses, enriches, and analyzes incident data using AI; acts as the system’s control center |
| 💬 **ConversationalAgent** | Handles user queries using RAG (Retrieval-Augmented Generation) |
| 📊 **AccidentAnalysisModule** | Performs seasonal, temporal, and cause-based accident trend analysis |
| 🚨 **AlertGenerator** | Detects high-risk patterns (e.g., repeated methane explosions in a specific region) and generates alerts |
| 🗃️ **MongoDB** | Stores structured incident data |
| 🧠 **ChromaDB** | Handles vector embeddings and semantic search for cause-code mapping |

All agents interact with each other using A2A protocol with **IncidentAnalysisAgent** as the main control centre of the system.

---

## ⚡ Technical Innovations & Features

### 1. AI-Powered Cause Code Mapping

Automatically maps free-text causes like  
> “Landslide”  
to an official DGMS code like  
> **0118 — Landslide**

**How it Works:**
- Preloads DGMS cause-code descriptions into a **ChromaDB vector store**  
- Embeds each new incident’s description  
- Performs **semantic similarity search** to find the most relevant DGMS code  

✅ *More accurate and context-aware than keyword-based methods.*

---

### 2. Retrieval-Augmented Generation (RAG) for Q&A

MineGuard AI’s chatbot delivers **factually grounded** responses.

**Pipeline:**
1. User query → contextualized and used to retrieve relevant documents  
2. Data fetched from **MongoDB (structured)** and **ChromaDB (semantic)**  
3. Retrieved context → injected into the LLM prompt for accurate synthesis  

💡 *Enables data-driven, explainable answers directly from verified sources.*

---

### 3. Accident Pattern Analysis

The **AccidentAnalysisModule** provides insights into:
- ⏳ **Temporal Trends:** Accidents by month, season, or year  
- 🌦️ **Seasonal Correlation:** Detects higher risks during specific weather conditions  
- 📍 **Geographical Patterns:** Hotspot regions prone to certain types of accidents  
- ⚙️ **Cause Distribution:** Frequent causes by mine type and state  

🧩 *Also provides recommendations to avoid accidents using historical data Helps decision-makers predict and mitigate risks before they escalate.*

---

### 4. Proactive Alert Generation

The **AlertGenerator** continuously scans new incidents for:
- Recurrent patterns (e.g., repeated gas explosions in the same region)  
- Seasonal spikes in accident frequency  
- Sudden anomalies in causes or severity  

⚠️ When thresholds are breached, **MineGuard AI** automatically generates alerts and stores them in MongoDB for dashboard visualization or email notifications.

---

### 5. Asynchronous Multi-Agent System

Each agent runs independently via `asyncio`, enabling:
- Concurrent scraping, analysis, and Q&A  
- High throughput and scalability  
- Fault-tolerant design (agents can restart independently)

---

## 🧰 Tech Stack

| Layer | Tools & Technologies |
|-------|----------------------|
| **Backend** | Python, Flask, asyncio |
| **AI/ML** | LangChain, Google Generative AI |
| **Databases** | MongoDB (Primary), ChromaDB (Vector Store) |
| **Data Processing** | PyPDF, BeautifulSoup, Pandas |
| **Architecture** | Custom Multi-Agent System |

---

## 🚀 Setup & Installation

### 🧱 Prerequisites
- Python **3.10+**
- **MongoDB** instance (local or MongoDB Atlas)
- `git` for cloning

### 🔧 Steps

```bash
# 1. Clone the repository
git clone https://github.com/23Tarandeep57/Mine-Safety-Analysis.git
cd Mine-Safety-Analysis

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables (MongoDB URI, API keys, etc.)
cp .env.example .env
# Edit .env with your configurations

# 5. Run the Flask server
python app.py
