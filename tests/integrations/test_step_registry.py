"""
Integration test for step_registry module.

Test core registration and hot reload.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auto_spider.core.step_registry import action, parse, extract, get_step
from auto_spider.step import Context


def test_registration():
    """Test decorator registration works"""
    
    @action()
    def fetch_page(context: Context):
        return "action_executed"
    
    @parse()
    def parse_data(context: Context):
        return "parse_executed"
    
    @extract()
    def save_data(context: Context):
        return "extract_executed"
    
    # verify can get registered functions
    action_func = get_step('action', 'fetch_page')
    parse_func = get_step('parse', 'parse_data')
    extract_func = get_step('extract', 'save_data')
    
    # verify execution
    ctx = Context(spider=None, task={}, initial={})
    assert action_func(ctx) == "action_executed"
    assert parse_func(ctx) == "parse_executed"
    assert extract_func(ctx) == "extract_executed"
    
    print("✅ Registration works: @action, @parse, @extract")


def test_hot_reload():
    """Test hot reload by re-registering same function"""
    
    @action()
    def hot_reload_test(context: Context):
        return "v1"
    
    func_v1 = get_step('action', 'hot_reload_test')
    ctx = Context(spider=None, task={}, initial={})
    assert func_v1(ctx) == "v1"
    
    # re-register with new implementation
    @action()
    def hot_reload_test(context: Context):
        return "v2"
    
    func_v2 = get_step('action', 'hot_reload_test')
    assert func_v2(ctx) == "v2"
    
    print("✅ Hot reload works: v1 → v2")


if __name__ == '__main__':
    print("\n" + "="*50)
    print("Registry Integration Test")
    print("="*50 + "\n")
    
    test_registration()
    test_hot_reload()
    
    print("\n" + "="*50)
    print("All Tests Passed ✅")
    print("="*50)
