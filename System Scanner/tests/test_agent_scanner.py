"""
Unit tests for the Agent Scanner module (scanner/modules/agent_scanner.py).
"""

import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from scanner.models import FindingCategory, RiskLevel
from scanner.modules import agent_scanner


class TestAgentScanner(unittest.TestCase):
    def test_scan_file_matches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            file_path = temp_path / "agent_code.py"
            
            # Content with mixed matches, comments, and non-matches
            code_content = """
# This is a comment containing Agent( or from langchain
import os
from langchain.chat_models import ChatOpenAI
from crewai import Agent

def run():
    # Another comment Crew(
    agent = Agent(role="researcher", goal="find info")
    crew = Crew(agents=[agent], tasks=[])
    assistant = AssistantAgent(name="autogen_assistant")
    
    print("Normal line of code")
"""
            file_path.write_text(code_content, encoding="utf-8")
            
            findings = agent_scanner.scan_file(file_path)
            
            # Should have findings for:
            # 1. from langchain (line 3)
            # 2. from crewai (line 4)
            # 3. Agent( (line 8)
            # 4. Crew( (line 9)
            # 5. AssistantAgent( (line 10)
            # Comments (lines 2, 7) should be ignored.
            
            self.assertEqual(len(findings), 5)
            
            # Verify details
            matches = [f.details["matched_pattern"] for f in findings]
            self.assertIn("LangChain Import", matches)
            self.assertIn("CrewAI Import", matches)
            self.assertIn("Agent Instantiation", matches)
            self.assertIn("Crew Instantiation", matches)
            self.assertIn("AssistantAgent Instantiation", matches)
            
            for f in findings:
                self.assertEqual(f.category, FindingCategory.AI_AGENT)
                self.assertEqual(f.risk_level, RiskLevel.MEDIUM)
                self.assertEqual(f.details["file_path"], str(file_path.resolve()).replace("\\", "/"))

    @patch("pathlib.Path.home")
    @patch("pathlib.Path.cwd")
    def test_run_traversal(self, mock_cwd, mock_home):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            
            # Setup mocked home and cwd
            mock_home.return_value = temp_path / "home"
            mock_cwd.return_value = temp_path / "workspace"
            
            # Create dirs
            home_dir = temp_path / "home"
            workspace_dir = temp_path / "workspace"
            
            home_dir.mkdir()
            workspace_dir.mkdir()
            
            # Create target files
            (home_dir / "home_script.py").write_text("from crewai import Agent\n", encoding="utf-8")
            (workspace_dir / "project_script.py").write_text("from langchain import OpenAI\n", encoding="utf-8")
            
            # File in excluded dir
            excluded_dir = workspace_dir / "venv"
            excluded_dir.mkdir()
            (excluded_dir / "dependency.py").write_text("from langchain import OpenAI\n", encoding="utf-8")
            
            # File beyond depth limit for home
            deep_home_dir = home_dir / "level1" / "level2" / "level3" / "level4"
            deep_home_dir.mkdir(parents=True)
            (deep_home_dir / "deep_script.py").write_text("from crewai import Agent\n", encoding="utf-8")

            findings, info = agent_scanner.run()
            
            self.assertEqual(info.status, "success")
            # Should scan home_script.py and project_script.py,
            # but skip dependency.py (in excluded venv) and deep_script.py (depth limit 3 exceeded for home)
            self.assertEqual(len(findings), 2)
            self.assertEqual(info.findings_count, 2)
            
            sources = [f.details["file_path"] for f in findings]
            self.assertIn(str((home_dir / "home_script.py").resolve()).replace("\\", "/"), sources)
            self.assertIn(str((workspace_dir / "project_script.py").resolve()).replace("\\", "/"), sources)
            self.assertNotIn(str((excluded_dir / "dependency.py").resolve()).replace("\\", "/"), sources)
            self.assertNotIn(str((deep_home_dir / "deep_script.py").resolve()).replace("\\", "/"), sources)

    def test_class_wrapper(self):
        scanner = agent_scanner.AgentScanner()
        self.assertEqual(scanner.MODULE_NAME, "AgentScanner")
        self.assertEqual(scanner.MODULE_NUMBER, 5)
        
        with patch.object(agent_scanner, "run") as mock_run:
            mock_run.return_value = ([], agent_scanner.ModuleInfo(name="AgentScanner", module_number=5))
            findings = scanner.scan()
            self.assertEqual(findings, [])
            mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
