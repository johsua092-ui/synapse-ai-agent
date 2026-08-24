from pathlib import Path


def test_windows_native_install_path_docs_match_installer() -> None:
    doc = Path("website/docs/user-guide/windows-native.md").read_text()
    install = Path("scripts/install.ps1").read_text()

    # The launchers live in the managed binary dir OUTSIDE the git checkout
    # (SYNAPSE_HOME\bin, next to the managed uv) — NOT the whole venv\Scripts
    # (which would shadow the user's python, #83797) and NOT a dir inside
    # the checkout (which `synapse update`'s autostash swept off disk).
    assert "%LOCALAPPDATA%\\synapse\\bin" in doc
    assert (
        "Get-Command synapse        # should print "
        "C:\\Users\\<you>\\AppData\\Local\\synapse\\bin\\synapse.exe"
    ) in doc
    # Installer exposes $SynapseHome\bin, and must copy the launchers into it.
    assert '$synapseBin = "$SynapseHome\\bin"' in install
    assert "synapse.exe" in install and "synapse-acp.exe" in install
    # Guard against regressions to either legacy layout.
    assert '$synapseBin = "$InstallDir\\venv\\Scripts"' not in install
    assert '$synapseBin = "$InstallDir\\bin"' not in install
