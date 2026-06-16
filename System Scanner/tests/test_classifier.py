"""
Unit tests for the Classification Engine (scanner/classifier.py).
"""

import unittest
from scanner.classifier import ClassificationEngine
from scanner.models import Finding, FindingCategory, RiskLevel


class TestClassificationEngine(unittest.TestCase):
    def setUp(self):
        self.classifier = ClassificationEngine()

    def test_classify_api_keys(self):
        # API Key from Title
        finding1 = Finding(
            module_name="APIScanner",
            title="OpenAI API Key Leak",
            description="Exposed OpenAI API key in source code",
            source="config.py",
        )
        classified1 = self.classifier.classify_single(finding1)
        self.assertEqual(classified1.category, FindingCategory.CONFIGURATION)
        self.assertEqual(classified1.risk_level, RiskLevel.HIGH)
        self.assertEqual(classified1.confidence, 0.95)
        self.assertEqual(classified1.details.get("provider"), "OpenAI")

        # API Key from Source path containing key
        finding2 = Finding(
            module_name="CustomScanner",
            title="Credential Leak",
            description="Some description",
            source="secrets/anthropic_key.txt",
        )
        classified2 = self.classifier.classify_single(finding2)
        self.assertEqual(classified2.category, FindingCategory.CONFIGURATION)
        self.assertEqual(classified2.risk_level, RiskLevel.HIGH)
        self.assertEqual(classified2.details.get("provider"), "Anthropic")

    def test_classify_ai_models(self):
        # HuggingFace Cache path
        finding1 = Finding(
            module_name="FileScanner",
            title="llama-2-7b.gguf",
            description="Large language model file",
            source="C:/Users/User/.cache/huggingface/hub/models--llama-2-7b/snapshots/.../model.safetensors",
        )
        classified1 = self.classifier.classify_single(finding1)
        self.assertEqual(classified1.category, FindingCategory.AI_MODEL)
        self.assertEqual(classified1.risk_level, RiskLevel.LOW)
        self.assertEqual(classified1.confidence, 0.95)

        # Downloads directory (unmanaged)
        finding2 = Finding(
            module_name="FileScanner",
            title="custom_model.pt",
            description="PyTorch weights",
            source="C:/Users/User/Downloads/custom_model.pt",
        )
        classified2 = self.classifier.classify_single(finding2)
        self.assertEqual(classified2.category, FindingCategory.AI_MODEL)
        self.assertEqual(classified2.risk_level, RiskLevel.MEDIUM)

        # Other path
        finding3 = Finding(
            module_name="FileScanner",
            title="model.onnx",
            description="ONNX model",
            source="C:/Project/model.onnx",
        )
        classified3 = self.classifier.classify_single(finding3)
        self.assertEqual(classified3.category, FindingCategory.AI_MODEL)
        self.assertEqual(classified3.risk_level, RiskLevel.INFO)

    def test_classify_llm_runtimes(self):
        # Running Ollama instance
        finding1 = Finding(
            module_name="ProcessScanner",
            title="ollama.exe",
            description="Running Ollama service",
            source="ollama",
        )
        classified1 = self.classifier.classify_single(finding1)
        self.assertEqual(classified1.category, FindingCategory.LLM_RUNTIME)
        self.assertEqual(classified1.risk_level, RiskLevel.MEDIUM)
        self.assertEqual(classified1.confidence, 0.90)

        # Non-active runtime reference
        finding2 = Finding(
            module_name="RuntimeScanner",
            title="LM Studio Folder",
            description="LM Studio app data directory exists",
            source="C:/Users/User/AppData/Local/lm-studio",
        )
        classified2 = self.classifier.classify_single(finding2)
        self.assertEqual(classified2.category, FindingCategory.LLM_RUNTIME)
        self.assertEqual(classified2.risk_level, RiskLevel.LOW)

    def test_classify_ai_agents(self):
        finding = Finding(
            module_name="AgentScanner",
            title="CrewAI Agent Detection",
            description="Found CrewAI code patterns: Agent(role='Researcher')",
            source="src/agents.py",
        )
        classified = self.classifier.classify_single(finding)
        self.assertEqual(classified.category, FindingCategory.AI_AGENT)
        self.assertEqual(classified.risk_level, RiskLevel.MEDIUM)
        self.assertEqual(classified.confidence, 0.85)

    def test_classify_ml_libraries(self):
        # Core library
        finding1 = Finding(
            module_name="PackageScanner",
            title="tensorflow==2.10.0",
            description="Installed python library",
            source="pip",
        )
        classified1 = self.classifier.classify_single(finding1)
        self.assertEqual(classified1.category, FindingCategory.ML_FRAMEWORK)
        self.assertEqual(classified1.risk_level, RiskLevel.INFO)
        self.assertEqual(classified1.confidence, 0.90)

        # Agent packages classified under AI_AGENT
        finding2 = Finding(
            module_name="PackageScanner",
            title="langchain==0.1.0",
            description="Installed python library",
            source="pip",
        )
        classified2 = self.classifier.classify_single(finding2)
        self.assertEqual(classified2.category, FindingCategory.AI_AGENT)
        self.assertEqual(classified2.risk_level, RiskLevel.INFO)

    def test_classify_system_info(self):
        finding = Finding(
            module_name="SystemScanner",
            title="Host Machine Specs",
            description="Hardware details",
            source="system",
        )
        classified = self.classifier.classify_single(finding)
        self.assertEqual(classified.category, FindingCategory.SYSTEM_INFO)
        self.assertEqual(classified.risk_level, RiskLevel.INFO)
        self.assertEqual(classified.confidence, 1.0)

    def test_classify_bulk(self):
        findings = [
            Finding(module_name="SystemScanner", title="SysInfo", description="SysDesc", source="sys"),
            Finding(module_name="APIScanner", title="OpenAI key", description="OpenAI desc", source="secrets.env"),
        ]
        classified = self.classifier.classify(findings)
        self.assertEqual(len(classified), 2)
        self.assertEqual(classified[0].category, FindingCategory.SYSTEM_INFO)
        self.assertEqual(classified[1].category, FindingCategory.CONFIGURATION)


if __name__ == "__main__":
    unittest.main()
