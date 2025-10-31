from tavily import TavilyClient
from bs4 import BeautifulSoup
import requests
import os
import json
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# --- Load environment variables ---
load_dotenv()
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# --- Initialize Tavily client ---
client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


# --- Tavily search ---
def tavily_search(query, max_results=20):
    try:
        response = client.search(
            query=query,
            time_range="month",
            max_results=max_results,
            include_raw_content=False
        )
        return response.get("results", [])
    except Exception as e:
        print(f"❌ Tavily API Error: {e}")
        return []


# --- Fetch article content ---
def fetch_article_text(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return ""

    if "facebook.com" in url or len(r.text) < 2000:
        print("⚠️ Skipping non-article or short page:", url)
        return ""

    soup = BeautifulSoup(r.text, "html.parser")
    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text(strip=True) for p in paragraphs)
    return text if len(text) > 500 else ""


# --- Summarize article ---
def summarize_text(article_text):
    if not article_text:
        return "No article content found."

    llm = ChatGroq(
        api_key=os.environ["GROQ_API_KEY"],
        model="llama-3.3-70b-versatile",
        temperature=0.7
    )

    prompt = PromptTemplate(
        input_variables=["content"],
        template=(
            "Summarize the following news article in 3–5 concise bullet points. "
            "Focus on key details — who, what, when, where, and why.\n\n"
            "Article:\n{content}"
        )
    )

    formatted_prompt = prompt.format(content=article_text[:4000])
    response = llm.invoke(formatted_prompt)
    return response.content.strip() if hasattr(response, "content") else str(response).strip()


# --- Get ALL articles (without deduplication) ---
def get_all_articles(query, total_attempts=3, batch_size=10):
    all_articles = []
    seen_urls = set()

    for attempt in range(1, total_attempts + 1):
        print(f"\n🔎 Tavily search attempt {attempt}/{total_attempts} for: {query}")
        results = tavily_search(query, max_results=batch_size)
        if not results:
            print("⚠️ No results returned.")
            continue

        for result in results:
            url = result.get("url")
            title = result.get("title")
            date = result.get("published_date", "Unknown")

            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            print(f"\n📰 Fetching: {title}")
            print(f"   🔗 URL: {url}")

            article_text = fetch_article_text(url)
            if not article_text:
                print("⚠️ Skipping — no valid article text found.")
                continue

            summary = summarize_text(article_text)

            all_articles.append({
                "title": title,
                "date": date,
                "url": url,
                "summary": summary
            })

            print(f"✅ Added article ({len(all_articles)})")

        time.sleep(2)

    return all_articles


# --- Remove duplicate articles AFTER search ---
def remove_duplicate_articles(articles, threshold=0.65):
    if not articles:
        return []

    summaries = [a["summary"] for a in articles]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(summaries)
    similarity_matrix = cosine_similarity(tfidf_matrix)

    unique_indices = []
    for i in range(len(summaries)):
        if not any(similarity_matrix[i][j] > threshold for j in unique_indices):
            unique_indices.append(i)

    unique_articles = [articles[i] for i in unique_indices]
    print(f"\n🧹 Filtered {len(articles) - len(unique_articles)} duplicates. Kept {len(unique_articles)} unique articles.")
    return unique_articles


# --- Analyze common patterns across summaries ---
def analyze_common_patterns(articles):
    if not articles:
        return "No summaries available for analysis."

    combined_summaries = "\n\n".join(
        [f"{i+1}. {a['summary']}" for i, a in enumerate(articles)]
    )

    llm = ChatGroq(
        api_key=os.environ["GROQ_API_KEY"],
        model="llama-3.3-70b-versatile",
        temperature=0.3
    )

    prompt = PromptTemplate(
        input_variables=["summaries"],
        template=(
            "You are a safety analysis expert specializing in mining incidents.\n"
            "Analyze the following summarized news reports about recent coal mine accidents in India.\n\n"
            "Identify and explain the **common patterns or recurring themes**, focusing on:\n"
            "- Type or cause of accident (blast, collapse, machinery failure, etc.)\n"
            "- Location patterns (states, open-cast vs underground)\n"
            "- Human or equipment-related issues\n"
            "- Negligence or regulatory gaps\n"
            "- Prevention recommendations.\n\n"
            "Summaries:\n{summaries}\n\n"
            "Now produce a structured analysis report in 5–7 bullet points."
        )
    )

    formatted_prompt = prompt.format(summaries=combined_summaries)
    response = llm.invoke(formatted_prompt)
    return response.content.strip() if hasattr(response, "content") else str(response).strip()


# --- Run ---
all_articles = get_all_articles("recent coal mining accidents in India", total_attempts=3, batch_size=10)

print(f"\n📄 Total articles fetched: {len(all_articles)}")

# ✅ Deduplicate after the search
unique_articles = remove_duplicate_articles(all_articles, threshold=0.65)

# Save to file
if unique_articles:
    with open("unique_articles.json", "w", encoding="utf-8") as f:
        json.dump(unique_articles, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved {len(unique_articles)} unique articles to 'unique_articles.json'")

print("\n\n--- 🧠 Final Unique Summaries ---\n")
for i, a in enumerate(unique_articles, 1):
    print(f"{i}. 📰 {a['title']}")
    print(f"   📅 {a['date']}")
    print(f"   🔗 {a['url']}")
    print(f"   🧾 Summary:\n{a['summary']}\n")
    print("-" * 90)

# --- Pattern analysis ---
pattern_analysis = analyze_common_patterns(unique_articles)

print("\n\n--- 🔍 COMMON PATTERN ANALYSIS ---\n")
print(pattern_analysis)
print("\n" + "=" * 100)
