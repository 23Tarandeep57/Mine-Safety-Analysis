# MineGuard AI: A Multi-Agent System for Proactive Mine Safety Analysis

**An intelligent, autonomous system for monitoring, analyzing, and reporting on mine safety incidents across India to prevent future accidents.**

---

## The Problem

Mine safety is a critical issue in India, with hundreds of accidents occurring annually, leading to tragic loss of life and injury. The Directorate General of Mines Safety (DGMS) and news outlets report on these incidents, but the data is often:

- **Unstructured and Disparate**: Published as PDFs, HTML tables, and news articles with no consistent format.
- **Difficult to Aggregate**: Manually collecting and consolidating data from various sources is slow, inefficient, and prone to error.
- **Hard to Query**: There is no centralized, searchable database, making it nearly impossible to perform trend analysis or get quick answers about specific locations or incident types.

This information latency means that valuable insights that could prevent future accidents are often buried in paperwork and disconnected reports.

## Our Solution: MineGuard AI

MineGuard AI is a sophisticated, multi-agent system that automates the entire mine safety data pipeline. It transforms raw, unstructured data into a structured, queryable knowledge base and provides a natural language interface for real-time analysis.

Our system autonomously performs:
1.  **Data Ingestion**: Scrapes DGMS reports and news articles.
2.  **Intelligent Structuring**: Uses AI to parse unstructured text and PDFs into a clean, JSON-like format.
3.  **Data Enrichment**: Intelligently fills in missing information, such as mapping ambiguous incident descriptions to official DGMS cause codes using vector similarity search.
4.  **Conversational Access**: Allows stakeholders to ask complex questions in plain English via a simple API.

This turns a reactive, manual process into a proactive, data-driven approach to improving mine safety.

---

## System Architecture

MineGuard AI is built on a **multi-agent architecture**, where independent agents collaborate asynchronously through a central **Message Bus**. This design allows for a scalable and resilient system where different tasks (e.g., scraping, analysis, user interaction) run concurrently without blocking each other.




### Core Components:

1.  **Agents (`agent.py`)**: The heart of the system.
    -   `DGMSMonitorAgent` & `NewsScannerAgent`: The data collectors. They watch their respective sources and publish new findings to the message bus.
    -   `IncidentAnalysisAgent`: The data processor. It subscribes to messages from the collectors, uses AI tools to parse and enrich the data, and upserts the structured result into MongoDB.
    -   `ConversationalAgent`: The brain. It listens for user queries, performs Retrieval-Augmented Generation (RAG) by fetching context from both MongoDB and a ChromaDB vector store, and generates a comprehensive answer.

2.  **Flask API (`app.py`)**: A lightweight server that exposes the system's capabilities via a REST API, primarily the `/api/chatbot` endpoint for frontend integration.

3.  **Databases**:
    -   **MongoDB**: The primary data store for all structured incident reports.
    -   **ChromaDB**: A vector database used for semantic search and our innovative cause-code mapping.

---

## Technical Innovations & Features

### 1. AI-Powered Cause Code Mapping

A standout feature of our system is its ability to map messy, free-text descriptions of an incident (e.g., *"a worker was hit by a falling rock"*) to a precise, official DGMS cause code (e.g., *"1.1 - Fall of roof"*).

-   **How it Works**: We pre-load a ChromaDB vector store with embeddings of all official DGMS cause code descriptions. When a new incident arrives, we embed its free-text `brief_cause` and perform a similarity search against the vector store to find the most semantically relevant code. This is far more accurate than simple keyword matching.

### 2. Retrieval-Augmented Generation (RAG) for Q&A

Our chatbot doesn't just guess answers; it finds them. When a user asks a question:

1.  The query is contextualized and used to fetch relevant documents from MongoDB (for structured data) and ChromaDB (for semantic matches).
2.  This retrieved "context" is injected directly into the prompt sent to the language model.
3.  The model uses this context to synthesize a factually grounded, accurate answer, complete with details from the source documents.

### 3. Asynchronous Multi-Agent System

The use of an agent-based framework with a message bus allows for high throughput and scalability. The system can be scraping new data, analyzing an incident, and answering a user query all at the same time, without any process blocking another.

---

## Tech Stack

-   **Backend**: Python, Flask
-   **AI/ML**: LangChain, Google Generative AI (for embeddings and generation)
-   **Databases**: MongoDB (Primary), ChromaDB (Vector Store)
-   **Data Processing**: PyPDF, BeautifulSoup, Pandas
-   **Core Framework**: Custom Multi-Agent System with `asyncio`

## Setup and Installation

### Prerequisites

-   Python 3.10+
-   MongoDB instance (local or a cloud service like MongoDB Atlas)
-   `git` for cloning the repository

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Mine-Safety-Analysis