#!/usr/bin/env python
"""
Enhanced documentation generator for AIvidence project.
Features:
- Responsive left sidebar with collapsible tree navigation showing only packages and classes
- Code highlighting
- Better visual styling
- Parameter tables
- Search functionality
- Classes display only their own methods 

To execute: python gen_docs.py
"""

import os
import sys
import inspect
import importlib
import importlib.util
import re
from datetime import datetime

def import_module_from_file(module_name, file_path):
    """Import a module from a file path."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error importing {module_name}: {e}")
        return None

def format_docstring(docstring):
    """Format a docstring to HTML with improved styling."""
    if not docstring:
        return "<p><em>No documentation available.</em></p>"
    
    # Extract parameters section
    params_match = re.search(r'(Args|Parameters):(.*?)(?:Returns:|Raises:|Examples:|Example:|$)', 
                           docstring, re.DOTALL)
    
    returns_match = re.search(r'Returns:(.*?)(?:Raises:|Examples:|Example:|$)', 
                            docstring, re.DOTALL)
    
    # Basic cleaning
    docstring = docstring.strip()
    
    # Create the parameter table if parameters are found
    params_html = ""
    if params_match:
        params_section = params_match.group(2).strip()
        param_lines = [line.strip() for line in params_section.split('\n') if line.strip()]
        
        if param_lines:
            params_html = """
            <div class="param-table">
                <h4>Parameters</h4>
                <table>
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            current_param = None
            current_desc = []
            
            for line in param_lines:
                param_match = re.match(r'^(\w+)(?:\s*\([\w\s,]+\))?\s*:\s*(.*)$', line)
                
                if param_match:
                    # Save previous parameter if exists
                    if current_param:
                        params_html += f"""
                        <tr>
                            <td><code>{current_param}</code></td>
                            <td>{"<br>".join(current_desc)}</td>
                        </tr>
                        """
                    
                    # Start new parameter
                    current_param = param_match.group(1)
                    current_desc = [param_match.group(2)]
                elif current_param:
                    # Continue previous parameter description
                    current_desc.append(line)
            
            # Add the last parameter
            if current_param:
                params_html += f"""
                <tr>
                    <td><code>{current_param}</code></td>
                    <td>{"<br>".join(current_desc)}</td>
                </tr>
                """
            
            params_html += """
                    </tbody>
                </table>
            </div>
            """
    
    # Format returns section
    returns_html = ""
    if returns_match:
        returns_text = returns_match.group(1).strip()
        if returns_text:
            returns_html = f"""
            <div class="returns">
                <h4>Returns</h4>
                <p>{returns_text}</p>
            </div>
            """
    
    # Remove parameter and returns sections from the main description
    main_desc = docstring
    if params_match:
        main_desc = main_desc.replace(params_match.group(0), '')
    if returns_match:
        main_desc = main_desc.replace(returns_match.group(0), '')
    
    # Format examples
    examples_match = re.search(r'(Examples?:.*?)$', main_desc, re.DOTALL)
    examples_html = ""
    
    if examples_match:
        examples_text = examples_match.group(1)
        main_desc = main_desc.replace(examples_text, '')
        
        examples_text = examples_text.replace('Examples:', '').replace('Example:', '').strip()
        if examples_text:
            examples_html = f"""
            <div class="examples">
                <h4>Examples</h4>
                <pre class="code-example"><code>{examples_text}</code></pre>
            </div>
            """
    
    # Format the main description
    main_desc = main_desc.strip()
    main_desc_html = f"<div class='description'>{main_desc}</div>" if main_desc else ""
    
    return f"{main_desc_html}{params_html}{returns_html}{examples_html}"

def get_classes_from_module(module_path, full_module_name):
    """Extract only the classes from a module."""
    module = import_module_from_file(full_module_name, module_path)
    if not module:
        return []
        
    classes = []
    for class_name, cls in inspect.getmembers(module, inspect.isclass):
        # Skip private classes and those not defined in this module
        if class_name.startswith('_') or cls.__module__ != full_module_name:
            continue
        classes.append((class_name, cls))
    
    # Sort classes alphabetically for consistent display
    classes.sort(key=lambda x: x[0])
    return classes

def generate_package_tree(package_root):
    """Generate a tree of packages and their classes for the sidebar."""
    tree = {}
    
    # Define the order of packages to display
    package_order = ['core', 'agents', 'clients', 'models']
    
    for package in package_order:
        package_path = os.path.join(package_root, package)
        if not os.path.isdir(package_path):
            continue
            
        tree[package] = {}
        
        # Sort files alphabetically within each package for consistent display
        files = sorted([f for f in os.listdir(package_path) 
                      if f.endswith('.py') and not f.startswith('__')])
        
        for file in files:
            module_path = os.path.join(package_path, file)
            module_name = os.path.splitext(file)[0]
            full_module_name = f"aividence.{package}.{module_name}"
            
            # Get classes from this module
            classes = get_classes_from_module(module_path, full_module_name)
            for class_name, _ in classes:
                tree[package][class_name] = f"{package}_{module_name}_{class_name}"
    
    return tree

def generate_sidebar_html(tree):
    """Generate HTML for the sidebar showing packages and classes."""
    html = "<ul class='tree'>"
    
    for package, classes in tree.items():
        # Only show packages with classes
        if not classes:
            continue
            
        html += f"""
        <li class="folder">
            <span class="folder-name"><i class="fas fa-folder"></i> {package}</span>
            <ul class="tree">
        """
        
        for class_name, target_id in sorted(classes.items()):
            html += f"""
            <li class="class-item">
                <a href="#{target_id}" class="class-link" data-target="{target_id}">
                    <i class="fas fa-cube"></i> {class_name}
                </a>
            </li>
            """
        
        html += """
            </ul>
        </li>
        """
    
    html += "</ul>"
    return html

def generate_html_doc():
    """Generate HTML documentation for AIvidence project."""
    # Find the aividence package
    current_dir = os.getcwd()
    
    # Check if we're in AIvidence or aividence directory
    if os.path.basename(current_dir).lower() == 'aividence':
        if os.path.isdir(os.path.join(current_dir, 'aividence')):
            # We're in project root and it contains aividence
            project_root = current_dir
            package_root = os.path.join(current_dir, 'aividence')
        else:
            # We're in the package directory
            project_root = os.path.dirname(current_dir)
            package_root = current_dir
    else:
        # Assume we're in the project root
        project_root = current_dir
        package_root = os.path.join(current_dir, 'aividence')
    
    if not os.path.isdir(package_root):
        print(f"Error: Could not find aividence package at {package_root}")
        sys.exit(1)
    
    print(f"Found AIvidence package at: {package_root}")
    print(f"Project root: {project_root}")
    
    # Add project root to sys.path
    if project_root not in sys.path:
        sys.modules['aividence'] = type('aividence', (), {})
        sys.path.insert(0, project_root)
        print("Added project root to sys.path")
    
    # Create output directory
    output_dir = os.path.join(project_root, 'docs')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'documentation.html')
    
    # Get package tree with classes for sidebar
    package_tree = generate_package_tree(package_root)
    
    # Define module structure with desired ordering (core and agents first)
    module_structure = {
        'core': [
            'fact_check_engine.py'
        ],
        'agents': [
            'domain_analyzer.py',
            'claim_extractor.py',
            'claim_verifier.py'
        ],
        'clients': [
            'content_scraper.py',
            'model_client.py',
            'web_search_client.py'
        ],
        'models': [
            'fact_claim.py',
            'search_result.py',
            'fact_check_result.py',
            'content_analysis_report.py'
        ]
    }
    
    # Start HTML content
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AIvidence Documentation</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
        <style>
            :root {{
                --primary-color: #800000;
                --primary-dark: #600000;
                --primary-light: #a50000;
                --secondary-color: #006400;
                --text-color: #333;
                --light-bg: #f9f9f9;
                --border-color: #ddd;
                --hover-color: #f0f0f0;
                --code-bg: #f5f5f5;
                --sidebar-width: 280px;
            }}
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: var(--text-color);
                display: flex;
                min-height: 100vh;
                background-color: #fff;
            }}
            
            /* Sidebar */
            .sidebar {{
                width: var(--sidebar-width);
                background-color: #f0f0f0;
                height: 100vh;
                position: fixed;
                overflow-y: auto;
                border-right: 1px solid var(--border-color);
                padding: 20px 0;
                box-shadow: 2px 0 5px rgba(0,0,0,0.1);
                z-index: 100;
            }}
            
            .sidebar-header {{
                background-color: var(--primary-color);
                color: white;
                padding: 15px;
                text-align: center;
                font-size: 1.2em;
                font-weight: bold;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            
            .sidebar-content {{
                padding: 15px;
            }}
            
            .search-bar {{
                margin-bottom: 20px;
                position: relative;
            }}
            
            .search-bar input {{
                width: 100%;
                padding: 10px;
                padding-left: 30px;
                border: 1px solid var(--border-color);
                border-radius: 4px;
                font-size: 14px;
            }}
            
            .search-bar .search-icon {{
                position: absolute;
                left: 10px;
                top: 12px;
                color: #888;
            }}
            
            /* Tree View */
            .tree {{
                list-style-type: none;
                padding-left: 15px;
            }}
            
            .tree li {{
                margin: 5px 0;
            }}
            
            .folder {{
                cursor: pointer;
                user-select: none;
            }}
            
            .folder-name {{
                display: block;
                padding: 5px;
                border-radius: 4px;
                transition: background-color 0.2s;
                font-weight: bold;
                color: var(--primary-color);
            }}
            
            .folder-name:hover {{
                background-color: var(--hover-color);
            }}
            
            .folder-name i {{
                margin-right: 5px;
                color: #f9a825;
            }}
            
            .class-item {{
                padding: 2px 0;
            }}
            
            .class-link {{
                display: block;
                text-decoration: none;
                color: var(--text-color);
                padding: 5px;
                border-radius: 4px;
                transition: background-color 0.2s;
            }}
            
            .class-link:hover {{
                background-color: var(--hover-color);
            }}
            
            .class-link i {{
                margin-right: 5px;
                color: var(--secondary-color);
            }}
            
            /* Main Content */
            .main-content {{
                flex: 1;
                margin-left: var(--sidebar-width);
                padding: 20px;
                max-width: calc(100% - var(--sidebar-width));
            }}
            
            header {{
                background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
                color: white;
                padding: 30px;
                margin-bottom: 30px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            
            header h1 {{
                margin-bottom: 10px;
                font-size: 2.4em;
            }}
            
            header p {{
                font-size: 1.1em;
                opacity: 0.9;
            }}
            
            /* Modules */
            .module {{
                margin-bottom: 40px;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                border: 1px solid var(--border-color);
            }}
            
            .module-header {{
                background-color: var(--primary-color);
                color: white;
                padding: 15px 20px;
                border-bottom: 1px solid var(--border-dark);
            }}
            
            .module-content {{
                padding: 20px;
                background-color: white;
            }}
            
            /* Classes */
            .class {{
                margin: 25px 0;
                background-color: var(--light-bg);
                border-radius: 6px;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }}
            
            .class-header {{
                background-color: #e9e9e9;
                padding: 12px 15px;
                font-weight: bold;
                border-bottom: 1px solid var(--border-color);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .class-badge {{
                background-color: var(--primary-color);
                color: white;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 0.75em;
                font-weight: normal;
            }}
            
            .class-content {{
                padding: 15px;
            }}
            
            /* Methods */
            .method {{
                margin: 15px 0;
                background-color: white;
                border-radius: 6px;
                overflow: hidden;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                border-left: 3px solid var(--secondary-color);
            }}
            
            .method-header {{
                background-color: #f5f5f5;
                padding: 10px 15px;
                font-weight: bold;
                border-bottom: 1px solid var(--border-color);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .method-type {{
                background-color: var(--secondary-color);
                color: white;
                padding: 2px 6px;
                border-radius: 12px;
                font-size: 0.7em;
                font-weight: normal;
            }}
            
            .method-content {{
                padding: 15px;
            }}
            
            /* Tables */
            .param-table {{
                margin: 15px 0;
            }}
            
            .param-table table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            
            .param-table th, .param-table td {{
                padding: 10px;
                text-align: left;
                border: 1px solid var(--border-color);
            }}
            
            .param-table th {{
                background-color: var(--light-bg);
                font-weight: 600;
            }}
            
            /* Code */
            pre, code {{
                background-color: var(--code-bg);
                font-family: 'Consolas', 'Monaco', monospace;
                border-radius: 4px;
            }}
            
            code {{
                padding: 2px 4px;
                font-size: 0.9em;
                color: var(--primary-color);
            }}
            
            pre {{
                padding: 15px;
                overflow-x: auto;
                margin: 15px 0;
                border: 1px solid #eee;
            }}
            
            pre code {{
                padding: 0;
                background-color: transparent;
                color: inherit;
            }}
            
            .code-example {{
                background-color: #f8f8f8;
                border: 1px solid #eaeaea;
            }}
            
            /* Descriptions */
            .description {{
                margin-bottom: 20px;
                line-height: 1.7;
            }}
            
            .returns {{
                margin: 15px 0;
                padding: 10px 15px;
                background-color: #f8f8f8;
                border-left: 3px solid #4caf50;
                border-radius: 4px;
            }}
            
            .examples {{
                margin: 15px 0;
            }}
            
            /* Signature */
            .signature {{
                font-family: 'Consolas', 'Monaco', monospace;
                padding: 8px 12px;
                background-color: #232323;
                color: #f8f8f8;
                border-radius: 4px;
                overflow-x: auto;
                margin: 10px 0;
            }}
            
            .signature .param {{
                color: #8be9fd;
            }}
            
            .signature .keyword {{
                color: #ff79c6;
            }}
            
            /* Footer */
            footer {{
                margin-top: 50px;
                padding: 25px;
                background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
                color: white;
                text-align: center;
                border-radius: 8px;
            }}
            
            /* Responsive */
            @media (max-width: 1024px) {{
                .sidebar {{
                    width: 240px;
                }}
                
                .main-content {{
                    margin-left: 240px;
                    max-width: calc(100% - 240px);
                }}
            }}
            
            @media (max-width: 768px) {{
                body {{
                    flex-direction: column;
                }}
                
                .sidebar {{
                    width: 100%;
                    height: auto;
                    position: relative;
                    border-right: none;
                    border-bottom: 1px solid var(--border-color);
                }}
                
                .main-content {{
                    margin-left: 0;
                    max-width: 100%;
                }}
            }}
            
            /* Active navigation item */
            .class-link.active {{
                background-color: var(--primary-light);
                color: white;
            }}
            
            /* Smooth scrolling */
            html {{
                scroll-behavior: smooth;
            }}
            
            /* Parent class indicator */
            .parent-class {{
                margin-top: 5px;
                font-style: italic;
                color: #666;
                font-size: 0.9em;
            }}

            /* Back to top button */
            .back-to-top {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                background-color: var(--primary-color);
                color: white;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                cursor: pointer;
                opacity: 0;
                transition: opacity 0.3s;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                z-index: 99;
            }}
            
            .back-to-top.visible {{
                opacity: 1;
            }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="sidebar-header">
                AIvidence
            </div>
            <div class="sidebar-content">
                <div class="search-bar">
                    <i class="fas fa-search search-icon"></i>
                    <input type="text" id="search-input" placeholder="Search classes...">
                </div>
                
                <div class="package-tree">
                    {generate_sidebar_html(package_tree)}
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <header>
                <h1>AIvidence Documentation</h1>
                <p>AI-powered fact checking tool for fighting misinformation</p>
            </header>
    """
    
    # Process each module in the specified order
    for package, module_files in module_structure.items():
        package_path = os.path.join(package_root, package)
        if not os.path.isdir(package_path):
            continue
        
        print(f"Processing package: {package}")
        
        for module_file in module_files:
            module_path = os.path.join(package_path, module_file)
            if not os.path.isfile(module_path):
                print(f"  - Module file not found: {module_file}")
                continue
                
            module_name = os.path.splitext(module_file)[0]
            full_module_name = f"aividence.{package}.{module_name}"
            module_id = f"{package}_{module_name}"
            
            print(f"  - Processing module: {module_name}")
            
            # Import module
            module = import_module_from_file(full_module_name, module_path)
            
            if not module:
                print(f"    - Failed to import module")
                continue
            
            # Get module docstring
            module_doc = inspect.getdoc(module) or "No module documentation available."
            
            html += f"""
            <div id="{module_id}" class="module">
                <div class="module-header">
                    <h2>{module_name}</h2>
                </div>
                <div class="module-content">
                    {format_docstring(module_doc)}
            """
            
            # Get classes
            classes = inspect.getmembers(module, inspect.isclass)
            for class_name, cls in classes:
                # Skip private classes and those not defined in this module
                if class_name.startswith('_') or cls.__module__ != full_module_name:
                    continue
                
                print(f"    - Processing class: {class_name}")
                
                class_doc = inspect.getdoc(cls) or "No class documentation available."
                class_id = f"{module_id}_{class_name}"
                
                # Get parent classes
                parent_classes = [base.__name__ for base in cls.__bases__ 
                                if base.__name__ != 'object']
                parent_html = ""
                if parent_classes:
                    parent_html = f"""
                    <div class="parent-class">
                        <span>Inherits from: {', '.join(parent_classes)}</span>
                    </div>
                    """
                
                html += f"""
                <div id="{class_id}" class="class">
                    <div class="class-header">
                        <span>{class_name}</span>
                        <span class="class-badge">Class</span>
                    </div>
                    <div class="class-content">
                        {format_docstring(class_doc)}
                        {parent_html}
                """
                
                # Get methods - skipping inherited methods for models package
                methods = inspect.getmembers(cls, inspect.isfunction)
                own_methods = []
                
                if package == 'models':
                    # For models package, only show methods defined in this class
                    # (i.e., skip inherited methods except init)
                    for method_name, method in methods:
                        if method_name == '__init__' or method.__qualname__.startswith(f"{class_name}."):
                            own_methods.append((method_name, method))
                else:
                    own_methods = methods
                
                for method_name, method in own_methods:
                    # Skip private methods except __init__
                    if method_name.startswith('_') and method_name != '__init__':
                        continue
                    
                    method_doc = inspect.getdoc(method) or "No method documentation available."
                    
                    # Get method signature
                    try:
                        signature = str(inspect.signature(method))
                        param_html = signature.replace('(', '(<span class="param">').replace(')', '</span>)').replace(', ', '</span>, <span class="param">')
                        signature_html = f'<div class="signature"><span class="keyword">def</span> {method_name}{param_html}:</div>'
                    except Exception as e:
                        print(f"      - Error getting signature for {method_name}: {e}")
                        signature_html = ""
                    
                    html += f"""
                    <div class="method">
                        <div class="method-header">
                            <span>{method_name}</span>
                            <span class="method-type">Method</span>
                        </div>
                        <div class="method-content">
                            {signature_html}
                            {format_docstring(method_doc)}
                        </div>
                    </div>
                    """
                
                html += """
                    </div>
                </div>
                """
            
            html += """
                </div>
            </div>
            """
    
    # Add Back to Top button
    html += """
        <a href="#" class="back-to-top" id="back-to-top">
            <i class="fas fa-arrow-up"></i>
        </a>
    """
    
    # Add JavaScript
    generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html += f"""
            <footer>
                <p>AIvidence © 2025 - Documentation generated on {generation_date}</p>
            </footer>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                // Folder expand/collapse functionality
                const folders = document.querySelectorAll('.folder > .folder-name');
                folders.forEach(folder => {{
                    folder.addEventListener('click', function() {{
                        const folderItem = this.parentElement;
                        const subTree = folderItem.querySelector('.tree');
                        if (subTree) {{
                            subTree.style.display = subTree.style.display === 'none' ? 'block' : 'none';
                            
                            // Toggle folder icon
                            const icon = this.querySelector('i');
                            if (icon.classList.contains('fa-folder')) {{
                                icon.classList.remove('fa-folder');
                                icon.classList.add('fa-folder-open');
                            }} else {{
                                icon.classList.remove('fa-folder-open');
                                icon.classList.add('fa-folder');
                            }}
                        }}
                    }});
                }});
                
                // Highlight active class
                const classLinks = document.querySelectorAll('.class-link');
                
                function setActiveClass() {{
                    const hash = window.location.hash.substring(1);
                    
                    classLinks.forEach(link => {{
                        link.classList.remove('active');
                        if (link.getAttribute('data-target') === hash) {{
                            link.classList.add('active');
                            
                            // Expand parent folders
                            let parent = link.parentElement;
                            while (parent) {{
                                if (parent.classList.contains('folder')) {{
                                    const subTree = parent.querySelector('.tree');
                                    if (subTree) {{
                                        subTree.style.display = 'block';
                                        
                                        // Update folder icon
                                        const icon = parent.querySelector('.folder-name i');
                                        if (icon && icon.classList.contains('fa-folder')) {{
                                            icon.classList.remove('fa-folder');
                                            icon.classList.add('fa-folder-open');
                                        }}
                                    }}
                                }}
                                parent = parent.parentElement;
                            }}
                        }}
                    }});
                }}
                
                window.addEventListener('hashchange', setActiveClass);
                setActiveClass();
                
                // Search functionality
                const searchInput = document.getElementById('search-input');
                const classElements = document.querySelectorAll('.class');
                
                searchInput.addEventListener('input', function() {{
                    const searchTerm = this.value.toLowerCase();
                    
                    if (searchTerm.length < 2) {{
                        // Show all classes if search term is too short
                        classElements.forEach(cls => {{
                            cls.style.display = 'block';
                        }});
                        
                        // Also show all modules
                        document.querySelectorAll('.module').forEach(module => {{
                            module.style.display = 'block';
                        }});
                        
                        return;
                    }}
                    
                    // Filter classes based on search term
                    classElements.forEach(cls => {{
                        const classText = cls.textContent.toLowerCase();
                        const classId = cls.id.toLowerCase();
                        
                        if (classText.includes(searchTerm) || classId.includes(searchTerm)) {{
                            cls.style.display = 'block';
                            
                            // Show parent module
                            let parent = cls.parentElement;
                            while (parent) {{
                                if (parent.classList.contains('module')) {{
                                    parent.style.display = 'block';
                                    break;
                                }}
                                parent = parent.parentElement;
                            }}
                        }} else {{
                            cls.style.display = 'none';
                        }}
                    }});
                    
                    // Hide modules with no visible classes
                    document.querySelectorAll('.module').forEach(module => {{
                        const visibleClasses = module.querySelectorAll('.class[style="display: block;"]');
                        if (visibleClasses.length === 0) {{
                            module.style.display = 'none';
                        }}
                    }});
                }});
                
                // Expand all folders initially
                document.querySelectorAll('.folder > .tree').forEach(tree => {{
                    tree.style.display = 'block';
                }});
                
                // Update folder icons to show as open initially
                document.querySelectorAll('.folder-name > i.fa-folder').forEach(icon => {{
                    icon.classList.remove('fa-folder');
                    icon.classList.add('fa-folder-open');
                }});
                
                // Back to top button functionality
                const backToTopButton = document.getElementById('back-to-top');
                
                // Show/hide back to top button based on scroll position
                window.addEventListener('scroll', function() {{
                    if (window.pageYOffset > 300) {{
                        backToTopButton.classList.add('visible');
                    }} else {{
                        backToTopButton.classList.remove('visible');
                    }}
                }});
                
                // Smooth scroll to top when button is clicked
                backToTopButton.addEventListener('click', function(e) {{
                    e.preventDefault();
                    window.scrollTo({{ top: 0, behavior: 'smooth' }});
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Documentation successfully generated: {output_file}")
    return output_file

if __name__ == "__main__":
    output_file = generate_html_doc()
    print(f"Documentation available at: {output_file}")
    print("You can open this file in your web browser to view the documentation.")