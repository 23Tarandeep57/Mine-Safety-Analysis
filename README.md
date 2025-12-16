# 🛡️ MineGuard AI: A Multi-Agent System for Proactive Mine Safety Analysis (CyberLabs IIT-ISM)

> **An intelligent, autonomous system that transforms unstructured mine safety reports into actionable insights — enabling proactive monitoring, analysis, and prevention of mine accidents in India.**

---

## 🎥 Demo: Workings of Chatbot in Backend

https://github.com/user-attachments/assets/a9042710-895c-4cb3-8a0e-6bf1fc35e954

---

## 🧭 Summary (In Brief)

**MineGuard AI** automates the entire mine safety intelligence pipeline — from **data collection and structuring** to **semantic enrichment, analysis, and alert generation**.  
It uses a **multi-agent architecture** with AI-driven reasoning and natural language querying to provide **real-time situational awareness** and **predictive insights** for accident prevention.

**In essence:**  
> MineGuard AI reads, understands, retrieve and analyzes every mine accident report and generate solutions to prevent accidents — so humans can focus on saving lives, not parsing data.

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

1. **Data Ingestion** — Scrapes DGMS and news reports.  
2. **Intelligent Structuring** — Converts unstructured text/PDFs into structured JSON data.  
3. **Data Enrichment** — Maps missing or vague entries to official DGMS codes using AI-powered semantic matching.  
4. **Conversational Querying** — Enables natural-language interaction for trend analysis, summaries, and Q&A.  
5. **Accident Pattern Analysis** — Uses historical data to analyze seasonal, temporal, and geographical trends.  
6. **Proactive Alert Generation** — Monitors new reports to generate early alerts for high-risk patterns.  

This transforms a **reactive** manual process into a **proactive**, AI-powered safety intelligence ecosystem.

---

## 🧠 System Architecture

MineGuard AI follows a **multi-agent architecture**, where specialized agents communicate asynchronously through a **Message Bus**, coordinated by the **IncidentAnalysisAgent**.

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

| **Architecture** | Custom Asynchronous Multi-Agent System |

---

## 🚀 Setup & Installation

### 🐳 Option 1: Docker (Recommended)

The easiest way to run the entire stack with all dependencies:

```bash
# 1. Clone the repository
git clone https://github.com/23Tarandeep57/Mine-Safety-Analysis.git
cd Mine-Safety-Analysis

# 2. Configure environment variables
cp .env.example .env
# Edit .env and add your API keys:
# - GROQ_API_KEY (Required for LLM)
# - GOOGLE_API_KEY (Required for Embeddings)
# - TAVILY_API_KEY (Optional, for web search)

# 3. Start all services
docker-compose up --build

# 4. Access the application
# Frontend:  http://localhost:5173
# API:       http://localhost:5001
# MongoDB:   localhost:27017
# Redis:     localhost:6379
```

**Docker Services:**
| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 5173 | React web interface |
| `flask` | 5001 | REST API server |
| `agent` | - | Multi-agent background worker |
| `redis` | 6379 | Message queue & pub/sub |
| `mongo` | 27017 | Incident database |

**Useful Docker Commands:**
```bash
# Stop all services
docker-compose down

# View logs
docker-compose logs -f flask agent

# Rebuild after code changes
docker-compose up --build

# Reset databases (WARNING: deletes data)
docker-compose down -v
```

---

### 🔧 Option 2: Manual Setup (Development)

#### Prerequisites

- Python **3.11+** (Recommended: 3.12)
- **Node.js 18+**
- **MongoDB** (Local or MongoDB Atlas)
- **Redis** (Local or Redis Cloud)
- `git` installed

#### Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/23Tarandeep57/Mine-Safety-Analysis.git
cd Mine-Safety-Analysis

# 2. Create and activate virtual environment
python3.12 -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env to include MongoDB URI, Redis URL, and API keys (GROQ, GOOGLE, TAVILY)

# 5. Start Redis (if not running)
# You can use Docker for dependencies:
docker-compose up -d redis mongo

# 6. Run the Flask API server (Terminal 1)
python app.py

# 7. Run the Multi-Agent System (Terminal 2)
python agent.py
```

---

## 🖥️ Frontend Setup

The web interface is built with **React + Vite** and provides:
- 💬 **AI Chatbot** with real-time streaming responses
- 📊 **Incident Analysis Dashboard** with YoY trends
- 🚨 **Safety Alerts Viewer** with severity indicators

### 📋 Prerequisites

- **Node.js 18+** (Download: https://nodejs.org/)
- **npm** or **yarn**

### 🔧 Frontend Installation

```bash
# 1. Navigate to frontend directory
cd Front-end/MSA

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

The frontend will start at: **http://localhost:5173**

### 🌐 API Configuration

The frontend connects to the Flask backend at `http://127.0.0.1:5001/api`.  
If your backend runs on a different port, update the API URL in:

```
Front-end/MSA/src/utils/chatApi.js
```

### 📦 Build for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build locally
npm run preview
```

### 🔄 Running the Full Stack

Open **3 terminals** and run:

| Terminal | Command | Purpose |
|----------|---------|---------|
| **Terminal 1** | `python app.py` | Flask API Server (port 5001) |
| **Terminal 2** | `python agent.py` | Multi-Agent System |
| **Terminal 3** | `cd Front-end/MSA && npm run dev` | React Frontend (port 5173) |

Then open **http://localhost:5173** in your browser.
