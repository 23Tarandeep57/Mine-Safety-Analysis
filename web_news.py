from tavily import TavilyClient
from bs4 import BeautifulSoup
import requests
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import time


load_dotenv()
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")


client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def tavily_search(query, max_results=10):
    """Perform a Tavily search with fallback handling."""
    try:
        response = client.search(
            query=query,
            time_range="month",
            max_results=max_results,
            include_raw_content=False
        )
        return response.get("results", [])
    except Exception as e:
        print(f"Tavily API Error: {e}")
        return []


def fetch_article_text(url):
    """Fetch article content and extract readable text."""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""


    if "facebook.com" in url or len(r.text) < 2000:
        print("Skipping non-article or short page:", url)
        return ""
    
    soup = BeautifulSoup(r.text, "html.parser")
    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text(strip=True) for p in paragraphs)
    return text if len(text) > 500 else ""

def summarize_text(article_text):
    """Summarize an article into key bullet points."""
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


def is_duplicate_article_llm(new_article, existing_articles):
    """
    Use an LLM to check if a new article describes the same event
    as any existing article. Returns True if duplicate.
    """
    if not existing_articles:
        return False
    llm = ChatGroq(
        api_key=os.environ["GROQ_API_KEY"],
        model="llama-3.3-70b-versatile",
        temperature=0
    )
    for existing in existing_articles:
        prompt = PromptTemplate(
            input_variables=["title1", "summary1", "title2", "summary2"],
            template=(
                "You are an expert news analyst.\n"
                "Determine whether the two news reports below describe the SAME real-world event.\n\n"
                "Article 1:\nTitle: {title1}\n\n"
                "Article 2:\nTitle: {title2}\n\n"
                "Answer strictly with one word: 'YES' if they are about the same incident, otherwise 'NO'."
            )
        )
        formatted = prompt.format(
            title1=new_article["title"],
            summary1=new_article.get("summary", ""),
            title2=existing["title"],
            summary2=existing.get("summary", "")
        )
        response = llm.invoke(formatted)
        answer = response.content.strip().upper() if hasattr(response, "content") else str(response).strip().upper()
        if "YES" in answer:
            print(f"🤖 LLM detected duplicate between:\n - '{new_article['title']}'\n - '{existing['title']}'")
            return True

    return False


def get_valid_articles(query, desired_count=5):
    """Fetch and summarize valid, unique news articles."""
    all_results = []
    seen_urls = set()
    attempts = 0

    while len(all_results) < desired_count and attempts < 5:
        attempts += 1
        print(f"\n🔎 Tavily search attempt {attempts} for: {query}")

        results = tavily_search(query, max_results=10)
        if not results:
            print("No results returned by Tavily.")
            break

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
                print("Skipping — no valid article text found.")
                continue

            summary = summarize_text(article_text)
            candidate = {
                "title": title,
                "date": date,
                "url": url,
                "summary": summary
            }
            if is_duplicate_article_llm(candidate, all_results):
                print("Duplicate detected — skipping this article.")
                continue

            all_results.append(candidate)
            print(f" Added valid article ({len(all_results)}/{desired_count})")

            if len(all_results) >= desired_count:
                break

        time.sleep(2)

    return all_results

def analyze_common_patterns(articles):
    """Analyze recurring themes and causes across summarized articles."""
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


if __name__ == "__main__":
    final_articles = get_valid_articles("recent coal mining accidents in India", desired_count=5)

    print("\n\n---Final Summaries ---\n")
    for i, a in enumerate(final_articles, 1):
        print(f"{i}. 📰 {a['title']}")
        print(f"   📅 {a['date']}")
        print(f"   🔗 {a['url']}")
        print(f"   🧾 Summary:\n{a['summary']}\n")
        print("-" * 90)

   
    pattern_analysis = analyze_common_patterns(final_articles)
    print("\n\n--- 🔍 COMMON PATTERN ANALYSIS ---\n")
    print(pattern_analysis)
    print("\n" + "=" * 100)



 