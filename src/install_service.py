"""Registra o Mercado Livre Tracker como tarefa agendada do Windows."""

import subprocess
import sys
from pathlib import Path

TASK_NAME = "MLPriceTracker"
SCRIPT_NAME = "scheduler.py"


def get_paths() -> tuple[Path, Path, Path]:
    project_dir = Path(__file__).parent.parent
    script_path = project_dir / "src" / SCRIPT_NAME

    # pythonw.exe = sem janela de console
    python_path = Path(sys.executable).parent / "pythonw.exe"

    return python_path, script_path, project_dir


def install_task() -> bool:
    """Cria tarefa que inicia na inicialização do usuário."""
    python_path, script_path, working_dir = get_paths()

    xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Monitor de preços do Mercado Livre - Executa a cada 30min</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT1M</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT5M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>-m src.scheduler</Arguments>
      <WorkingDirectory>{working_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    xml_path = working_dir / "task_config.xml"
    xml_path.write_text(xml_content, encoding="utf-16")

    try:
        cmd = [
            "schtasks",
            "/Create",
            "/TN",
            TASK_NAME,
            "/XML",
            str(xml_path),
            "/F",
        ]

        print(f"📝 Registrando tarefa: {TASK_NAME}")
        print(f"🐍 Python: {python_path}")
        print(f"📜 Script: {script_path}")
        print(f"📁 Pasta: {working_dir}")
        print()

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Tarefa registrada com sucesso!")
            print(f"   A tarefa iniciará automaticamente após o login.")
            print()
            print("⏱️  Comandos úteis:")
            print(f"   Iniciar agora: schtasks /Run /TN {TASK_NAME}")
            print(f"   Parar:         schtasks /End /TN {TASK_NAME}")
            print(f"   Status:        schtasks /Query /TN {TASK_NAME} /V /FO LIST")
            print(f"   Remover:       python -m src.install_service uninstall")
            return True
        else:
            print(f"❌ Erro ao registrar: {result.stderr}")
            print("💡 Execute como Administrador se o erro for de permissão.")
            return False
    finally:
        if xml_path.exists():
            xml_path.unlink()


def uninstall_task() -> bool:
    """Remove a tarefa agendada."""
    cmd = ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]

    print(f"🗑️  Removendo tarefa: {TASK_NAME}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Tarefa '{TASK_NAME}' removida com sucesso!")
        return True
    else:
        print(f"❌ Erro: {result.stderr}")
        return False


def check_task() -> bool:
    """Verifica se a tarefa existe e mostra seu status."""
    cmd = ["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Tarefa '{TASK_NAME}' está registrada\n")
        # Filtra informações relevantes
        for line in result.stdout.split("\n"):
            if any(
                key in line
                for key in [
                    "Status:",
                    "Last Run Time:",
                    "Next Run Time:",
                    "Last Result:",
                    "TaskName:",
                    "Author:",
                ]
            ):
                print(line.strip())
        return True
    else:
        print(f"❌ Tarefa '{TASK_NAME}' não encontrada")
        return False


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m src.install_service [install|uninstall|check|run]")
        print("  install   - Registra o tracker para iniciar com o Windows")
        print("  uninstall - Remove o tracker da inicialização")
        print("  check     - Verifica status da tarefa")
        print("  run       - Inicia o tracker manualmente agora")
        return

    action = sys.argv[1].lower()

    if action == "install":
        install_task()
    elif action == "uninstall":
        uninstall_task()
    elif action == "check":
        check_task()
    elif action == "run":
        # Inicia a tarefa manualmente
        cmd = ["schtasks", "/Run", "/TN", TASK_NAME]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"🚀 Tarefa '{TASK_NAME}' iniciada!")
        else:
            print(f"❌ Erro: {result.stderr}")
    else:
        print(f"Ação desconhecida: {action}")


if __name__ == "__main__":
    main()
