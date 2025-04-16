from duckduckgo_search import DDGS

def duckduckgo_web_search(query, max_results=1):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, region='wt-wt', safesearch='Off', max_results=max_results):
            results.append({
                "title": r["title"],
                "href": r["href"],
                "snippet": r["body"]
            })
    return results