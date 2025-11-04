# 🛡️ MineGuard AI: A Multi-Agent System for Proactive Mine Safety Analysis (CyberLabs IIT-ISM)

> **An intelligent, autonomous system that transforms unstructured mine safety reports into actionable insights — enabling proactive monitoring, analysis, and prevention of mine accidents in India.**

---

## 🧭 Summary (In Brief)

**MineGuard AI** automates the entire mine safety intelligence pipeline — from **data collection and structuring** to **semantic enrichment, analysis, and alert generation**.  
It uses a **multi-agent architecture** with AI-driven reasoning and natural language querying to provide **real-time situational awareness** and **predictive insights** for accident prevention.

**In essence:**  
> MineGuard AI reads, understands, retrieve and analyzes every mine accident report and generate solutions to prevent accidents — so humans can focus on saving lives, not parsing data.

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
5. **Accident Pattern Analysis** — Uses historical data to analyze seasonal, temporal, and geographical trends.  
6. **Proactive Alert Generation** — Monitors new reports to generate early alerts for high-risk patterns.  

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
| 🚨 **AlertGenerator** | Detects high-risk patterns and generates alerts |
| 🗃️ **MongoDB** | Stores structured incident data |
| 🧠 **ChromaDB** | Handles vector embeddings and semantic search for cause-code mapping |

All agents interact with each other using **A2A protocol**, with the **IncidentAnalysisAgent** as the control center.

---

## ⚡ Technical Innovations & Features

### 1. AI-Powered Cause Code Mapping
Automatically maps free-text causes like  
> “Landslide”  
to official DGMS code  
> **0118 — Landslide**

**How it Works:**
- DGMS cause-code descriptions → stored in **ChromaDB vector store**  
- Incident descriptions → embedded and semantically compared  
- Most relevant DGMS code → automatically assigned  

✅ *Accurate and context-aware semantic matching.*

---

### 2. Retrieval-Augmented Generation (RAG) for Q&A
Delivers **factually grounded** responses through RAG pipelines:

1. User query → contextualized  
2. Context retrieved from **MongoDB** + **ChromaDB**  
3. Fused into LLM prompt → generates reliable answers  

💡 *Data-driven, explainable responses directly from verified sources.*

---

### 3. Accident Pattern Analysis
Provides insights into:
- ⏳ **Temporal Trends**
- 🌦️ **Seasonal Correlations**
- 📍 **Geographical Hotspots**
- ⚙️ **Cause Distribution**

🧩 *Also generates preventive recommendations using historical data.*

---

### 4. Proactive Alert Generation
Monitors new incidents for:
- Repeated accidents of the same type  
- Seasonal spikes  
- Regional anomalies  

⚠️ When thresholds are exceeded, **alerts** are generated and stored for dashboards or notifications.

---

### 5. Asynchronous Multi-Agent System
All agents run concurrently via **asyncio**, offering:
- Real-time updates  
- Fault-tolerant operation  
- Scalable architecture  

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
- **MongoDB** (local or Atlas)
- `git`

### 🔧 Steps

```bash
# 1. Clone the repository
git clone https://github.com/23Tarandeep57/Mine-Safety-Analysis.git
cd Mine-Safety-Analysis

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env to include MongoDB URI, API keys, etc.

# 5. Run the Flask server
python app.py
