"""
Playwright Spider - Two Common Patterns
"""

from auto_spider import action, Context


# ── Pattern 1: Capture API requests during page load ──

@action()
def fetch_with_intercept(context: Context):
    """Navigate to page and capture API responses triggered during load."""
    url = context.task.get('url')
    api_pattern = context.task.get('api_pattern', '**/api/**')

    page = context.spider.get_driver()
    captured = []

    def on_response(response):
        if api_pattern.replace('**/', '').replace('/**', '') in response.url:
            captured.append({
                'url': response.url,
                'status': response.status,
                'body': response.text(),
            })

    page.on('response', on_response)

    # navigate - all responses during load will be captured
    content = context.spider.do_url(url, wait_until='networkidle')

    page.remove_listener('response', on_response)

    context['content'] = content
    context['result'] = {
        'captured_responses': captured,
    }


# ── Pattern 1b: Wait for a specific API response ──

@action()
def fetch_wait_for_api(context: Context):
    """Navigate and wait for a specific API call to complete."""
    url = context.task.get('url')
    api_url_keyword = context.task.get('api_url_keyword')

    page = context.spider.get_driver()

    with page.expect_response(lambda r: api_url_keyword in r.url) as response_info:
        context.spider.do_url(url)

    api_response = response_info.value
    api_data = api_response.json()

    context['content'] = page.content()
    context['result'] = {
        'api_data': api_data,
        'api_url': api_response.url,
        'status': api_response.status,
    }


# ── Pattern 2a: Make API request via JS fetch (uses browser cookies) ──

@action()
def fetch_api_via_js(context: Context):
    """Open page first, then call API using browser's cookies via JS evaluate."""
    page_url = context.task.get('page_url')
    api_url = context.task.get('api_url')
    api_params = context.task.get('api_params', {})

    page = context.spider.get_driver()

    # open page to establish session/cookies
    context.spider.do_url(page_url)

    # build query string
    qs = '&'.join(f'{k}={v}' for k, v in api_params.items())
    full_url = f'{api_url}?{qs}' if qs else api_url

    # fetch in browser context - cookies are automatically included
    api_data = page.evaluate(f"""
        async () => {{
            const res = await fetch('{full_url}', {{
                credentials: 'include'
            }});
            return res.json();
        }}
    """)

    context['content'] = str(api_data)
    context['result'] = {'api_data': api_data}


# ── Pattern 2b: Make API request via Playwright context.request (uses browser cookies) ──

@action()
def fetch_api_via_context_request(context: Context):
    """Open page first, then use page.context.request to call API."""
    page_url = context.task.get('page_url')
    api_url = context.task.get('api_url')
    post_body = context.task.get('post_body', {})

    page = context.spider.get_driver()

    # open page to establish session/cookies
    context.spider.do_url(page_url)

    # use browser context request - same cookies/session as the open page
    api_response = page.context.request.post(
        api_url,
        data=post_body,
    )

    api_data = api_response.json()

    context['content'] = str(api_data)
    context['result'] = {
        'api_data': api_data,
        'status': api_response.status,
    }
