import os
import re
import markdown
import shutil

# --- Configuration ---
SOURCE_DIR = "docs"
OUTPUT_DIR = "docs_html"
TEMPLATE_FILE = "docs/layout_template.html" # We will create this

# Navigation Structure (Sidebar)
NAV = [
    {"title": "Home", "path": "index.md"},
    {"title": "User Guide", "children": [
        {"title": "Getting Started", "path": "user-guide/getting-started.md"},
        {"title": "Configuration", "path": "user-guide/configuration.md"},
        {"title": "Usage Modes", "path": "user-guide/usage-modes.md"},
        {"title": "Waiver Management", "path": "user-guide/waiver-management.md"},
        {"title": "Reports", "path": "user-guide/reports.md"},
    ]},
    {"title": "Developer Guide", "children": [
        {"title": "Architecture", "path": "developer-guide/architecture.md"},
        {"title": "Testing", "path": "developer-guide/testing.md"},
        {"title": "Contributing", "path": "developer-guide/contributing.md"},
    ]},
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} - JanusTrace Documentation</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #f0ad4e;
            --primary-dark: #ec971f;
            --bg-sidebar: #1a1a1a;
            --bg-content: #ffffff;
            --text-main: #333333;
            --text-muted: #666666;
            --border: #e1e4e8;
            --sidebar-width: 280px;
        }

        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding: 0;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            color: var(--text-main);
            background: #f8f9fa;
            display: flex;
            min-height: 100vh;
            line-height: 1.6;
        }

        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: var(--bg-sidebar);
            color: #ffffff;
            height: 100vh;
            position: fixed;
            overflow-y: auto;
            padding: 2rem 1.5rem;
            border-right: 1px solid rgba(255,255,255,0.1);
        }

        .sidebar h2 {
            font-size: 1.25rem;
            margin-top: 0;
            margin-bottom: 2rem;
            color: var(--primary);
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        .nav-group { margin-bottom: 2rem; }
        .nav-group-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #888;
            margin-bottom: 0.75rem;
            font-weight: 600;
        }

        .nav-item {
            display: block;
            color: #ccc;
            text-decoration: none;
            padding: 0.5rem 0;
            font-size: 0.95rem;
            transition: color 0.2s;
        }
        .nav-item:hover { color: var(--primary); }
        .nav-item.active { color: var(--primary); font-weight: 600; }

        .main-content {
            margin-left: var(--sidebar-width);
            flex: 1;
            padding: 3rem 4rem;
            max-width: 1200px;
            background: var(--bg-content);
            box-shadow: 0 0 20px rgba(0,0,0,0.05);
            min-height: 100vh;
            min-width: 0; /* Prevents flex box blowout from wide pre blocks */
        }

        /* Typography */
        h1 { font-size: 2.5rem; margin-top: 0; margin-bottom: 2rem; font-weight: 800; color: #111; letter-spacing: -0.03em; border-bottom: 2px solid var(--primary); padding-bottom: 1rem; }
        h2 { font-size: 1.75rem; margin-top: 3rem; margin-bottom: 1.25rem; font-weight: 700; color: #222; }
        h3 { font-size: 1.25rem; margin-top: 2rem; margin-bottom: 1rem; }

        pre {
            background: #f4f4f4;
            padding: 1.5rem;
            border-radius: 8px;
            overflow-x: auto;
            border: 1px solid #ddd;
            font-size: 0.9rem;
            margin: 1.5rem 0;
        }

        code {
            background: #f0f0f0;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 0.9em;
        }

        pre code { padding: 0; background: none; }

        table { border-collapse: collapse; width: 100%; margin: 2rem 0; font-size: 0.95rem; }
        th, td { border: 1px solid var(--border); padding: 0.75rem 1rem; text-align: left; }
        th { background: #f8f9fa; font-weight: 600; }

        .footer {
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.85rem;
            text-align: center;
        }

        a { color: var(--primary-dark); text-decoration: none; }
        a:hover { text-decoration: underline; }

        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 2.5rem auto;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border: 1px solid var(--border);
            transition: transform 0.3s ease;
        }
        img:hover {
            transform: scale(1.01);
        }
        a:hover { text-decoration: underline; }

        .mermaid { margin: 2rem 0; background: white; padding: 1rem; border: 1px solid #eee; border-radius: 8px; }

        /* Responsive */
        @media (max-width: 992px) {
            .sidebar { width: 220px; }
            .main-content { margin-left: 220px; padding: 2rem; }
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({startOnLoad:true});</script>
</head>
<body>
    <div class="sidebar">
        <h2>JanusTrace</h2>
        <div class="nav">
            {{sidebar_nav}}
        </div>
    </div>
    <div class="main-content">
        {{content}}
        <div class="footer">
            &copy; 2026 JanusTrace Documentation - Developed by Ugur Nezir with Gemini 3.1 Pro & Claude 4.6 Sonnet on Google Antigravity
        </div>
    </div>
</body>
</html>
"""

def build_sidebar(current_rel_path):
    html = ""
    for item in NAV:
        if "children" in item:
            html += f'<div class="nav-group"><div class="nav-group-title">{item["title"]}</div>'
            for child in item["children"]:
                active = ' active' if child["path"] == current_rel_path else ''
                # Convert path to .html
                target = child["path"].replace(".md", ".html")
                # Adjust for relative depth
                depth = current_rel_path.count('/')
                prefix = "../" * depth
                html += f'<a href="{prefix}{target}" class="nav-item{active}">{child["title"]}</a>'
            html += '</div>'
        else:
            active = ' active' if item["path"] == current_rel_path else ''
            target = item["path"].replace(".md", ".html")
            depth = current_rel_path.count('/')
            prefix = "../" * depth
            html += f'<a href="{prefix}{target}" class="nav-item{active}">{item["title"]}</a>'
    return html

def convert_md_links(html):
    # Regex to find [text](path.md) and convert to path.html
    return re.sub(r'href="([^"]+)\.md"', r'href="\1.html"', html)

def generate():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Walk through docs
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, SOURCE_DIR).replace('\\', '/')
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content_md = f.read()

                # Convert MD to HTML
                content_html = markdown.markdown(content_md, extensions=['fenced_code', 'tables'])
                content_html = convert_md_links(content_html)

                # Special handling for mermaid diagrams
                content_html = re.sub(
                    r'<pre><code class="language-mermaid">(.*?)</code></pre>',
                    r'<div class="mermaid">\1</div>',
                    content_html,
                    flags=re.DOTALL
                )

                # Build full page
                sidebar = build_sidebar(rel_path)
                final_html = HTML_TEMPLATE.replace("{{content}}", content_html)
                final_html = final_html.replace("{{sidebar_nav}}", sidebar)
                
                # Get title from first H1
                title_match = re.search(r'<h1>(.*?)</h1>', content_html)
                title = title_match.group(1) if title_match else rel_path
                final_html = final_html.replace("{{title}}", title)

                # Save output
                target_path = os.path.join(OUTPUT_DIR, rel_path.replace(".md", ".html"))
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(final_html)
                print(f"Generated: {target_path}")

    # Copy images
    if os.path.exists(os.path.join(SOURCE_DIR, "images")):
        target_img_dir = os.path.join(OUTPUT_DIR, "images")
        if os.path.exists(target_img_dir):
            shutil.rmtree(target_img_dir)
        shutil.copytree(os.path.join(SOURCE_DIR, "images"), target_img_dir)
        print("Copied images directory.")

if __name__ == "__main__":
    try:
        generate()
        print("\nSuccess! Documentation generated in 'docs_html' folder.")
    except ImportError:
        print("Error: 'markdown' package not found. Please run 'pip install markdown'")
    except Exception as e:
        print(f"Error: {e}")
