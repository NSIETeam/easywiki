"""
Agent 自动检测 — 扫描本机安装的AI工具, 弹出连接选项
"""
import os, shutil, subprocess, json
from typing import List, Dict


def detect_agents() -> List[Dict]:
    """扫描本机, 返回所有可检测到的AI Agent"""
    agents = []

    cc_path = shutil.which('claude') or os.path.expanduser('~/.local/bin/claude')
    if cc_path and os.path.exists(cc_path):
        agents.append({
            'id': 'claude-code', 'name': 'Claude Code', 'label': 'CC',
            'path': cc_path, 'type': 'cli',
            'description': 'Anthropic Claude Code CLI',
            'auto_config': {'endpoint': 'stdio://claude', 'model': 'claude-sonnet-4-20250514'},
        })

    codex_path = shutil.which('codex') or shutil.which('opencode')
    if codex_path:
        agents.append({
            'id': 'codex', 'name': 'OpenAI Codex', 'label': 'CX',
            'path': codex_path, 'type': 'cli',
            'description': 'OpenAI Codex CLI',
            'auto_config': {'endpoint': 'stdio://codex', 'model': 'gpt-4o'},
        })

    ec_path = shutil.which('easycode') or shutil.which('ec')
    if ec_path:
        agents.append({
            'id': 'easycode', 'name': 'Easy Code', 'label': 'EC',
            'path': ec_path, 'type': 'cli',
            'description': 'Easy Code CLI Agent',
            'auto_config': {'endpoint': 'stdio://easycode', 'model': 'auto'},
        })

    vscode_path = shutil.which('code')
    copilot_ext = os.path.expanduser('~/.vscode/extensions/github.copilot-*')
    if vscode_path:
        agents.append({
            'id': 'vscode-copilot', 'name': 'VS Code Copilot', 'label': 'VS',
            'path': vscode_path, 'type': 'ide',
            'description': 'GitHub Copilot in VS Code',
            'auto_config': {'endpoint': 'copilot://local', 'model': 'gpt-4o'},
        })

    ollama = shutil.which('ollama')
    if ollama:
        try:
            models = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
            for line in models.stdout.strip().split('\n')[1:]:
                name = line.split()[0] if line.strip() else ''
                if name:
                    agents.append({
                        'id': f'ollama-{name}', 'name': f'Ollama: {name}', 'label': 'OL',
                        'path': ollama, 'type': 'local',
                        'description': f'Local model {name} (Ollama)',
                        'auto_config': {'endpoint': 'http://localhost:11434', 'model': name},
                    })
        except Exception:
            agents.append({
                'id': 'ollama', 'name': 'Ollama', 'label': 'OL',
                'path': ollama, 'type': 'local',
                'description': 'Local LLM (Ollama)',
                'auto_config': {'endpoint': 'http://localhost:11434', 'model': 'llama3'},
            })

    if os.getenv('OPENAI_API_KEY'):
        agents.append({
            'id': 'openai-api', 'name': 'OpenAI API', 'label': 'OA',
            'path': os.getenv('OPENAI_API_KEY', '')[:20] + '...',
            'type': 'cloud',
            'description': 'OPENAI_API_KEY configured',
            'auto_config': {'endpoint': 'https://api.openai.com', 'model': 'gpt-4o'},
        })

    return agents


def generate_agent_config(selected: str) -> Dict:
    agents = detect_agents()
    for a in agents:
        if a['id'] == selected:
            return {
                'agent_id': a['id'], 'agent_name': a['name'],
                'agent_type': a['type'], 'config': a['auto_config'],
                'status': 'connected',
            }
    return {'agent_id': selected, 'status': 'manual_config', 'message': 'Enter endpoint and model manually'}
