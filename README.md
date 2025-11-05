# 🛡️ MineGuard AI: A Multi-Agent System for Proactive Mine Safety Analysis (CyberLabs IIT-ISM)

> **An intelligent, autonomous system that transforms unstructured mine safety reports into actionable insights — enabling proactive monitoring, analysis, and prevention of mine accidents in India.**

---

## 🧭 Summary

**MineGuard AI** automates the entire mine safety intelligence pipeline — from **data collection and structuring** to **semantic enrichment, analysis, and alert generation**.  
It uses a **multi-agent architecture** with AI-driven reasoning and natural language querying to provide **real-time situational awareness** and **predictive insights** for accident prevention.

> In essence, MineGuard AI reads, understands, retrieves, and analyzes every mine accident report and generates solutions to prevent accidents — so humans can focus on saving lives, not parsing data.

---

## 🚨 Problem Statement

Mine safety remains a **critical challenge** in India, with hundreds of accidents reported every year. Despite continuous reporting by the **Directorate General of Mines Safety (DGMS)** and various media sources, the current data ecosystem faces major challenges:

- 🧾 **Unstructured & Disparate** — Reports are often published as PDFs, HTML tables, or unformatted news articles.  
- 🧩 **Difficult to Aggregate** — Manual data collection is slow, inconsistent, and error-prone.  
- 🔍 **Hard to Query** — No unified database exists for trend analysis or real-time insights.

This causes **information latency**, where critical insights that could prevent accidents are buried in fragmented reports and paperwork.

---

## 🤖 Solution: MineGuard AI

**MineGuard AI** is a **multi-agent, AI-powered system** that automates the full lifecycle of mine safety data — from ingestion to analysis and conversational access.

### Key Capabilities

1. **Data Ingestion** — Scrapes DGMS and media sources for incident data.  
2. **Intelligent Structuring** — Converts unstructured text/PDFs into structured JSON format.  
3. **Data Enrichment** — Maps missing or vague entries to official DGMS codes using semantic AI.  
4. **Conversational Querying** — Enables natural-language interaction for summaries, trends, and Q&A.  
5. **Accident Pattern Analysis** — Identifies seasonal, temporal, and geographical trends.  
6. **Proactive Alerts** — Detects anomalies and generates safety warnings.

This transforms a **reactive** manual process into a **proactive**, AI-powered safety intelligence ecosystem.

---

## 🧠 System Architecture

MineGuard AI follows a **multi-agent architecture**, where specialized agents communicate asynchronously through a **Message Bus**, coordinated by the **IncidentAnalysisAgent**.

### ⚙️ Core Components

| Component | Description |
|------------|-------------|
| 🕵️‍♂️ **DGMSMonitorAgent** | Scrapes and monitors DGMS official reports. |
| ⚙️ **NewsScannerAgent** | Extracts incident data from verified media and government sources. |
| 🧩 **IncidentAnalysisAgent** | Parses, enriches, and analyzes incidents; acts as the control center. |
| 💬 **ConversationalAgent** | Handles natural language queries using Retrieval-Augmented Generation (RAG). |
| 📊 **AccidentAnalysisModule** | Performs statistical and temporal trend analysis. |
| 🚨 **AlertGenerator** | Detects high-risk patterns and issues alerts. |
| 🗃️ **MongoDB** | Stores structured incident data. |
| 🧠 **ChromaDB** | Stores vector embeddings for semantic retrieval and cause mapping. |

All agents communicate using the **A2A (Agent-to-Agent)** protocol, enabling modular scalability and asynchronous execution.

---

## ⚡ Technical Highlights

### 1. AI-Powered Cause Code Mapping

Automatically maps free-text causes like  
> “Landslide” to the official DGMS code  
> **0118 — Landslide**

**How it Works**
- DGMS cause-code descriptions → stored as embeddings in **ChromaDB**  
- Incident cause text → converted into vector embeddings  
- Semantic similarity → retrieves and assigns most relevant DGMS code  

✅ *Context-aware, consistent, and automatic classification.*

---

### 2. Retrieval-Augmented Generation (RAG)

Provides **factually grounded** Q&A through RAG pipelines:

1. User query → contextualized by the **ConversationalAgent**  
2. Relevant context → retrieved from **MongoDB** + **ChromaDB**  
3. Context + Query → fused into an **LLM prompt**  
4. Model → generates grounded, verifiable responses  

💡 *Ensures explainable, data-backed responses directly from verified records.*

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

| **Architecture** | Custom Asynchronous Multi-Agent System |

---

## 🚀 Setup & Installation

### 🧱 Prerequisites

- Python **3.10+**  
- **MongoDB** (Local or MongoDB Atlas)  
- `git` installed

---

### 🔧 Steps to Run

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
