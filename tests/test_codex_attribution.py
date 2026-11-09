"""Regression cases for process classification; no live processes required."""
import ast
from pathlib import Path
import unittest

source = Path(__file__).resolve().parents[1] / 'skills/more-bananas/app/memlog.py'
module = ast.parse(source.read_text())
function = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'codex_class')
namespace = {}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)


class CodexAttributionTests(unittest.TestCase):
    def test_shared_desktop_is_not_a_codex_tool_ancestor(self):
        namespace['procs'] = {
            '1': ['0', '0', '/Applications/ChatGPT.app/Contents/MacOS/ChatGPT'],
            '2': ['1', '0', '/usr/bin/python3 unrelated.py'],
            '3': ['1', '0', '/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex app-server'],
            '4': ['3', '0', '/usr/bin/python3 actual_tool.py'],
        }
        classify = namespace['codex_class']
        self.assertEqual(classify('1'), 'ChatGPT and Codex shared app')
        self.assertIsNone(classify('2'))
        self.assertEqual(classify('3'), 'Codex processes')
        self.assertEqual(classify('4'), 'Tools started by Codex')

    def test_command_arguments_are_not_executables_and_cycles_stop(self):
        namespace['procs'] = {
            '1': ['2', '0', '/bin/echo /Applications/ChatGPT.app/Contents/MacOS/ChatGPT'],
            '2': ['1', '0', '/bin/echo /Applications/Codex.app/Contents/MacOS/Codex'],
            '3': ['0', '0', '/usr/local/bin/codex exec'],
        }
        self.assertIsNone(namespace['codex_class']('1'))
        self.assertEqual(namespace['codex_class']('3'), 'Codex processes')
