"""
End-to-end integration test.

Test complete workflow:
1. Start HTTP server
2. Generate plan in tests/data_output/
3. Modify tasks and steps (full file replace)
4. Run stages
5. Verify output
6. Cleanup
"""

import sys
import json
import time
import shutil
import subprocess
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# use standard test output directory (git ignored)
TEST_OUTPUT_DIR = Path(__file__).parent.parent / 'data_output'

# test server port (change if port is occupied)
TEST_SERVER_PORT = 9999

TEST_HTML = """<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
    <h1>Product Title</h1>
    <div class="price">$99.99</div>
</body>
</html>"""


class TestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(TEST_HTML.encode())
    
    def log_message(self, format, *args):
        pass


def start_server(port=TEST_SERVER_PORT):
    server = HTTPServer(('localhost', port), TestHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_end_to_end():
    print("\n" + "="*60)
    print("End-to-End Test")
    print("="*60)
    
    # step 1: start server
    print("\n[1/6] Starting server...")
    server = start_server(port=TEST_SERVER_PORT)
    test_url = f"http://localhost:{TEST_SERVER_PORT}"
    time.sleep(0.5)
    print(f"✅ Server: {test_url}")
    
    # step 2: setup test directory
    print("\n[2/6] Setup...")
    plan_name = 'test_e2e'
    plan_dir = TEST_OUTPUT_DIR / plan_name
    
    # cleanup old test directory if exists
    if plan_dir.exists():
        shutil.rmtree(plan_dir, ignore_errors=True)
    
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plan_dir / f'plan_{plan_name}.py'
    steps_dir = plan_dir / f'steps_{plan_name}'
    
    # step 3: generate plan
    print("\n[3/6] Generating plan...")
    cmd = f'python -m auto_spider generate {plan_name}'
    subprocess.run(cmd, shell=True, cwd=plan_dir)
    
    assert plan_file.exists(), f"Plan file not found: {plan_file}"
    print(f"✅ Generated")
    
    # step 4: modify tasks
    print("\n[4/6] Modifying files...")
    plan_content = plan_file.read_text(encoding='utf-8')
    plan_content = plan_content.replace(
        """def initial_task():
    return [
        Task(url='https://example.com/page1'),
    ]""",
        f"""def initial_task():
    return [
        Task(url='{test_url}/page1'),
        Task(url='{test_url}/page2'),
    ]"""
    )
    plan_file.write_text(plan_content, encoding='utf-8')
    
    # step 5: replace action.py
    action_file = steps_dir / 'action.py'
    action_file.write_text("""from auto_spider import action, Context

@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    response = context.spider.do_url(url)
    
    context['content'] = response.text
    context['result'] = {'url': url, 'status': 200}
""", encoding='utf-8')
    
    # step 6: replace parse.py
    parse_file = steps_dir / 'parse.py'
    parse_file.write_text("""from auto_spider import parse, Context

@parse()
def parse_data(context: Context):
    content = context.get('content', '')
    action_result = context.get('input', {})
    
    has_title = 'Product Title' in content
    has_price = 'price' in content
    
    context['result'] = {
        'url': action_result.get('url'),
        'has_title': has_title,
        'has_price': has_price
    }
""", encoding='utf-8')
    print("✅ Files configured")
    
    # step 7: run stages using subprocess (simulate real user scenario)
    print("\n[5/6] Running stages...")
    
    # real user scenario: cd to plan directory, then run command
    print("\n--- Action Stage ---")
    result = subprocess.run(
        ['python', '-m', 'auto_spider', 'run', plan_file.name, 'fetch_page', '-s', 'action', '-w', '2'],
        cwd=plan_dir
    )
    assert result.returncode == 0, f"Action stage failed with code {result.returncode}"
    
    print("\n--- Parse Stage ---")
    result = subprocess.run(
        ['python', '-m', 'auto_spider', 'run', plan_file.name, 'parse_data', '-s', 'parse', '-w', '2'],
        cwd=plan_dir
    )
    assert result.returncode == 0, f"Parse stage failed with code {result.returncode}"
    
    print("\n✅ Executed")
    
    # step 8: verify
    print("\n[6/6] Verifying...")
    output_dir = plan_dir / 'output'
    
    action_dirs = sorted(output_dir.glob('*_action_*'))
    assert len(action_dirs) > 0, f"No action output found in {output_dir}"
    action_dir = action_dirs[-1]
    
    with open(action_dir / 'task1_action.json') as f:
        action_data = json.load(f)
        assert action_data['status'] == 200
    
    parse_dirs = sorted(output_dir.glob('*_parse_*'))
    assert len(parse_dirs) > 0, f"No parse output found in {output_dir}"
    parse_dir = parse_dirs[-1]
    
    with open(parse_dir / 'task1_parse.json') as f:
        parse_data = json.load(f)
        assert parse_data['has_title'] == True
    
    print("✅ Verified")
    
    print("\n" + "="*60)
    print("Test PASSED ✅")
    print("="*60)
    
    # cleanup
    print("\nCleaning up...")
    server.shutdown()
    shutil.rmtree(plan_dir, ignore_errors=True)
    print(f"✅ Cleaned")


if __name__ == '__main__':
    test_end_to_end()
