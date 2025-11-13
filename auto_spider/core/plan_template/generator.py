"""
Template generator functions.

Generate plan and step files from templates.
"""

from pathlib import Path
from string import Template

# Template file directory
_TEMPLATE_DIR = Path(__file__).parent / 'template_files'


def _load_template(filename: str, **kwargs) -> str:
    """
    Load and render template from file.
    
    Args:
        filename: Template filename
        **kwargs: Template variables
    
    Returns:
        Rendered template string
    """
    template_path = _TEMPLATE_DIR / filename
    template_content = template_path.read_text(encoding='utf-8')
    template = Template(template_content)
    return template.safe_substitute(**kwargs)


def generate_steps(name: str, description: str = None) -> Path:
    """
    Generate steps package with three modules: action, parse, extract.
    
    Args:
        name: Package name (will generate steps_{name}/)
        description: Package description
        
    Returns:
        Path to generated package directory
        
    Example:
        generate_steps('baidu', description='Baidu scraping steps')
        
    Generated structure:
        steps_{name}/
            __init__.py
            action.py
            parse.py
            extract.py
    """
    if not description:
        description = f'Steps for {name}'
    
    package_name = f'steps_{name}'
    package_path = Path(package_name)
    package_path.mkdir(exist_ok=True)
    
    # generate __init__.py
    init_path = package_path / '__init__.py'
    init_content = _load_template('step_init.py.txt', description=description)
    init_path.write_text(init_content, encoding='utf-8')
    
    # generate action.py
    action_path = package_path / 'action.py'
    action_content = _load_template('action.py.txt', description=description)
    action_path.write_text(action_content, encoding='utf-8')
    
    # generate parse.py
    parse_path = package_path / 'parse.py'
    parse_content = _load_template('parse.py.txt', description=description)
    parse_path.write_text(parse_content, encoding='utf-8')
    
    # generate extract.py
    extract_path = package_path / 'extract.py'
    extract_content = _load_template('extract.py.txt', description=description)
    extract_path.write_text(extract_content, encoding='utf-8')
    
    return package_path


def generate_plan(name: str, description: str = None, single_file: bool = False) -> Path:
    """
    Generate plan_xxx.py template file in current directory.
    
    Args:
        name: Plan name (will generate plan_{name}.py)
        description: Plan description
        single_file: Include steps inline in plan file (default: False)
        
    Returns:
        Path to generated file
        
    Example:
        # with steps package
        generate_plan('baidu', description='Fetch baidu homepage')
        
        # single file with inline steps
        generate_plan('baidu', description='Fetch baidu homepage', single_file=True)
    """
    if not description:
        description = f'Plan for {name}'
    
    filename = f'plan_{name}.py'
    output_path = Path(filename)
    
    # choose template based on mode
    if single_file:
        # inline steps mode
        content = _load_template('plan_single.py.txt', description=description, name=name)
    else:
        # separate steps package mode
        content = _load_template('plan.py.txt', description=description, name=name)
        generate_steps(name, description=f'Steps for {name}')
    
    output_path.write_text(content, encoding='utf-8')
    
    return output_path
