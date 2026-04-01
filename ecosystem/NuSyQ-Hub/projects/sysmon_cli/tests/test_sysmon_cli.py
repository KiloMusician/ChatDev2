from sysmon_cli import SysMonCli


def test_cpu_usage():
    """Test CPU usage functionality."""
    cli = SysMonCli()
    cpu_usage = cli.get_cpu_usage()
    assert isinstance(cpu_usage, float)
    assert 0 <= cpu_usage <= 100


def test_memory_usage():
    """Test memory usage functionality."""
    cli = SysMonCli()
    memory_usage = cli.get_memory_usage()
    assert isinstance(memory_usage, float)
    assert 0 <= memory_usage <= 100


def test_disk_usage():
    """Test disk usage functionality."""
    cli = SysMonCli()
    disk_usage = cli.get_disk_usage()
    assert isinstance(disk_usage, float)
    assert 0 <= disk_usage <= 100


def test_network_usage():
    """Test network usage functionality."""
    cli = SysMonCli()
    network_usage = cli.get_network_usage()
    assert isinstance(network_usage, float)
    assert 0 <= network_usage <= 100


def test_cpu_count():
    """Test CPU count functionality."""
    cli = SysMonCli()
    cpu_count = cli.get_cpu_count()
    assert isinstance(cpu_count, int)
    assert cpu_count > 0


def test_memory_size():
    """Test memory size functionality."""
    cli = SysMonCli()
    memory_size = cli.get_memory_size()
    assert isinstance(memory_size, int)
    assert memory_size > 0


def test_disk_space():
    """Test disk space functionality."""
    cli = SysMonCli()
    disk_space = cli.get_disk_space()
    assert isinstance(disk_space, float)
    assert disk_space > 0


def test_network_speed():
    """Test network speed functionality."""
    cli = SysMonCli()
    network_speed = cli.get_network_speed()
    assert isinstance(network_speed, float)
    assert network_speed > 0
