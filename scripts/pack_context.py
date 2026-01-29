#!/usr/bin/env python3
import os
import sys

def pack_app_context(source_dir="app", output_file="project_context.md"):
    """
    Walks through the source_dir and writes all file contents to output_file
    in a markdown format suitable for AI context.
    """
    
    # Extensions to include
    VALID_EXTENSIONS = {'.py', '.yml', '.yaml', '.Dockerfile', 'Dockerfile', '.json', '.md', '.txt', '.sh'}
    # Directories to ignore
    IGNORE_DIRS = {'__pycache__', '.git', '.idea', '.vscode', 'node_modules', 'venv', 'env'}
    
    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return

    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(f"# Project Context: {source_dir}\n\n")
        out.write("This document contains the source code for the project.\n\n")
        
        file_count = 0
        
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in sorted(files):
                ext = os.path.splitext(file)[1]
                if ext in VALID_EXTENSIONS or file in VALID_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        rel_path = os.path.relpath(file_path, start=".")
                        
                        out.write(f"## File: `{rel_path}`\n\n")
                        
                        # Determine language for highlighting
                        lang = "text"
                        if ext == '.py': lang = "python"
                        elif ext in ('.yml', '.yaml'): lang = "yaml"
                        elif ext == '.json': lang = "json"
                        elif ext == '.sh': lang = "bash"
                        elif 'Dockerfile' in file: lang = "dockerfile"
                        elif ext == '.md': lang = "markdown"

                        out.write(f"```{lang}\n")
                        out.write(content)
                        if not content.endswith('\n'):
                            out.write('\n')
                        out.write("```\n\n")
                        out.write("---\n\n")
                        
                        file_count += 1
                        print(f"Packed: {rel_path}")
                        
                    except Exception as e:
                        print(f"Skipping {file_path}: {e}")

    print(f"\n✅ Successfully packed {file_count} files from '{source_dir}' into '{output_file}'")

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "app"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "project_context.md"
    
    pack_app_context(target_dir, output_path)
