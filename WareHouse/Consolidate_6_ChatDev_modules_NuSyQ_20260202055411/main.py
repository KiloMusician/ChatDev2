import unittest
from unified_chatdev_bridge import ChatDevOrchestrator, ChatDevIntegration
class TestUnifiedChatdevBridge(unittest.TestCase):
    def setUp(self):
        self.orchestrator = ChatDevOrchestrator()
        self.integration_module = ChatDevIntegration()
    def test_load_module(self):
        self.orchestrator.load_module("chatdev_integration", self.integration_module)
        self.assertEqual(self.orchestrator.get_module("chatdev_integration"), self.integration_module)
    def test_get_module(self):
        self.assertIsNone(self.orchestrator.get_module("non_existent_module"))
if __name__ == "__main__":
    unittest.main()