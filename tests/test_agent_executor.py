from types import SimpleNamespace
import unittest
from unittest import mock

from entity.messages import Message, MessageRole
from runtime.node.executor.agent_executor import AgentNodeExecutor
from runtime.node.executor.base import ExecutionContext
from utils.exceptions import WorkflowCancelledError


class _FakeProvider:
    def __init__(self, config) -> None:
        self.config = config

    def create_client(self):
        return object()


class AgentExecutorCancellationTests(unittest.TestCase):
    def test_execute_treats_workflow_cancellation_as_non_error(self) -> None:
        tool_manager = mock.Mock()
        tool_manager.get_tool_specs.return_value = []
        log_manager = mock.Mock()
        context = ExecutionContext(
            tool_manager=tool_manager,
            function_manager=mock.Mock(),
            log_manager=log_manager,
        )
        executor = AgentNodeExecutor(context)

        agent_config = SimpleNamespace(
            provider="openai",
            tooling=None,
            thinking=False,
            input_mode=None,
            params=None,
        )
        node = SimpleNamespace(
            id="Mechanic_Game_Developer",
            node_type="agent",
            role=None,
            model_name="ecosystem-coder-fast",
            as_config=lambda _cls: agent_config,
        )

        with mock.patch("runtime.node.executor.agent_executor.ProviderRegistry.get_provider", return_value=_FakeProvider):
            with mock.patch.object(executor, "_build_agent_invoker", return_value=mock.Mock()):
                with mock.patch.object(executor, "_apply_memory_retrieval", return_value=None):
                    with mock.patch.object(executor, "_build_initial_timeline", return_value=[]):
                        with mock.patch.object(
                            executor,
                            "_invoke_provider",
                            side_effect=WorkflowCancelledError("Workflow execution cancelled"),
                        ):
                            with mock.patch("runtime.node.executor.agent_executor.traceback.print_exc") as print_exc:
                                messages = executor.execute(
                                    node,
                                    [Message(role=MessageRole.USER, content="Create a pygame demo.")],
                                )

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].text_content(), "Workflow execution cancelled")
        self.assertTrue(messages[0].metadata.get("cancelled"))
        print_exc.assert_not_called()
        log_manager.info.assert_called_once()
        log_manager.error.assert_not_called()


if __name__ == "__main__":
    unittest.main()
