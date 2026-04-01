from pathlib import Path

from src.integration.chatdev_launcher import ChatDevLauncher


def test_chatdev_resolve_and_validate(tmp_path: Path, monkeypatch):
    # Create a fake ChatDev installation with run.py
    chatdev_dir = tmp_path / "chatdev"
    chatdev_dir.mkdir()
    (chatdev_dir / "run.py").write_text("print('hello')")

    monkeypatch.setenv("CHATDEV_PATH", str(chatdev_dir))

    launcher = ChatDevLauncher()
    assert str(launcher.chatdev_path) == str(chatdev_dir)


def test_chatdev_shadow_runtime_when_warehouse_not_writable(tmp_path: Path, monkeypatch):
    chatdev_dir = tmp_path / "chatdev_ro"
    chatdev_dir.mkdir()
    (chatdev_dir / "run.py").write_text("print('hello')", encoding="utf-8")

    monkeypatch.setenv("CHATDEV_PATH", str(chatdev_dir))
    monkeypatch.setattr("src.integration.chatdev_launcher.repo_root", tmp_path)

    def fake_probe(self: ChatDevLauncher, root: Path) -> tuple[bool, str]:
        if root == chatdev_dir:
            return False, "permission denied"
        return True, "ok"

    def fake_copytree(src: Path, dst: Path, **_: object) -> str:
        dst_path = Path(dst)
        dst_path.mkdir(parents=True, exist_ok=True)
        (dst_path / "run.py").write_text("print('shadow')", encoding="utf-8")
        return str(dst_path)

    monkeypatch.setattr(ChatDevLauncher, "_probe_warehouse_writable", fake_probe)
    monkeypatch.setattr("src.integration.chatdev_launcher.shutil.copytree", fake_copytree)

    launcher = ChatDevLauncher()
    assert launcher.chatdev_path == (tmp_path / "state" / "runtime" / "chatdev_shadow")
