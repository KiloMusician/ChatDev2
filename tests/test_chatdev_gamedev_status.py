import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tools.chatdev_gamedev_status import (
    _build_assessment,
    _build_automation_summary,
    _latest_receipt_payload,
    _preferred_model_alignment,
)
from tests.chatdev_gamedev_test_helpers import build_smoke_receipt_payload


class ChatdevGamedevStatusTests(unittest.TestCase):
    def test_latest_receipt_payload_preserves_running_smoke_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            (receipt_dir / "latest.json").write_text(
                json.dumps(
                    build_smoke_receipt_payload(
                        session_name="status-running-summary",
                        status="running",
                        bounded_stop_reason=None,
                        first_artifact_path=None,
                        token_usage={
                            "model_usages": {},
                            "call_history": [],
                        },
                        artifact_runtime_validation=[],
                    )
                ),
                encoding="utf-8",
            )

            payload = _latest_receipt_payload(receipt_dir, full=False)

            self.assertEqual(payload["status"], "running")
            self.assertEqual(payload["attempted_model"], "ecosystem-devstral")
            self.assertIsNone(payload["model"])
            self.assertEqual(payload["runtime_proof_depth"], "missing")
            self.assertFalse(payload["runtime_launch_proven"])
            self.assertFalse(payload["runtime_completion_proven"])

    def test_latest_receipt_payload_reuses_shared_latest_summary_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            (receipt_dir / "latest.json").write_text(
                json.dumps(build_smoke_receipt_payload(session_name="status-shared-summary")),
                encoding="utf-8",
            )

            payload = _latest_receipt_payload(receipt_dir, full=False)

            self.assertEqual(payload["workflow_used"], r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml")
            self.assertEqual(payload["provider"], "openai")
            self.assertEqual(payload["model"], "ecosystem-coder-fast")
            self.assertEqual(payload["proven_smoke_model"], "ecosystem-coder-fast")
            self.assertEqual(payload["attempted_model"], "ecosystem-devstral")
            self.assertEqual(payload["env_defaults"]["BASE_URL"], "http://127.0.0.1:4000/v1")
            self.assertEqual(
                payload["output_path"],
                r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\proof\code_workspace\game.py",
            )
            self.assertEqual(payload["artifact_runtime_outcome"], "completed")
            self.assertEqual(payload["runtime_proof_depth"], "completed")
            self.assertTrue(payload["runtime_launch_proven"])
            self.assertTrue(payload["runtime_completion_proven"])

    def test_preferred_model_alignment_returns_empty_advisories_when_models_missing(self) -> None:
        alignment = _preferred_model_alignment(
            preferred_live_model=None,
            proven_smoke_model=None,
            smoke_proven=False,
        )

        self.assertEqual(
            alignment,
            {
                "preferred_live_model": None,
                "proven_smoke_model": None,
                "preferred_live_model_matches_smoke": False,
                "preferred_live_model_proven_for_smoke": False,
                "advisories": [],
            },
        )

    def test_preferred_model_alignment_marks_matching_proven_model(self) -> None:
        alignment = _preferred_model_alignment(
            preferred_live_model="ecosystem-coder-fast",
            proven_smoke_model="ecosystem-coder-fast",
            smoke_proven=True,
        )

        self.assertEqual(alignment["preferred_live_model"], "ecosystem-coder-fast")
        self.assertEqual(alignment["proven_smoke_model"], "ecosystem-coder-fast")
        self.assertTrue(alignment["preferred_live_model_matches_smoke"])
        self.assertTrue(alignment["preferred_live_model_proven_for_smoke"])
        self.assertEqual(alignment["advisories"], [])

    def test_preferred_model_alignment_marks_drift_and_unproven_live_model(self) -> None:
        alignment = _preferred_model_alignment(
            preferred_live_model="ecosystem-devstral",
            proven_smoke_model="ecosystem-coder-fast",
            smoke_proven=True,
        )

        self.assertEqual(alignment["preferred_live_model"], "ecosystem-devstral")
        self.assertEqual(alignment["proven_smoke_model"], "ecosystem-coder-fast")
        self.assertFalse(alignment["preferred_live_model_matches_smoke"])
        self.assertFalse(alignment["preferred_live_model_proven_for_smoke"])
        self.assertIn("preferred_live_model_differs_from_proven_smoke_model", alignment["advisories"])
        self.assertIn("preferred_live_model_not_proven_for_bounded_smoke", alignment["advisories"])

    def test_build_assessment_marks_ready_with_gaps_for_worker_only_surface(self) -> None:
        doctor = {
            "summary": {
                "chatdev_colony_health": True,
                "chatdev_local_health": False,
                "live_surface_id": "devmentor-chatdev-worker",
                "gamedev_python_with_pygame": ["repo_gamedev_venv"],
            },
            "probes": {
                "litellm": {
                    "paths": {
                        "/v1/models": {"ok": True},
                    }
                }
            },
        }
        latest = {"status": "artifact_emitted"}
        yaml_validation = {"ok": True}

        assessment = _build_assessment(doctor, latest, yaml_validation)

        self.assertEqual(assessment["overall_status"], "ready_with_gaps")
        self.assertTrue(assessment["bounded_smoke_ok"])
        self.assertTrue(assessment["yaml_validation_ok"])
        self.assertTrue(assessment["litellm_ok"])
        self.assertTrue(assessment["repo_gamedev_runtime_ok"])
        self.assertEqual(assessment["live_surface_mode"], "worker_only")
        self.assertIsNone(assessment["preferred_live_model"])
        self.assertIsNone(assessment["proven_smoke_model"])
        self.assertFalse(assessment["preferred_live_model_matches_smoke"])
        self.assertFalse(assessment["preferred_live_model_proven_for_smoke"])
        self.assertEqual(assessment["next_action"], "start_local_devall_app")
        self.assertIn("local_start", assessment["operator_commands"])
        self.assertIn("latest_summary", assessment["operator_commands"])
        self.assertIn("status_compact", assessment["operator_commands"])
        self.assertIn("status_full", assessment["operator_commands"])
        self.assertIn("smoke_status_compact", assessment["operator_commands"])
        self.assertTrue(all("-NoProfile" in command for command in assessment["operator_commands"].values()))
        self.assertIn("chatdev_local_offline", assessment["gaps"])
        self.assertIn("live_surface_is_queue_worker_not_devall_app", assessment["gaps"])
        self.assertEqual(assessment["advisories"], [])
        self.assertEqual(assessment["notes"], [])

    def test_build_assessment_marks_degraded_when_yaml_validation_is_not_proven(self) -> None:
        doctor = {
            "summary": {
                "chatdev_colony_health": True,
                "chatdev_local_health": True,
                "live_surface_id": "devmentor-chatdev-worker",
                "gamedev_python_with_pygame": ["repo_gamedev_venv"],
            },
            "probes": {
                "litellm": {
                    "paths": {
                        "/v1/models": {"ok": True},
                    }
                }
            },
        }
        latest = {"status": "artifact_emitted"}
        yaml_validation = {"ok": False}

        assessment = _build_assessment(doctor, latest, yaml_validation)

        self.assertEqual(assessment["overall_status"], "degraded")
        self.assertFalse(assessment["yaml_validation_ok"])
        self.assertIsNone(assessment["preferred_live_model"])
        self.assertIsNone(assessment["proven_smoke_model"])
        self.assertFalse(assessment["preferred_live_model_matches_smoke"])
        self.assertFalse(assessment["preferred_live_model_proven_for_smoke"])
        self.assertEqual(assessment["next_action"], "run_validate_yamls")
        self.assertIn("yaml_validation_not_proven", assessment["gaps"])
        self.assertEqual(assessment["advisories"], [])

    def test_build_assessment_surfaces_preferred_model_drift_note(self) -> None:
        doctor = {
            "summary": {
                "chatdev_colony_health": True,
                "chatdev_local_health": False,
                "live_surface_id": "devmentor-chatdev-worker",
                "gamedev_python_with_pygame": ["repo_gamedev_venv"],
            },
            "probes": {
                "litellm": {
                    "paths": {
                        "/v1/models": {"ok": True},
                    }
                },
                "chatdev_colony": {
                    "paths": {
                        "/status": {
                            "json": {
                                "backend": "litellm",
                                "model": "ecosystem-devstral",
                            }
                        }
                    }
                },
            },
        }
        latest = {
            "status": "artifact_emitted",
            "token_usage": {
                "model_usages": {"ecosystem-coder-fast": {"total_tokens": 123}},
            },
        }
        yaml_validation = {"ok": True}

        assessment = _build_assessment(doctor, latest, yaml_validation)

        self.assertEqual(assessment["preferred_live_model"], "ecosystem-devstral")
        self.assertEqual(assessment["proven_smoke_model"], "ecosystem-coder-fast")
        self.assertFalse(assessment["preferred_live_model_matches_smoke"])
        self.assertFalse(assessment["preferred_live_model_proven_for_smoke"])
        self.assertIn("preferred_live_model_differs_from_proven_smoke_model", assessment["advisories"])
        self.assertIn("preferred_live_model_not_proven_for_bounded_smoke", assessment["advisories"])
        self.assertEqual(assessment["next_action"], "start_local_devall_app")
        self.assertEqual(len(assessment["notes"]), 2)
        self.assertIn("ecosystem-devstral", assessment["notes"][0])
        self.assertIn("ecosystem-coder-fast", assessment["notes"][0])

    def test_build_automation_summary_surfaces_callable_and_proxy_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "proof.json"
            receipt_path.write_text("{}", encoding="utf-8")
            recent = time.time() - 120
            os.utime(receipt_path, (recent, recent))

            doctor = {
                "summary": {
                    "chatdev_colony_health": True,
                    "chatdev_local_health": False,
                    "local_app_loaded": True,
                    "local_app_bootable": True,
                    "local_app_core_routes_ready": True,
                    "local_app_extended_routes_ready": False,
                    "live_surface_id": "devmentor-chatdev-worker",
                    "live_surface_kind": "queue_worker",
                    "gamedev_python_with_pygame": ["repo_gamedev_venv"],
                },
                "probes": {
                    "litellm": {"paths": {"/v1/models": {"ok": True}}},
                    "ollama": {"paths": {"/api/tags": {"ok": True}}},
                    "chatdev_colony": {
                        "paths": {
                            "/status": {
                                "json": {
                                    "backend": "litellm",
                                    "model": "ecosystem-devstral",
                                }
                            }
                        }
                    },
                },
                "local_startup_probe": {
                    "ok": False,
                    "port": 63687,
                    "health_url": "http://127.0.0.1:63687/health",
                    "error": "startup_timeout",
                    "log_path": r"C:\Users\keath\AppData\Local\Temp\chatdev-local-startup-smoke\startup-63687.log",
                },
            }
            latest = {
                "status": "artifact_emitted",
                "repo_root": r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke",
                "first_artifact_path": r"WareHouse\proof\code_workspace\game.py",
                "result_json": str(receipt_path),
                "runtime_python": r"C:\dev\active\ChatDev2\.venv-gamedev313\Scripts\python.exe",
                "artifact_runtime_outcome": "timed_out_after_launch",
                "runtime_proof_depth": "launch_only",
                "runtime_launch_proven": True,
                "runtime_completion_proven": False,
                "yaml_file": r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml",
                "override_model": "ecosystem-devstral",
                "env_defaults": {
                    "BASE_URL": "http://127.0.0.1:4000/v1",
                    "API_KEY": "ollama-local-model",
                },
                "token_usage": {
                    "model_usages": {"ecosystem-coder-fast": {"total_tokens": 123}},
                    "call_history": [
                        {
                            "provider": "openai",
                            "model_name": "ecosystem-coder-fast",
                        }
                    ],
                },
            }
            yaml_validation = {"ok": True}
            assessment = _build_assessment(doctor, latest, yaml_validation)

            summary = _build_automation_summary(doctor, latest, yaml_validation, assessment)

            self.assertEqual(summary["contract_version"], 1)
            self.assertEqual(summary["proof_scope"], "bounded_sandbox_smoke")
            self.assertTrue(summary["callable"])
            self.assertEqual(summary["callable_via"], "worker_only_lane")
            self.assertFalse(summary["full_devall_ready"])
            self.assertTrue(summary["local_app_bootable"])
            self.assertTrue(summary["local_app_core_routes_ready"])
            self.assertFalse(summary["local_app_extended_routes_ready"])
            self.assertEqual(summary["workflow_execution"], "passed")
            self.assertEqual(summary["workflow_used"], latest["yaml_file"])
            self.assertEqual(summary["provider"], "openai")
            self.assertEqual(summary["model"], "ecosystem-coder-fast")
            self.assertEqual(summary["proven_smoke_model"], "ecosystem-coder-fast")
            self.assertEqual(summary["attempted_model"], "ecosystem-devstral")
            self.assertEqual(summary["preferred_live_model"], "ecosystem-devstral")
            self.assertEqual(summary["preferred_live_backend"], "litellm")
            self.assertFalse(summary["preferred_live_model_matches_smoke"])
            self.assertFalse(summary["preferred_live_model_proven_for_smoke"])
            self.assertEqual(summary["env_defaults"]["BASE_URL"], "http://127.0.0.1:4000/v1")
            self.assertFalse(summary["smoke_attempted_without_model_call"])
            self.assertEqual(
                summary["output_path"],
                r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\proof\code_workspace\game.py",
            )
            self.assertEqual(summary["proof_freshness"], "fresh")
            self.assertEqual(summary["proof_stale_after_seconds"], 86400)
            self.assertIsNotNone(summary["proof_generated_at"])
            self.assertLess(summary["proof_age_seconds"], 3600)
            self.assertEqual(summary["artifact_runtime_outcome"], "timed_out_after_launch")
            self.assertEqual(summary["runtime_proof_depth"], "launch_only")
            self.assertTrue(summary["runtime_launch_proven"])
            self.assertFalse(summary["runtime_completion_proven"])
            self.assertTrue(summary["current_proof"])
            self.assertEqual(summary["current_proof_blockers"], [])
            self.assertTrue(summary["runtime_launch_gate_ok"])
            self.assertEqual(summary["runtime_launch_gate_blockers"], [])
            self.assertFalse(summary["runtime_completion_gate_ok"])
            self.assertIn("runtime_completion_not_proven", summary["runtime_completion_gate_blockers"])
            self.assertTrue(summary["workflow_gate_ok"])
            self.assertEqual(summary["workflow_gate_blockers"], [])
            self.assertFalse(summary["proxy_health"]["local_devall_app"])
            self.assertTrue(summary["proxy_health"]["local_devall_core_routes"])
            self.assertFalse(summary["proxy_health"]["local_devall_extended_routes"])
            self.assertTrue(summary["proxy_health"]["colony_worker"])
            self.assertTrue(summary["proxy_health"]["ollama"])
            self.assertEqual(summary["backend_requirements"]["primary_provider"], "litellm")
            self.assertTrue(summary["backend_requirements"]["primary_provider_required"])
            self.assertTrue(summary["backend_requirements"]["primary_provider_healthy"])
            self.assertFalse(summary["backend_requirements"]["ollama_required_for_current_lane"])
            self.assertTrue(summary["backend_requirements"]["ollama_healthy"])
            self.assertEqual(
                summary["backend_requirements"]["ollama_optional_reason"],
                "bounded_gamedev_smoke_is_currently_proven_via_litellm",
            )
            self.assertFalse(summary["local_devall_proof"]["currently_live_on_6400"])
            self.assertTrue(summary["local_devall_proof"]["loaded_from_checkout"])
            self.assertFalse(summary["local_devall_proof"]["startup_probe_ok"])
            self.assertEqual(summary["local_devall_proof"]["startup_probe_error"], "startup_timeout")
            self.assertEqual(summary["local_devall_proof"]["startup_probe_port"], 63687)
            self.assertFalse(summary["local_devall_proof"]["extended_routes_ready"])
            self.assertIn("local_devall_not_running_on_6400", summary["local_devall_proof"]["blockers"])
            self.assertIn("local_startup_probe_startup_timeout", summary["local_devall_proof"]["blockers"])
            self.assertEqual(summary["local_devall_proof"]["operator_command"], summary["operator_commands"]["local_start"])
            self.assertEqual(summary["local_devall_proof"]["proof_command"], summary["operator_commands"]["local_proof"])
            self.assertIn("local_start", summary["operator_commands"])
            self.assertIn("local_proof", summary["operator_commands"])
            self.assertIn("latest_summary", summary["operator_commands"])
            self.assertIn("status_compact", summary["operator_commands"])
            self.assertIn("status_full", summary["operator_commands"])
            self.assertIn("smoke_status_compact", summary["operator_commands"])
            self.assertTrue(all("-NoProfile" in command for command in summary["operator_commands"].values()))
            self.assertIn("preferred_live_model_differs_from_proven_smoke_model", summary["advisories"])
            self.assertIn("preferred_live_model_not_proven_for_bounded_smoke", summary["advisories"])
            self.assertIn("chatdev_local_offline", summary["errors"])
            self.assertIn("live_surface_is_queue_worker_not_devall_app", summary["errors"])

    def test_assessment_and_automation_summary_stay_aligned_on_preferred_model_truth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "proof.json"
            receipt_path.write_text("{}", encoding="utf-8")
            recent = time.time() - 120
            os.utime(receipt_path, (recent, recent))

            doctor = {
                "summary": {
                    "chatdev_colony_health": True,
                    "chatdev_local_health": False,
                    "local_app_bootable": True,
                    "local_app_core_routes_ready": True,
                    "local_app_extended_routes_ready": True,
                    "live_surface_id": "devmentor-chatdev-worker",
                    "live_surface_kind": "queue_worker",
                    "gamedev_python_with_pygame": ["repo_gamedev_venv"],
                },
                "probes": {
                    "litellm": {"paths": {"/v1/models": {"ok": True}}},
                    "ollama": {"paths": {"/api/tags": {"ok": True}}},
                    "chatdev_colony": {
                        "paths": {
                            "/status": {
                                "json": {
                                    "backend": "litellm",
                                    "model": "ecosystem-devstral",
                                }
                            }
                        }
                    },
                },
            }
            latest = {
                "status": "artifact_emitted",
                "repo_root": r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke",
                "first_artifact_path": r"WareHouse\proof\code_workspace\game.py",
                "result_json": str(receipt_path),
                "runtime_python": r"C:\dev\active\ChatDev2\.venv-gamedev313\Scripts\python.exe",
                "artifact_runtime_outcome": "completed",
                "runtime_proof_depth": "completed",
                "runtime_launch_proven": True,
                "runtime_completion_proven": True,
                "yaml_file": r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml",
                "token_usage": {
                    "model_usages": {"ecosystem-coder-fast": {"total_tokens": 123}},
                    "call_history": [
                        {
                            "provider": "openai",
                            "model_name": "ecosystem-coder-fast",
                        }
                    ],
                },
            }
            yaml_validation = {"ok": True}

            assessment = _build_assessment(doctor, latest, yaml_validation)
            summary = _build_automation_summary(doctor, latest, yaml_validation, assessment)

            self.assertEqual(summary["proven_smoke_model"], assessment["proven_smoke_model"])
            self.assertEqual(summary["preferred_live_model"], assessment["preferred_live_model"])
            self.assertEqual(summary["preferred_live_model_matches_smoke"], assessment["preferred_live_model_matches_smoke"])
            self.assertEqual(summary["preferred_live_model_proven_for_smoke"], assessment["preferred_live_model_proven_for_smoke"])
            self.assertEqual(summary["advisories"], assessment["advisories"])

    def test_build_automation_summary_marks_workflow_gate_false_when_yaml_validation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "proof.json"
            receipt_path.write_text("{}", encoding="utf-8")
            recent = time.time() - 120
            os.utime(receipt_path, (recent, recent))

            doctor = {
                "summary": {
                    "chatdev_colony_health": True,
                    "chatdev_local_health": False,
                    "local_app_bootable": True,
                    "local_app_core_routes_ready": True,
                    "local_app_extended_routes_ready": False,
                    "live_surface_id": "devmentor-chatdev-worker",
                    "live_surface_kind": "queue_worker",
                    "gamedev_python_with_pygame": ["repo_gamedev_venv"],
                },
                "probes": {
                    "litellm": {"paths": {"/v1/models": {"ok": True}}},
                    "ollama": {"paths": {"/api/tags": {"ok": True}}},
                    "chatdev_colony": {
                        "paths": {
                            "/status": {
                                "json": {
                                    "backend": "litellm",
                                    "model": "ecosystem-devstral",
                                }
                            }
                        }
                    },
                },
            }
            latest = {
                "status": "artifact_emitted",
                "repo_root": r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke",
                "first_artifact_path": r"WareHouse\proof\code_workspace\game.py",
                "result_json": str(receipt_path),
                "runtime_python": r"C:\dev\active\ChatDev2\.venv-gamedev313\Scripts\python.exe",
                "artifact_runtime_outcome": "timed_out_after_launch",
                "runtime_proof_depth": "launch_only",
                "runtime_launch_proven": True,
                "runtime_completion_proven": False,
                "yaml_file": r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml",
                "token_usage": {
                    "model_usages": {"ecosystem-coder-fast": {"total_tokens": 123}},
                    "call_history": [
                        {
                            "provider": "openai",
                            "model_name": "ecosystem-coder-fast",
                        }
                    ],
                },
            }
            yaml_validation = {"ok": False}
            assessment = _build_assessment(doctor, latest, yaml_validation)

            summary = _build_automation_summary(doctor, latest, yaml_validation, assessment)

            self.assertTrue(summary["current_proof"])
            self.assertEqual(summary["current_proof_blockers"], [])
            self.assertTrue(summary["runtime_launch_gate_ok"])
            self.assertEqual(summary["runtime_launch_gate_blockers"], [])
            self.assertFalse(summary["runtime_completion_gate_ok"])
            self.assertIn("runtime_completion_not_proven", summary["runtime_completion_gate_blockers"])
            self.assertFalse(summary["workflow_gate_ok"])
            self.assertIn("yaml_validation_not_proven", summary["workflow_gate_blockers"])

    def test_build_automation_summary_marks_preferred_live_model_proven_when_models_align(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "proof.json"
            receipt_path.write_text("{}", encoding="utf-8")
            recent = time.time() - 120
            os.utime(receipt_path, (recent, recent))

            doctor = {
                "summary": {
                    "chatdev_colony_health": True,
                    "chatdev_local_health": False,
                    "local_app_bootable": True,
                    "local_app_core_routes_ready": True,
                    "local_app_extended_routes_ready": True,
                    "live_surface_id": "devmentor-chatdev-worker",
                    "live_surface_kind": "queue_worker",
                    "gamedev_python_with_pygame": ["repo_gamedev_venv"],
                },
                "probes": {
                    "litellm": {"paths": {"/v1/models": {"ok": True}}},
                    "ollama": {"paths": {"/api/tags": {"ok": True}}},
                    "chatdev_colony": {
                        "paths": {
                            "/status": {
                                "json": {
                                    "backend": "litellm",
                                    "model": "ecosystem-coder-fast",
                                }
                            }
                        }
                    },
                },
            }
            latest = {
                "status": "artifact_emitted",
                "repo_root": r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke",
                "first_artifact_path": r"WareHouse\proof\code_workspace\game.py",
                "result_json": str(receipt_path),
                "runtime_python": r"C:\dev\active\ChatDev2\.venv-gamedev313\Scripts\python.exe",
                "artifact_runtime_outcome": "completed",
                "runtime_proof_depth": "completed",
                "runtime_launch_proven": True,
                "runtime_completion_proven": True,
                "yaml_file": r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml",
                "token_usage": {
                    "model_usages": {"ecosystem-coder-fast": {"total_tokens": 123}},
                    "call_history": [
                        {
                            "provider": "openai",
                            "model_name": "ecosystem-coder-fast",
                        }
                    ],
                },
            }
            yaml_validation = {"ok": True}
            assessment = _build_assessment(doctor, latest, yaml_validation)

            summary = _build_automation_summary(doctor, latest, yaml_validation, assessment)

            self.assertTrue(summary["preferred_live_model_matches_smoke"])
            self.assertTrue(summary["preferred_live_model_proven_for_smoke"])
            self.assertEqual(summary["advisories"], [])

    def test_build_automation_summary_surfaces_attempted_model_without_token_usage(self) -> None:
        doctor = {
            "summary": {
                "chatdev_colony_health": True,
                "chatdev_local_health": False,
                "local_app_bootable": True,
                "local_app_core_routes_ready": True,
                "local_app_extended_routes_ready": False,
                "live_surface_id": "devmentor-chatdev-worker",
                "live_surface_kind": "queue_worker",
                "gamedev_python_with_pygame": ["repo_gamedev_venv"],
            },
            "probes": {
                "litellm": {"paths": {"/v1/models": {"ok": True}}},
                "ollama": {"paths": {"/api/tags": {"ok": False}}},
            },
        }
        latest = {
            "status": "timeout_no_artifact",
            "yaml_file": r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml",
            "override_model": "ecosystem-devstral",
            "env_defaults": {
                "BASE_URL": "http://127.0.0.1:4000/v1",
                "API_KEY": "ollama-local-model",
            },
            "token_usage": {
                "model_usages": {},
                "call_history": [],
            },
        }
        yaml_validation = {"ok": True}
        assessment = _build_assessment(doctor, latest, yaml_validation)

        summary = _build_automation_summary(doctor, latest, yaml_validation, assessment)

        self.assertIsNone(summary["model"])
        self.assertIsNone(summary["proven_smoke_model"])
        self.assertEqual(summary["attempted_model"], "ecosystem-devstral")
        self.assertEqual(summary["env_defaults"]["BASE_URL"], "http://127.0.0.1:4000/v1")
        self.assertTrue(summary["smoke_attempted_without_model_call"])

    def test_status_json_honors_custom_receipt_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            (receipt_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "session_name": "status-proof",
                        "status": "artifact_emitted",
                        "bounded_stop_reason": "artifact_threshold_reached",
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    "tools/chatdev_gamedev_lane.ps1",
                    "status",
                    "-ReceiptDir",
                    str(receipt_dir),
                ],
                cwd="C:\\dev\\active\\ChatDev2",
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["latest_smoke"]["session_name"], "status-proof")
            self.assertEqual(payload["latest_smoke"]["status"], "artifact_emitted")
            self.assertEqual(payload["latest_smoke"]["bounded_stop_reason"], "artifact_threshold_reached")
            self.assertIn("doctor_summary", payload)
            self.assertIn("yaml_validation", payload)
            self.assertIn("assessment", payload)
            self.assertIn("automation_summary", payload)
            self.assertIn("callable", payload["automation_summary"])
            self.assertIn("callable_via", payload["automation_summary"])
            self.assertIn("full_devall_ready", payload["automation_summary"])
            self.assertIn("local_app_bootable", payload["automation_summary"])
            self.assertIn("local_app_core_routes_ready", payload["automation_summary"])
            self.assertIn("local_app_extended_routes_ready", payload["automation_summary"])
            self.assertIn("proof_generated_at", payload["automation_summary"])
            self.assertIn("proof_age_seconds", payload["automation_summary"])
            self.assertIn("proof_freshness", payload["automation_summary"])
            self.assertIn("proof_stale_after_seconds", payload["automation_summary"])
            self.assertIn("artifact_runtime_outcome", payload["automation_summary"])
            self.assertIn("runtime_proof_depth", payload["automation_summary"])
            self.assertIn("runtime_launch_proven", payload["automation_summary"])
            self.assertIn("runtime_completion_proven", payload["automation_summary"])
            self.assertIn("current_proof", payload["automation_summary"])
            self.assertIn("current_proof_blockers", payload["automation_summary"])
            self.assertIn("runtime_launch_gate_ok", payload["automation_summary"])
            self.assertIn("runtime_launch_gate_blockers", payload["automation_summary"])
            self.assertIn("runtime_completion_gate_ok", payload["automation_summary"])
            self.assertIn("runtime_completion_gate_blockers", payload["automation_summary"])
            self.assertIn("workflow_gate_ok", payload["automation_summary"])
            self.assertIn("workflow_gate_blockers", payload["automation_summary"])
            self.assertIn("workflow_execution", payload["automation_summary"])
            self.assertIn("proxy_health", payload["automation_summary"])
            self.assertIn("backend_requirements", payload["automation_summary"])
            self.assertIn("local_devall_proof", payload["automation_summary"])
            self.assertIn("operator_command", payload["automation_summary"]["local_devall_proof"])
            self.assertIn("proof_command", payload["automation_summary"]["local_devall_proof"])
            self.assertIn("operator_commands", payload["automation_summary"])
            self.assertIn("latest_summary", payload["automation_summary"]["operator_commands"])
            self.assertIn("status_compact", payload["automation_summary"]["operator_commands"])
            self.assertIn("status_full", payload["automation_summary"]["operator_commands"])
            self.assertIn("smoke_status_compact", payload["automation_summary"]["operator_commands"])

    def test_automation_summary_only_returns_compact_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_dir = Path(tmp)
            receipt_path = receipt_dir / "latest.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "session_name": "compact-proof",
                        "status": "artifact_emitted",
                        "bounded_stop_reason": "artifact_threshold_reached",
                        "repo_root": r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke",
                        "first_artifact_path": r"WareHouse\proof\code_workspace\game.py",
                        "yaml_file": r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml",
                        "runtime_python": r"C:\dev\active\ChatDev2\.venv-gamedev313\Scripts\python.exe",
                        "override_model": "ecosystem-devstral",
                        "env_defaults": {
                            "BASE_URL": "http://127.0.0.1:4000/v1",
                            "API_KEY": "ollama-local-model",
                        },
                        "artifact_runtime_outcome": "completed",
                        "runtime_proof_depth": "completed",
                        "runtime_launch_proven": True,
                        "runtime_completion_proven": True,
                        "token_usage": {
                            "model_usages": {"ecosystem-coder-fast": {"total_tokens": 123}},
                            "call_history": [
                                {
                                    "provider": "openai",
                                    "model_name": "ecosystem-coder-fast",
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "C:\\dev\\active\\ChatDev2\\.venv-gamedev313\\Scripts\\python.exe",
                    "tools\\chatdev_gamedev_status.py",
                    "--receipt-dir",
                    str(receipt_dir),
                    "--automation-summary-only",
                ],
                cwd="C:\\dev\\active\\ChatDev2",
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["contract_version"], 1)
            self.assertIn("callable", payload)
            self.assertIn("backend_requirements", payload)
            self.assertIn("local_devall_proof", payload)
            self.assertIn("currently_live_on_6400", payload["local_devall_proof"])
            self.assertIn("operator_commands", payload)
            self.assertIn("latest_summary", payload["operator_commands"])
            self.assertIn("status_compact", payload["operator_commands"])
            self.assertIn("status_full", payload["operator_commands"])
            self.assertIn("smoke_status_compact", payload["operator_commands"])
            self.assertFalse(payload["backend_requirements"]["ollama_required_for_current_lane"])
            self.assertEqual(payload["workflow_used"], r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml")
            self.assertEqual(payload["provider"], "openai")
            self.assertEqual(payload["model"], "ecosystem-coder-fast")
            self.assertEqual(payload["attempted_model"], "ecosystem-devstral")
            self.assertEqual(payload["env_defaults"]["API_KEY"], "ollama-local-model")
            self.assertEqual(
                payload["output_path"],
                r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\proof\code_workspace\game.py",
            )
            self.assertEqual(payload["result_json"], str(receipt_path))
            self.assertNotIn("latest_smoke", payload)


if __name__ == "__main__":
    unittest.main()
