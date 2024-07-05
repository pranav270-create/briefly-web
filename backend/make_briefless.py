import os, time, asyncio, requests
from pydantic import BaseModel
from typing import Optional, List, Tuple
import anthropic
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import concurrent.futures

from make_briefly import anthropic_cost

DEBUG = 1

class SearchResult(BaseModel):
    title: str
    href: str
    body: Optional[str]


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-images")
    chrome_options.page_load_strategy = 'eager'
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def scrape_url(url, timeout=10):
    """
    grab 1 html page
    """
    driver = setup_driver()
    try:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        
        # Wait for the body to be present
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        return driver.page_source
    except (TimeoutException, WebDriverException) as e:
        print(f"Error scraping {url}: {str(e)}")
        return None
    finally:
        driver.quit()


def scrape_urls(urls, max_workers=5):
    """
    selenium scraper to download html pages
    """
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                html = future.result()
                if html:
                    results[url] = html
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
    return results


def generate_search_query(client: anthropic.Anthropic, summary: str) -> Tuple[str, float]:
    """
    snippet of text from a newsletter -> google search query
    """
    prompt = f"""
    Based on this snippet of news, generate a very concise Google search query to find more information
    <snippet>
    {summary}
    </snippet>"""
    response = client.messages.create(
        messages=[{"role":"user", "content": prompt}, {"role":"assistant", "content": "<search_query>"}],
        stop_sequences=["</search_query>"], 
        max_tokens=64, 
        temperature=0.0,
        model="claude-3-5-sonnet-20240620"
    )
    cost = anthropic_cost(response.usage)
    return response.content[0].text.strip(), cost


async def async_google_search(session, query: str, num_results=10) -> Optional[List[SearchResult]]:
    """
    google search api
    num_results max is 10
    """
    api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
    cse_id = os.environ.get("GOOGLE_SEARCH_CSE_ID")

    if not api_key or not cse_id:
        raise ValueError("GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CSE_ID must be set")

    search_url = "https://www.googleapis.com/customsearch/v1/"
    params = {
        'q': query,
        'key': api_key,
        'cx': cse_id,
        'num': num_results,
    }

    async def fetch_results():
        async with session.get(search_url, params=params) as response:
            if response.status == 200:
                search_results = await response.json()
                items = search_results.get('items', [])
                results = [SearchResult(title=item['title'], href=item['link'], body=item.get('snippet', '')) for item in items]
                return results if results else []
            elif response.status == 400:
                error_content = await response.text()
                print(f"Error 400: Bad Request. Content: {error_content}", flush=True)
                return []
            else:
                print(f"Error: {response.status}")
                return []

    results = await fetch_results()
    if not results:
        print("Retrying search due to empty results...", flush=True)
        results = await fetch_results()

    return results


def extract_text_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    # Get text
    text = soup.get_text()
    # Break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text


def summarize_search_results(client, original_summary: str, search_results: List[str]) -> Tuple[str, float]:
    """
    10 pages of cleaned html -> summary
    """
    research = ''.join([f"\nPage {i+1}:\n" + s for i, s in enumerate(search_results)])
    prompt = f"""
    After reading a small news segment, I have conducted additional research on the topic. 
    Synethize the research into a comprehensive summary that provides detailed insight on the news segment.

    <news_segment>
    {original_summary}
    </news_segment>

    <research>
    {search_results}
    </research>"""
    
    response = client.messages.create(
        messages=[{"role":"user", "content": prompt}, {"role":"assistant", "content": "<comprehensive_summary>"}],
        stop_sequences=["</comprehensive_summary>"], 
        max_tokens=64, 
        temperature=0.0,
        model="claude-3-5-sonnet-20240620"
    )
    cost = anthropic_cost(response.usage)
    return response.completion.strip(), cost


async def generate_news_summary(email_summary: str):
    """
    given some information on a topic, go to the web and get more information for the user
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    if DEBUG >= 1:
        print(f"Generating Search Query")
    search_query, cost = generate_search_query(client, email_summary)
    if DEBUG >= 1:
        print(f"Search Query: {search_query}")
        print(f"Searching Google")
    search_results: List[SearchResult] = await async_google_search(query=search_query)
    if DEBUG >= 1:
        print(f"Scraping Web")
    web_pages = scrape_urls(urls=[s.href for s in search_results])
    search_results_text = [extract_text_from_html(web_page) for web_page in web_pages]
    if DEBUG >= 1:
        print(f"Summarizing Search Results")
    final_summary, cost2 = summarize_search_results(client, email_summary, search_results_text)
    print(f"Total Cost: {cost + cost2}")
    return final_summary


def generate_calendar_event_details(request):
    content = f"""
    Event: {request.summary}
    When: {request.start} - {request.end}
    Where: {request.location or 'No location specified'}
    Organizer: {request.organizer}
    Attendees: {', '.join(request.attendees)}

    Description:
    {request.description}

    Context:
    {request.context}
    """.strip()
    return content


if __name__ == "__main__":
    sample_summary = "SpaceX launches new satellite constellation for global internet coverage"
    detailed_summary = asyncio.run(generate_news_summary(sample_summary))
    print(detailed_summary)