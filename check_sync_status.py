#!/usr/bin/env python3
"""
Magentic-UI 同步状态检查脚本
自动检查是否需要与官方仓库同步
"""

import subprocess
import sys
from datetime import datetime
from typing import Tuple

def run_cmd(cmd: str) -> Tuple[bool, str, str]:
    """执行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_git_status():
    """检查Git状态"""
    print("🔍 检查Git仓库状态...")
    
    # 检查是否在Git仓库中
    success, _, _ = run_cmd("git rev-parse --git-dir")
    if not success:
        print("❌ 当前目录不是Git仓库")
        return False
    
    # 检查是否有未提交的更改
    success, output, _ = run_cmd("git status --porcelain")
    if output:
        print("⚠️  有未提交的更改:")
        print(output)
        return False
    
    print("✅ Git状态清洁")
    return True

def check_remotes():
    """检查远程仓库配置"""
    print("\n🔗 检查远程仓库配置...")
    
    success, output, _ = run_cmd("git remote -v")
    if not success:
        print("❌ 无法获取远程仓库信息")
        return False
    
    has_upstream = "upstream" in output
    has_origin = "origin" in output
    
    print(f"📍 远程仓库状态:")
    print(f"  - Origin: {'✅' if has_origin else '❌'}")
    print(f"  - Upstream: {'✅' if has_upstream else '❌'}")
    
    if not has_upstream:
        print("\n❌ 未配置upstream远程仓库")
        print("请执行: git remote add upstream https://github.com/microsoft/magentic-ui.git")
        return False
    
    return True

def fetch_updates():
    """获取最新更新"""
    print("\n📥 获取最新更新...")
    
    # 获取upstream更新
    success, _, error = run_cmd("git fetch upstream")
    if not success:
        print(f"❌ 获取upstream更新失败: {error}")
        return False
    
    # 获取origin更新
    success, _, error = run_cmd("git fetch origin")
    if not success:
        print(f"❌ 获取origin更新失败: {error}")
        return False
    
    print("✅ 更新获取成功")
    return True

def check_sync_status():
    """检查同步状态"""
    print("\n🔄 检查同步状态...")
    
    # 检查是否有新的上游提交
    _, upstream_new, _ = run_cmd("git log --oneline HEAD..upstream/main")
    
    # 检查是否有本地提交未推送
    _, local_ahead, _ = run_cmd("git log --oneline upstream/main..HEAD")
    
    print(f"📊 同步状态:")
    
    if upstream_new:
        print(f"  🆕 上游新提交 ({len(upstream_new.split(chr(10)))} 个):")
        for line in upstream_new.split('\n')[:5]:  # 显示前5个
            print(f"    - {line}")
        if len(upstream_new.split('\n')) > 5:
            print(f"    ... 还有 {len(upstream_new.split(chr(10))) - 5} 个提交")
    else:
        print("  ✅ 已与上游同步")
    
    if local_ahead:
        print(f"  🚀 本地领先提交 ({len(local_ahead.split(chr(10)))} 个):")
        for line in local_ahead.split('\n')[:3]:  # 显示前3个
            print(f"    - {line}")
        if len(local_ahead.split('\n')) > 3:
            print(f"    ... 还有 {len(local_ahead.split(chr(10))) - 3} 个提交")
    else:
        print("  📍 本地无领先提交")
    
    return bool(upstream_new), bool(local_ahead)

def check_interesting_branches():
    """检查有趣的分支"""
    print("\n🌿 检查有价值的分支...")
    
    interesting_branches = [
        "upstream/fix_latency",
        "upstream/further_experiments", 
        "upstream/latency_db",
        "upstream/sentinel/add-planstep"
    ]
    
    for branch in interesting_branches:
        success, output, _ = run_cmd(f"git log --oneline {branch} -1")
        if success:
            print(f"  🔍 {branch}: {output}")
        else:
            print(f"  ❌ {branch}: 不存在")

def generate_report():
    """生成报告"""
    print(f"\n📋 同步检查报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 检查Git状态
    if not check_git_status():
        return
    
    # 检查远程仓库
    if not check_remotes():
        return
    
    # 获取更新
    if not fetch_updates():
        return
    
    # 检查同步状态
    need_sync, has_local = check_sync_status()
    
    # 检查有趣的分支
    check_interesting_branches()
    
    # 生成建议
    print("\n💡 建议:")
    if need_sync:
        print("  🔄 需要同步上游更新")
        print("  📝 请参考 SYNC_STRATEGY.md 文档")
        print("  🚀 建议命令:")
        print("    git merge upstream/main --no-ff")
    else:
        print("  ✅ 无需同步，您已是最新状态")
    
    if has_local:
        print("  📤 考虑推送本地更改到origin")
        print("    git push origin main")
    
    print("\n📚 参考文档: SYNC_STRATEGY.md")

def main():
    """主函数"""
    print("🔄 Magentic-UI 同步状态检查器")
    print("=" * 40)
    
    try:
        generate_report()
    except KeyboardInterrupt:
        print("\n\n⏹️  检查已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检查过程中出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 