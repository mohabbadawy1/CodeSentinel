import requests
from bs4 import BeautifulSoup
from crewai.tools import tool


@tool("CVE Scraper")
def scrape_cves(technology: str) -> str:
    """
    Scrape GitHub Security Advisories for CVEs related to a given technology or package.
    Input: technology name e.g. 'python requests' or 'flask'
    """
    try:
        url = f"https://github.com/advisories?query={technology}&ecosystem=pip"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; CodeSentinel/1.0)"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        advisories = []
        for item in soup.select(".Box-row")[:8]:
            title_el = item.select_one("h3, .f4, a[href*='/advisories/']")
            severity_el = item.select_one("[class*='Label'], [class*='severity']")
            title = title_el.get_text(strip=True) if title_el else "Unknown"
            severity = severity_el.get_text(strip=True) if severity_el else "UNKNOWN"
            advisories.append(f"- [{severity}] {title}")

        if not advisories:
            return f"No CVEs found for '{technology}' on GitHub Advisories."

        return f"CVEs found for '{technology}':\n" + "\n".join(advisories)

    except Exception as e:
        return f"CVE scraping failed: {str(e)}"


@tool("ArXiv Scraper")
def scrape_arxiv(topic: str) -> str:
    """
    Scrape arXiv for recent security research papers related to a topic.
    Input: topic e.g. 'python code security' or 'sql injection detection'
    """
    try:
        query = topic.replace(" ", "+")
        url = f"https://arxiv.org/search/?searchtype=all&query={query}+security&start=0"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; CodeSentinel/1.0)"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        papers = []
        for result in soup.select(".arxiv-result")[:5]:
            title_el = result.select_one(".title")
            abstract_el = result.select_one(".abstract-short")
            if title_el:
                title = title_el.get_text(strip=True).replace("Title:", "").strip()
                abstract = ""
                if abstract_el:
                    abstract = abstract_el.get_text(strip=True)[:200]
                papers.append(f"- {title}\n  {abstract}")

        if not papers:
            return f"No arXiv papers found for '{topic}'."

        return f"Recent security papers related to '{topic}':\n" + "\n".join(papers)

    except Exception as e:
        return f"arXiv scraping failed: {str(e)}"
