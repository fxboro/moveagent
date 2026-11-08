"""Allowlisted official-source reachability checks, never simulated recognition."""
import httpx

SOURCES = {
    'anabin': 'https://anabin.kmk.org/',
    'zab': 'https://zab.kmk.org/en/',
    'migration': 'https://www.make-it-in-germany.com/en/',
}

def query_anabin_on_demand(institution_name: str, source: str = 'anabin') -> dict:
    url = SOURCES[source]
    result = dict(institution_name=institution_name, source=source, source_url=url,
                  status='manual_review', verified=False,
                  note='Institution-specific recognition and migration eligibility require manual verification at the official source.')
    try:
        with httpx.Client(timeout=8, follow_redirects=False) as client:
            response = client.get(url, headers={'User-Agent': 'CommanderResearch/1.0'})
        result['note'] = f'Official portal HTTP {response.status_code}. ' + result['note']
        if response.status_code >= 400:
            result['status'] = 'unavailable'
    except httpx.HTTPError:
        result['status'] = 'unavailable'
        result['note'] = 'Portal could not be reached. ' + result['note']
    return result
