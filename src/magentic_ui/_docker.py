import docker
import os
import sys
import time
import logging
from typing import Tuple, Optional, Dict, Any
from docker.errors import DockerException, ImageNotFound, APIError

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
VNC_BROWSER_IMAGE = "magentic-ui-vnc-browser"
PYTHON_IMAGE = "magentic-ui-python-env"

VNC_BROWSER_BUILD_CONTEXT = "magentic-ui-browser-docker"
PYTHON_BUILD_CONTEXT = "magentic-ui-python-env"

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_docker_running() -> bool:
    """检查Docker是否运行"""
    try:
        client = docker.from_env()
        client.ping()  # type: ignore
        return True
    except (DockerException, ConnectionError) as e:
        logger.error(f"Docker连接失败: {e}")
        return False


def build_image_with_progress(
    image_name: str, build_context: str, client: docker.DockerClient
) -> None:
    """构建镜像并显示进度"""
    logger.info(f"开始构建镜像: {image_name}")
    
    try:
        for segment in client.api.build(
            path=build_context,
            dockerfile="Dockerfile",
            rm=True,
            tag=image_name,
            decode=True,
            pull=True,  # 确保使用最新基础镜像
        ):
            if "stream" in segment:
                lines = segment["stream"].splitlines()
                for line in lines:
                    if line.strip():
                        print(line.strip())
                sys.stdout.flush()
            elif "error" in segment:
                raise Exception(f"构建错误: {segment['error']}")
                        
        logger.info(f"✅ 镜像构建完成: {image_name}")
        
    except Exception as e:
        logger.error(f"❌ 镜像构建失败 {image_name}: {e}")
        raise


def check_docker_image_health(image_name: str, client: docker.DockerClient) -> Tuple[bool, bool, str]:
    """
    检查Docker镜像健康状态
    返回: (镜像存在, 镜像健康, 状态信息)
    """
    try:
        image = client.images.get(image_name)
        
        # 检查镜像完整性
        try:
            # 尝试获取镜像详细信息
            image.reload()
            return True, True, "镜像正常"
        except Exception as e:
            logger.warning(f"镜像 {image_name} 可能损坏: {e}")
            return True, False, f"镜像损坏: {str(e)}"
            
    except ImageNotFound:
        return False, False, "镜像不存在"
    except APIError as e:
        if "500" in str(e) or "Internal Server Error" in str(e):
            logger.error(f"检测到Docker存储错误: {e}")
            return True, False, f"存储错误: {str(e)}"
        return False, False, f"API错误: {str(e)}"
    except Exception as e:
        logger.error(f"未知错误: {e}")
        return False, False, f"未知错误: {str(e)}"


def clean_corrupted_image(image_name: str, client: docker.DockerClient) -> bool:
    """清理损坏的镜像"""
    try:
        logger.info(f"清理损坏的镜像: {image_name}")
        
        # 尝试强制删除镜像
        client.images.remove(image_name, force=True)  # type: ignore
        logger.info(f"✅ 已删除损坏镜像: {image_name}")
        
        # 清理相关的构建缓存
        try:
            client.api.prune_builds()
        except:
            pass  # 忽略清理缓存的错误
        
        return True
    except Exception as e:
        logger.warning(f"清理镜像失败 {image_name}: {e}")
        return False


def build_image_with_retry(
    image_name: str, 
    build_context: str, 
    client: docker.DockerClient, 
    max_retries: int = 2
) -> bool:
    """带重试机制的镜像构建"""
    
    for attempt in range(max_retries):
        try:
            logger.info(f"构建尝试 {attempt + 1}/{max_retries}: {image_name}")
            
            # 在重试前清理可能存在的损坏镜像
            if attempt > 0:
                clean_corrupted_image(image_name.replace(":latest", ""), client)
                time.sleep(2)  # 等待清理完成
            
            build_image_with_progress(image_name, build_context, client)
            
            # 验证构建结果
            exists, healthy, status = check_docker_image_health(image_name.replace(":latest", ""), client)
            if exists and healthy:
                logger.info(f"✅ 镜像构建并验证成功: {image_name}")
                return True
            else:
                logger.warning(f"构建完成但验证失败: {status}")
                if attempt < max_retries - 1:
                    continue
                    
        except Exception as e:
            logger.error(f"构建失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise e
            
            # 重试前的清理工作
            try:
                client.api.prune_builds()
                time.sleep(1)
            except:
                pass
    
    return False


# 保持原有函数签名的兼容性
def build_image(image_name: str, build_context: str, client: docker.DockerClient) -> None:
    """构建镜像（兼容性函数）"""
    build_image_with_progress(image_name, build_context, client)


def build_browser_image(client: Optional[docker.DockerClient] = None) -> None:
    """构建浏览器镜像"""
    if client is None:
        client = docker.from_env()
    
    build_context = os.path.join(_PACKAGE_DIR, "docker", VNC_BROWSER_BUILD_CONTEXT)
    
    if not build_image_with_retry(
        VNC_BROWSER_IMAGE + ":latest",
        build_context,
        client
    ):
        raise Exception(f"无法构建 {VNC_BROWSER_IMAGE} 镜像")


def build_python_image(client: Optional[docker.DockerClient] = None) -> None:
    """构建Python环境镜像"""
    if client is None:
        client = docker.from_env()
    
    build_context = os.path.join(_PACKAGE_DIR, "docker", PYTHON_BUILD_CONTEXT)
    
    if not build_image_with_retry(
        PYTHON_IMAGE + ":latest",
        build_context,
        client
    ):
        raise Exception(f"无法构建 {PYTHON_IMAGE} 镜像")


def check_docker_access() -> bool:
    """检查Docker访问权限"""
    try:
        client = docker.from_env()
        client.ping()  # type: ignore
        return True
    except DockerException as e:
        logger.error(f"无法访问Docker: {e}")
        logger.error("请参考 TROUBLESHOOTING.md 文档获取解决方案")
        return False


# 保持原有函数签名的兼容性
def check_docker_image(image_name: str, client: docker.DockerClient) -> bool:
    """检查Docker镜像是否存在（兼容性函数）"""
    exists, healthy, _ = check_docker_image_health(image_name, client)
    return exists and healthy


def check_browser_image(client: Optional[docker.DockerClient] = None) -> bool:
    """检查浏览器镜像状态"""
    if not check_docker_access():
        return False
    
    if client is None:
        client = docker.from_env()
    
    exists, healthy, status = check_docker_image_health(VNC_BROWSER_IMAGE, client)
    
    if not exists:
        logger.info(f"浏览器镜像不存在: {VNC_BROWSER_IMAGE}")
        return False
    elif not healthy:
        logger.warning(f"浏览器镜像不健康: {status}")
        # 尝试清理损坏的镜像
        clean_corrupted_image(VNC_BROWSER_IMAGE, client)
        return False
    
    logger.info(f"✅ 浏览器镜像正常: {VNC_BROWSER_IMAGE}")
    return True


def check_python_image(client: Optional[docker.DockerClient] = None) -> bool:
    """检查Python镜像状态"""
    if not check_docker_access():
        return False
    
    if client is None:
        client = docker.from_env()
    
    exists, healthy, status = check_docker_image_health(PYTHON_IMAGE, client)
    
    if not exists:
        logger.info(f"Python镜像不存在: {PYTHON_IMAGE}")
        return False
    elif not healthy:
        logger.warning(f"Python镜像不健康: {status}")
        # 尝试清理损坏的镜像
        clean_corrupted_image(PYTHON_IMAGE, client)
        return False
    
    logger.info(f"✅ Python镜像正常: {PYTHON_IMAGE}")
    return True


def get_docker_system_info() -> Dict[str, Any]:
    """获取Docker系统信息用于诊断"""
    try:
        client = docker.from_env()
        info = client.info()  # type: ignore
        return {
            'server_version': info.get('ServerVersion', 'unknown'),  # type: ignore
            'storage_driver': info.get('Driver', 'unknown'),  # type: ignore
            'docker_root_dir': info.get('DockerRootDir', 'unknown'),  # type: ignore
            'images_count': len(client.images.list()),  # type: ignore
            'containers_count': len(client.containers.list(all=True))  # type: ignore
        }
    except Exception as e:
        return {'error': str(e)}
