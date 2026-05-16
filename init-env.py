#!/usr/bin/env python3

import os
import sys
from pathlib import Path

def get_timezone():
    """Retrieves the system timezone from /etc/timezone or defaults to UTC."""
    try:
        if os.path.exists('/etc/timezone'):
            with open('/etc/timezone', 'r') as f:
                return f.read().strip()
        # Fallback for systems where /etc/timezone doesn't exist
        return os.readlink('/etc/localtime').split('zoneinfo/')[-1]
    except:
        return "UTC"

def list_parent_contents(path):
    """Lists contents of the nearest existing parent directory."""
    p = Path(path).resolve()
    # Find the nearest existing parent
    if not p.exists():
        p = p.parent
    while not p.exists() and p != p.parent:
        p = p.parent
    
    print(f"\n[INFO] Nearest existing parent contains:")
    print(f"{p}:")
    print()
    try:
        # Sort items: directories first, then files, both alphabetically
        items = sorted(list(p.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
        if not items:
            print("(Empty)")
        for item in items:
            name = item.name + ("/" if item.is_dir() else "")
            print(f"{name}")
    except Exception as e:
        print(f"(Error listing contents: {e})")

def prompt_path(key, default, current_val=None):
    """Prompts the user for a path repeatedly until a valid one is found or created."""
    base_val = current_val if current_val else default
    
    while True:
        p = Path(base_val).resolve()
        if p.exists():
            return str(p)
        
        print(f"\n[PROMPT] Path for {key} ({base_val}) not found.")
        try:
            user_input = input(f"Enter preferred location for {key} [{base_val}]: ").strip()
        except EOFError:
            user_input = ""
            
        # If user provided a new path, use it. Otherwise stick with our current base_val
        current_attempt = user_input if user_input else base_val
        p = Path(current_attempt).resolve()
        
        if p.exists():
            return str(p)
            
        list_parent_contents(current_attempt)
        try:
            confirm = input(f"Confirm create directory '{p}'? [y/N]: ").lower()
        except EOFError:
            confirm = "n"
            
        if confirm == 'y':
            try:
                p.mkdir(parents=True, exist_ok=True)
                print(f"[OK] Created {p}")
                return str(p)
            except Exception as e:
                print(f"[ERROR] Failed to create directory: {e}")
        else:
            print("[INFO] Path not created. Please provide a valid location.")
            # Update base_val to the attempt for the next prompt iteration
            base_val = current_attempt

def load_existing_env(path):
    """Loads existing .env values into a dictionary."""
    env = {}
    if not path.exists():
        return env
    with open(path, 'r') as f:
        for line in f:
            stripped = line.strip()
            if '=' in stripped and not stripped.startswith('#'):
                parts = stripped.split('=', 1)
                if len(parts) == 2:
                    env[parts[0].strip()] = parts[1].strip()
    return env

def main():
    example_file = Path('.env-example')
    env_file = Path('.env')
    
    if not example_file.exists():
        print(f"[ERROR] {example_file} not found.")
        sys.exit(1)
        
    # Check if .env exists and ask for permission
    if env_file.exists():
        try:
            confirm = input(f"[WARNING] {env_file} already exists. Overwrite and merge values? [y/N]: ").lower()
            if confirm != 'y':
                print("[INFO] Initialization aborted.")
                sys.exit(0)
        except EOFError:
            print("[ERROR] Input required. Aborting.")
            sys.exit(1)

    existing_env = load_existing_env(env_file)
    puid = os.getuid()
    pgid = os.getgid()
    tz = get_timezone()
    
    print(f"[INFO] Auto-detected: PUID={puid}, PGID={pgid}, TZ={tz}")
    
    output_lines = []
    is_mounts_section = False
    example_keys = set()
    
    with open(example_file, 'r') as f:
        for line in f:
            raw_line = line
            stripped = line.strip()
            
            # Identify the Mounts section
            if stripped.startswith('# Mounts'):
                is_mounts_section = True
                output_lines.append(raw_line)
                continue
            
            # Reset section flag on empty lines or new headers
            if is_mounts_section and (stripped == "" or (stripped.startswith('#') and not stripped.startswith('# Mounts'))):
                is_mounts_section = False
            
            if '=' in stripped and not stripped.startswith('#'):
                parts = stripped.split('=', 1)
                key = parts[0].strip()
                value = parts[1].strip()
                example_keys.add(key)
                
                if key == 'PUID':
                    output_lines.append(f"PUID={puid}\n")
                elif key == 'PGID':
                    output_lines.append(f"PGID={pgid}\n")
                elif key == 'TZ':
                    output_lines.append(f"TZ={tz}\n")
                elif is_mounts_section and key != 'LOCALTIME':
                    # Use existing value if available and valid, otherwise prompt
                    new_val = prompt_path(key, value, existing_env.get(key))
                    output_lines.append(f"{key}={new_val}\n")
                else:
                    # For other keys, preserve existing value if present
                    final_val = existing_env.get(key, value)
                    output_lines.append(f"{key}={final_val}\n")
            else:
                output_lines.append(raw_line)
                
    # Append any keys from existing .env that aren't in .env-example
    extra_keys = [k for k in existing_env if k not in example_keys and k not in ['PUID', 'PGID', 'TZ']]
    if extra_keys:
        output_lines.append("\n# Custom Values (Preserved)\n")
        for k in extra_keys:
            output_lines.append(f"{k}={existing_env[k]}\n")
            
    final_content = "".join(output_lines)
    
    print("\n" + "="*60)
    print("FINAL .env CONTENT:")
    print("="*60)
    print(final_content.strip())
    print("="*60 + "\n")
    
    with open(env_file, 'w') as f:
        f.write(final_content)
        
    print(f"[DONE] Configuration written to {env_file}")

if __name__ == "__main__":
    main()
