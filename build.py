#!/usr/bin/env python3
import subprocess
import os
import shutil
import sys

LATEX_DIR = 'latex'
TEMP_DIR = os.path.join(LATEX_DIR, 'temp')
OUTPUT_DIR = 'output'

def load_env(env_file):
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def snake_to_camel(snake_str):
    components = snake_str.split('_')
    return ''.join(x.capitalize() for x in components[0:])

os.environ['UID'] = str(os.getuid())
os.environ['GID'] = str(os.getgid())
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

if len(sys.argv) == 3:
    mode = sys.argv[1]
    lang = sys.argv[2]
    output_name = f'cv_{mode.replace("-", "")}_{["eng", "ptbr"][int(lang)]}'
    variants = [{'mode': mode, 'lang': lang, 'output': output_name}]
elif len(sys.argv) == 1:
    variants = [
        {'mode': 'altacv', 'lang': '0', 'output': 'cv_eng'},
        {'mode': 'altacv', 'lang': '1', 'output': 'cv_ptbr'},
        {'mode': 'altacv-ats', 'lang': '0', 'output': 'cv_ats_eng'},
        {'mode': 'altacv-ats', 'lang': '1', 'output': 'cv_ats_ptbr'},
    ]
else:
    print("Usage: python build.py [mode] [lang]")
    print("  mode: altacv or altacv-ats")
    print("  lang: 0 (eng) or 1 (pt-br)")
    print("Example: python build.py altacv 0")
    print("Or run without arguments to build all variants")
    sys.exit(1)

build_commands = []
for variant in variants:
    lang_name = 'eng' if variant['lang'] == '0' else 'ptbr'
    env_file = f'.{lang_name}.env'
    env_vars = load_env(env_file)
    
    temp_main = os.path.join(LATEX_DIR, f'temp_{variant["output"]}.tex')
    
    env_defs = '\n'.join([
        f"\t\t\\def\\env{snake_to_camel(key)}{{{value}}}"
        for key, value in env_vars.items()
    ])
    
    temp_content = f"""\
		\\def\\currentMode{{{variant['mode']}}}
		\\def\\currentLang{{{variant['lang']}}}
        {env_defs}
		\\input{{main.tex}}
	"""
    
    with open(temp_main, 'w') as f:
        f.write(temp_content)
    
    build_commands.append({'temp_main': temp_main, 'output': variant['output']})

shell_script = " && ".join([
    f"pdflatex -interaction=nonstopmode -output-directory=temp -jobname={cmd['output']} temp_{cmd['output']}.tex"
    for cmd in build_commands
])

if len(variants) == 1:
    print(f"Building {variants[0]['output']} (mode={variants[0]['mode']}, lang={variants[0]['lang']})...")
else:
    print("Building all CV variants...")

result = subprocess.run(
    ['docker', 'compose', 'run', '--rm', 'latex', 'sh', '-c', shell_script],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print("✗ Build errors occurred:")
    print(result.stdout)
    print(result.stderr)
else:
    print("✓ All builds completed")

for cmd in build_commands:
    temp_pdf = os.path.join(TEMP_DIR, f'{cmd["output"]}.pdf')
    output_pdf = os.path.join(OUTPUT_DIR, f'{cmd["output"]}.pdf')
    
    if os.path.exists(temp_pdf):
        shutil.move(temp_pdf, output_pdf)
        size = os.path.getsize(output_pdf) / 1024
        print(f"  ✓ {cmd['output']}.pdf ({size:.1f} KB)")
    else:
        print(f"  ✗ {cmd['output']}.pdf not generated")
    
    if os.path.exists(cmd['temp_main']):
        os.remove(cmd['temp_main'])

shutil.rmtree(TEMP_DIR, ignore_errors=True)