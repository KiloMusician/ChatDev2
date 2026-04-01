import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';

/**
 * Execute a Python snippet located in src/ai/ollama_hub.py.
 * We call into the Python hub using small inline scripts to avoid
 * maintaining a long-running server.  The working directory is the
 * repository root so Python package imports resolve correctly.
 */
function runPython(args: string[]): Promise<{stdout: string; stderr: string; exitCode: number}> {
    return new Promise((resolve, reject) => {
        const repoRoot = path.resolve(__dirname, '..', '..');
        const proc = spawn('python', args, { cwd: repoRoot });
        let stdout = '';
        let stderr = '';
        proc.stdout.on('data', (d: Buffer) => (stdout += d.toString()));
        proc.stderr.on('data', (d: Buffer) => (stderr += d.toString()));
        proc.on('close', (code: number | null) => {
            resolve({ stdout, stderr, exitCode: code ?? 0 });
        });
        proc.on('error', (err: Error) => reject(err));
    });
}

async function listModels(): Promise<string[]> {
    const py = [
        '-c',
        'from src.ai.ollama_hub import ollama_hub; import json; print(json.dumps(ollama_hub.list_models()))'
    ];
    const { stdout, stderr, exitCode } = await runPython(py);
    if (exitCode !== 0) {
        throw new Error(stderr || `list_models exited with code ${exitCode}`);
    }
    try {
        return JSON.parse(stdout.trim() || '[]');
    } catch (e) {
        throw new Error(`Failed to parse model list: ${e}`);
    }
}

async function loadModel(model: string): Promise<boolean> {
    const py = [
        '-c',
        'from src.ai.ollama_hub import ollama_hub; import sys; success = ollama_hub.load_model(sys.argv[1]); print("1" if success else "0")',
        model
    ];
    const { stdout, stderr, exitCode } = await runPython(py);
    if (exitCode !== 0) {
        throw new Error(stderr || `load_model exited with code ${exitCode}`);
    }
    return stdout.toString().trim() === '1';
}

/**
 * Register command and status bar integration for Ollama model selection.
 */
export function registerOllama(context: vscode.ExtensionContext) {
    const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left);
    status.text = 'Ollama: none';
    status.command = 'ollama.selectModel';
    status.show();

    const disposable = vscode.commands.registerCommand('ollama.selectModel', async () => {
        try {
            const models = await listModels();
            if (!models || models.length === 0) {
                vscode.window.showErrorMessage('No Ollama models available.');
                return;
            }
            const selection = await vscode.window.showQuickPick(models, {
                placeHolder: 'Select an Ollama model'
            });
            if (!selection) {
                return;
            }
            const ok = await loadModel(selection);
            if (ok) {
                status.text = `Ollama: ${selection}`;
                vscode.window.showInformationMessage(`Loaded Ollama model: ${selection}`);
            } else {
                vscode.window.showErrorMessage(`Failed to load model: ${selection}`);
            }
        } catch (err: any) {
            vscode.window.showErrorMessage(`Ollama error: ${err.message || err}`);
        }
    });

    context.subscriptions.push(disposable, status);
}
