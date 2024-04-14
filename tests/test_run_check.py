from click.testing import CliRunner
from nanodjango.commands import cli


def test_run_check():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "../examples/counter.py", "check"])
    assert result.exit_code == 0
    print(result.output)
