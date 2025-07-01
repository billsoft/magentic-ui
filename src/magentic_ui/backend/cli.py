import os
import warnings
import typer
import uvicorn
import docker
from typing_extensions import Annotated
from typing import Optional
from pathlib import Path
import logging

from ..version import VERSION
from .._docker import (
    check_docker_running,
    check_browser_image,
    check_python_image,
    build_browser_image,
    build_python_image,
    get_docker_system_info,
    check_docker_image_health,
    clean_corrupted_image,
)

# Configure basic logging to show only errors
logging.basicConfig(level=logging.ERROR)

# Create a Typer application instance with a descriptive help message
# This is the main entry point for CLI commands
app = typer.Typer(help="Magentic-UI: A human-centered interface for web agents.")

# Ignore deprecation warnings from websockets
warnings.filterwarnings("ignore", message="websockets.legacy is deprecated*")
warnings.filterwarnings(
    "ignore", message="websockets.server.WebSocketServerProtocol is deprecated*"
)

# Ignore warnings about ffmpeg or avconv not being found
# Audio is not used in the UI, so we can ignore this warning
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg or avconv*")


def get_env_file_path():
    """
    Create a temporary environment file path in the user's home directory.
    Used to pass environment variables to Uvicorn workers.

    Returns:
        str: The full path to the temporary environment file
    """
    app_dir = os.path.join(os.path.expanduser("~"), ".magentic_ui")
    if not os.path.exists(app_dir):
        os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "temp_env_vars.env")


# This decorator makes this function the default action when no subcommand is provided
# invoke_without_command=True means this function runs automatically when only 'magentic-ui' is typed
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,  # Typer context provides information about the command invocation
    host: str = typer.Option("127.0.0.1", help="Host to run the UI on."),
    port: int = typer.Option(8081, help="Port to run the UI on."),
    workers: int = typer.Option(1, help="Number of workers to run the UI with."),
    reload: Annotated[
        bool, typer.Option("--reload", help="Reload the UI on code changes.")
    ] = False,
    docs: bool = typer.Option(True, help="Whether to generate API docs."),
    appdir: str = typer.Option(
        str(Path.home() / ".magentic_ui"),
        help="Path to the app directory where files are stored.",
    ),
    database_uri: Optional[str] = typer.Option(
        None, "--database-uri", help="Database URI to connect to."
    ),
    upgrade_database: bool = typer.Option(
        False, "--upgrade-database", help="Upgrade the database schema on startup."
    ),
    config: Optional[str] = typer.Option(
        None, "--config", help="Path to the config file."
    ),
    rebuild_docker: Optional[bool] = typer.Option(
        False, "--rebuild-docker", help="Rebuild the docker images before starting."
    ),
    version: bool = typer.Option(
        False, "--version", help="Print the version of Magentic-UI and exit."
    ),
    run_without_docker: Annotated[
        bool,
        typer.Option(
            "--run-without-docker",
            help="Run without docker. This will remove coder and filesurfer agents and disable live browser view.",
        ),
    ] = False,
):
    """
    Magentic-UI: A human-centered interface for web agents.

    Run `magentic-ui` to start the application.
    """
    # Check if version flag was provided
    if version:
        typer.echo(f"Magentic-UI version: {VERSION}")
        raise typer.Exit()

    # This conditional checks if a subcommand was provided
    # If no subcommand was specified (e.g., just 'magentic-ui'), run the UI
    if ctx.invoked_subcommand is None:
        run_ui(
            host=host,
            port=port,
            workers=workers,
            reload=reload,
            docs=docs,
            appdir=appdir,
            database_uri=database_uri,
            upgrade_database=upgrade_database,
            config=config,
            rebuild_docker=rebuild_docker,
            run_without_docker=run_without_docker,
        )


def run_ui(
    host: str,
    port: int,
    workers: int,
    reload: bool,
    docs: bool,
    appdir: str,
    database_uri: Optional[str],
    upgrade_database: bool,
    config: Optional[str],
    rebuild_docker: Optional[bool],
    run_without_docker: bool,
):
    """
    Core logic to run the Magentic-UI web application.
    This function is used by both the main entry point and the legacy 'ui' command.

    Args:
        host (str, optional): Host to run the UI on. Defaults to 127.0.0.1 (localhost).
        port (int, optional): Port to run the UI on. Defaults to 8081.
        workers (int, optional): Number of workers to run the UI with. Defaults to 1.
        reload (bool, optional): Whether to reload the UI on code changes. Defaults to False.
        docs (bool, optional): Whether to generate API docs. Defaults to True.
        appdir (str, optional): Path to the app directory where files are stored. Defaults to ~/.magentic_ui.
        database_uri (str, optional): Database URI to connect to. Defaults to None.
        upgrade_database (bool, optional): Whether to upgrade the database schema. Defaults to False.
        config (str, optional): Path to the config file. Defaults to config.yaml if present.
        rebuild_docker (bool, optional): Rebuild the docker images. Defaults to False.
        run_without_docker (bool, optional): Run without docker. This will remove coder and filesurfer agents and disale live browser view. Defaults to False.
    """
    # Display a green, bold "Starting Magentic-UI" message
    typer.echo(typer.style("Starting Magentic-UI", fg=typer.colors.GREEN, bold=True))

    # === 增强的Docker设置 ===
    if not run_without_docker:
        typer.echo("检查Docker运行状态...", nl=False)

        if not check_docker_running():
            typer.echo(typer.style("失败\n", fg=typer.colors.RED, bold=True))
            typer.echo("Docker未运行。请启动Docker后重试。")
            
            # 提供诊断信息
            typer.echo("\n💡 故障排除建议:")
            typer.echo("1. 确保Docker Desktop已启动")
            typer.echo("2. 检查Docker状态: docker --version")
            typer.echo("3. 参考 TROUBLESHOOTING.md 获取更多帮助")
            
            raise typer.Exit(1)
        else:
            typer.echo(typer.style("正常", fg=typer.colors.GREEN, bold=True))

        # 获取Docker客户端（复用连接）
        try:
            docker_client = docker.from_env()
            docker_info = get_docker_system_info()
            typer.echo(f"Docker版本: {docker_info.get('server_version', 'unknown')}")
        except Exception as e:
            typer.echo(typer.style(f"Docker连接错误: {e}", fg=typer.colors.RED))
            raise typer.Exit(1)

        # 增强的浏览器镜像检查
        typer.echo("检查Docker VNC浏览器镜像...", nl=False)
        browser_healthy = check_browser_image(docker_client)
        
        if not browser_healthy or rebuild_docker:
            if not browser_healthy:
                typer.echo(typer.style("需要修复\n", fg=typer.colors.YELLOW, bold=True))
                typer.echo("🔧 检测到镜像问题，正在重建VNC浏览器镜像...")
            else:
                typer.echo(typer.style("更新中\n", fg=typer.colors.YELLOW, bold=True))
                typer.echo("🏗️ 构建Docker VNC镜像（需要几分钟时间）")
            
            try:
                build_browser_image(docker_client)
                typer.echo("✅ VNC浏览器镜像构建完成")
            except Exception as e:
                typer.echo(typer.style(f"❌ 镜像构建失败: {e}", fg=typer.colors.RED))
                typer.echo("\n🛠️ 建议的修复步骤:")
                typer.echo("1. 运行: docker system prune -a")
                typer.echo("2. 重启Docker Desktop")
                typer.echo("3. 重新运行此命令")
                typer.echo("4. 如问题持续，请查看 TROUBLESHOOTING.md")
                raise typer.Exit(1)
        else:
            typer.echo(typer.style("正常", fg=typer.colors.GREEN, bold=True))

        # 增强的Python镜像检查
        typer.echo("检查Docker Python镜像...", nl=False)
        python_healthy = check_python_image(docker_client)
        
        if not python_healthy or rebuild_docker:
            if not python_healthy:
                typer.echo(typer.style("需要修复\n", fg=typer.colors.YELLOW, bold=True))
                typer.echo("🔧 检测到镜像问题，正在重建Python环境镜像...")
            else:
                typer.echo(typer.style("更新中\n", fg=typer.colors.YELLOW, bold=True))
                typer.echo("🏗️ 构建Docker Python镜像（需要几分钟时间）")
            
            try:
                build_python_image(docker_client)
                typer.echo("✅ Python环境镜像构建完成")
            except Exception as e:
                typer.echo(typer.style(f"❌ 镜像构建失败: {e}", fg=typer.colors.RED))
                typer.echo("\n🛠️ 建议的修复步骤:")
                typer.echo("1. 运行: docker system prune -a")
                typer.echo("2. 重启Docker Desktop")
                typer.echo("3. 重新运行此命令")
                raise typer.Exit(1)
        else:
            typer.echo(typer.style("正常", fg=typer.colors.GREEN, bold=True))

        # 最终验证
        if not check_browser_image(docker_client) or not check_python_image(docker_client):
            typer.echo(typer.style("❌ Docker镜像验证失败", fg=typer.colors.RED, bold=True))
            typer.echo("请运行以下命令进行诊断: magentic-ui doctor")
            raise typer.Exit(1)
        else:
            typer.echo("✅ 所有Docker镜像准备就绪")
    else:
        typer.echo(
            typer.style(
                "Running without docker... This will remove the live browser view and will disable code and file manipulation.",
                fg=typer.colors.YELLOW,
                bold=True,
            )
        )
        typer.echo(
            typer.style(
                "For the full experience of Magentic-UI please use docker.",
                fg=typer.colors.YELLOW,
                bold=True,
            )
        )

    typer.echo("Launching Web Application...")

    # === Environment Setup ===
    # Create environment variables to pass to the web application
    env_vars = {
        "_HOST": host,
        "_PORT": port,
        "_API_DOCS": str(docs),
    }

    # Add optional environment variables
    if appdir:
        env_vars["_APPDIR"] = appdir
    if database_uri:
        env_vars["DATABASE_URI"] = database_uri
    if upgrade_database:
        env_vars["_UPGRADE_DATABASE"] = "1"

    # ✅ 关键修复：传递API密钥环境变量到运行时
    # 确保API密钥环境变量能够传递到Uvicorn进程中
    api_key_vars = ["OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY"]
    for api_key_var in api_key_vars:
        api_key_value = os.getenv(api_key_var)
        if api_key_value:
            env_vars[api_key_var] = api_key_value
            typer.echo(f"✅ 传递API密钥环境变量: {api_key_var}={api_key_value[:10]}...")
        else:
            typer.echo(f"⚠️ 未找到环境变量: {api_key_var}")
    
    # 传递所有以_API_KEY结尾的环境变量（通用支持）
    for key, value in os.environ.items():
        if key.endswith("_API_KEY") and key not in env_vars:
            env_vars[key] = value
            typer.echo(f"✅ 传递通用API密钥: {key}={value[:10]}...")
    
    if not any(key.endswith("_API_KEY") for key in env_vars):
        typer.echo(typer.style("⚠️ 警告: 未检测到任何API密钥环境变量", fg=typer.colors.YELLOW, bold=True))
        typer.echo("请确保在.env文件中设置了正确的API密钥")

    # Set Docker-related environment variables
    env_vars["INSIDE_DOCKER"] = "0"
    env_vars["EXTERNAL_WORKSPACE_ROOT"] = appdir
    env_vars["INTERNAL_WORKSPACE_ROOT"] = appdir
    env_vars["RUN_WITHOUT_DOCKER"] = str(run_without_docker)

    # Handle configuration file path
    if not config:
        # Look for config.yaml in the current directory if not specified
        if os.path.isfile("config.yaml"):
            config = "config.yaml"
        else:
            typer.echo("Config file not provided. Using default settings.")
    if config:
        env_vars["_CONFIG"] = config

    # Create a temporary environment file to share with Uvicorn workers
    env_file_path = get_env_file_path()
    with open(env_file_path, "w") as temp_env:
        for key, value in env_vars.items():
            temp_env.write(f"{key}={value}\n")

    # Start the Uvicorn server with the configured settings
    uvicorn.run(
        "magentic_ui.backend.web.app:app",  # Path to the ASGI application
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        reload_excludes=["**/alembic/*", "**/alembic.ini", "**/versions/*"]
        if reload
        else None,
        env_file=env_file_path,  # Pass environment variables via file
    )


# This command is hidden from help to encourage using the new syntax
# but kept for backward compatibility with existing scripts and documentation
@app.command(hidden=True)
def ui(
    host: str = "127.0.0.1",
    port: int = 8081,
    workers: int = 1,
    reload: Annotated[bool, typer.Option("--reload")] = False,
    docs: bool = True,
    appdir: str = str(Path.home() / ".magentic_ui"),
    database_uri: Optional[str] = None,
    upgrade_database: bool = False,
    config: Optional[str] = None,
    rebuild_docker: Optional[bool] = False,
    run_without_docker: Annotated[
        bool,
        typer.Option(
            "--run-without-docker",
            help="Run without docker. This will remove coder and filesurfer agents and disale live browser view.",
        ),
    ] = False,
):
    """
    [Deprecated] Run Magentic-UI.
    This command is kept for backward compatibility.
    """
    # Simply delegate to the main run_ui function with the same parameters
    run_ui(
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        docs=docs,
        appdir=appdir,
        database_uri=database_uri,
        upgrade_database=upgrade_database,
        config=config,
        rebuild_docker=rebuild_docker,
        run_without_docker=run_without_docker,
    )


# Keep the version command for backward compatibility but hide it from help
@app.command(hidden=True)
def version():
    """
    Print the version of the Magentic-UI backend CLI.
    """
    typer.echo(f"Magentic-UI version: {VERSION}")


@app.command(hidden=True)
def help():
    """
    Show help information about available commands and options.
    """
    # Use a system call to run the command with --help
    import subprocess
    import sys
    import os

    # Get the command that was used to run this script
    command = os.path.basename(sys.argv[0])

    # If running directly as a module, use the appropriate command name
    if command == "python" or command == "python3":
        command = "magentic-ui"

    # Run the command with --help
    try:
        subprocess.run([command, "--help"])
    except FileNotFoundError:
        # Fallback if the command isn't found in PATH
        typer.echo(f"Error: Command '{command}' not found in PATH.")
        typer.echo(f"For more information, run `{command} --help`")


@app.command()
def doctor():
    """诊断Magentic-UI Docker环境问题"""
    typer.echo(typer.style("🔍 Magentic-UI 环境诊断", fg=typer.colors.BLUE, bold=True))
    typer.echo("=" * 50)
    
    # 检查Docker基础状态
    typer.echo("1. 检查Docker运行状态...", nl=False)
    if check_docker_running():
        typer.echo(typer.style("✅ 正常", fg=typer.colors.GREEN))
    else:
        typer.echo(typer.style("❌ Docker未运行", fg=typer.colors.RED))
        typer.echo("   请启动Docker Desktop后重试")
        return
    
    # 获取Docker系统信息
    docker_info = get_docker_system_info()
    if 'error' not in docker_info:
        typer.echo("2. Docker系统信息:")
        typer.echo(f"   版本: {docker_info['server_version']}")
        typer.echo(f"   存储驱动: {docker_info['storage_driver']}")
        typer.echo(f"   镜像数量: {docker_info['images_count']}")
        typer.echo(f"   容器数量: {docker_info['containers_count']}")
    else:
        typer.echo(f"   ⚠️ 获取信息失败: {docker_info['error']}")
    
    # 检查具体镜像
    try:
        client = docker.from_env()
        
        typer.echo("3. 检查Magentic-UI镜像:")
        from .._docker import VNC_BROWSER_IMAGE, PYTHON_IMAGE
        for image_name in [VNC_BROWSER_IMAGE, PYTHON_IMAGE]:
            typer.echo(f"   {image_name}...", nl=False)
            exists, healthy, status = check_docker_image_health(image_name, client)
            
            if exists and healthy:
                typer.echo(typer.style("✅ 正常", fg=typer.colors.GREEN))
            elif exists and not healthy:
                typer.echo(typer.style(f"⚠️ 异常: {status}", fg=typer.colors.YELLOW))
            else:
                typer.echo(typer.style("❌ 不存在", fg=typer.colors.RED))
        
    except Exception as e:
        typer.echo(f"   ❌ 检查失败: {e}")
    
    typer.echo("\n💡 如果发现问题，请运行: magentic-ui fix-docker")


@app.command(name="fix-docker")
def fix_docker():
    """修复Docker镜像问题"""
    typer.echo(typer.style("🔧 修复Magentic-UI Docker环境", fg=typer.colors.BLUE, bold=True))
    typer.echo("=" * 50)
    
    if not check_docker_running():
        typer.echo("❌ Docker未运行，请先启动Docker")
        return
    
    try:
        client = docker.from_env()
        
        # 清理损坏的镜像
        typer.echo("1. 清理可能损坏的镜像...")
        from .._docker import VNC_BROWSER_IMAGE, PYTHON_IMAGE
        for image_name in [VNC_BROWSER_IMAGE, PYTHON_IMAGE]:
            if clean_corrupted_image(image_name, client):
                typer.echo(f"   ✅ 已清理: {image_name}")
            else:
                typer.echo(f"   ℹ️ 跳过: {image_name}")
        
        # 清理Docker系统缓存
        typer.echo("2. 清理Docker构建缓存...")
        try:
            client.api.prune_builds()  # type: ignore
            typer.echo("   ✅ 构建缓存已清理")
        except Exception as e:
            typer.echo(f"   ⚠️ 清理缓存失败: {e}")
        
        # 重建镜像
        typer.echo("3. 重建镜像...")
        typer.echo("   这可能需要几分钟时间，请耐心等待...")
        
        try:
            build_browser_image(client)
            typer.echo("   ✅ VNC浏览器镜像重建完成")
        except Exception as e:
            typer.echo(f"   ❌ VNC浏览器镜像重建失败: {e}")
        
        try:
            build_python_image(client)
            typer.echo("   ✅ Python环境镜像重建完成")
        except Exception as e:
            typer.echo(f"   ❌ Python环境镜像重建失败: {e}")
        
        typer.echo("\n✅ 修复完成！现在可以运行: magentic-ui --port 8081")
        
    except Exception as e:
        typer.echo(f"❌ 修复过程出错: {e}")
        typer.echo("\n🛠️ 手动修复建议:")
        typer.echo("1. docker system prune -a --volumes")
        typer.echo("2. 重启Docker Desktop")
        typer.echo("3. 重新运行此命令")


@app.command(name="clean-docker")
def clean_docker():
    """完全清理Magentic-UI相关的Docker资源"""
    typer.echo(typer.style("⚠️ 警告: 这将删除所有Magentic-UI相关的Docker资源", fg=typer.colors.YELLOW, bold=True))
    
    if not typer.confirm("是否继续？"):
        typer.echo("操作已取消")
        return
    
    try:
        client = docker.from_env()
        
        # 停止相关容器
        typer.echo("1. 停止相关容器...")
        from .._docker import VNC_BROWSER_IMAGE, PYTHON_IMAGE
        for image_name in [VNC_BROWSER_IMAGE, PYTHON_IMAGE]:
            containers = client.containers.list(all=True, filters={"ancestor": image_name})  # type: ignore
            for container in containers:
                container.stop()  # type: ignore
                container.remove()  # type: ignore
                typer.echo(f"   ✅ 已移除容器: {container.short_id}")  # type: ignore
        
        # 删除镜像
        typer.echo("2. 删除镜像...")
        for image_name in [VNC_BROWSER_IMAGE, PYTHON_IMAGE]:
            try:
                client.images.remove(image_name, force=True)  # type: ignore
                typer.echo(f"   ✅ 已删除镜像: {image_name}")
            except Exception as e:
                typer.echo(f"   ℹ️ 镜像不存在或已删除: {image_name}")
        
        # 清理系统
        typer.echo("3. 清理系统缓存...")
        client.api.prune_builds()  # type: ignore
        client.api.prune_images(filters={"dangling": True})  # type: ignore
        
        typer.echo("✅ 清理完成！")
        typer.echo("💡 下次启动时将自动重建镜像")
        
    except Exception as e:
        typer.echo(f"❌ 清理失败: {e}")


def run():
    """
    Main entry point called by the 'magentic' and 'magentic-ui' commands.
    This function is referenced in pyproject.toml's [project.scripts] section.
    """
    app()  # Hand control to the Typer application


if __name__ == "__main__":
    app()  # Allow running this file directly with 'python -m magentic_ui.backend.cli'
