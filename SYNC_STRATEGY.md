# 🔄 Magentic-UI 官方同步策略

## 📊 当前状态 (2025年1月)

### ✅ 同步状态
- **本地分支**: main (已与upstream/main同步)
- **上游状态**: 无新的提交需要同步
- **备份分支**: backup-before-sync-20250711-132214
- **自定义功能**: 已完整保留

### 🎯 您的主要增强功能
1. **OpenAI 多轮对话和图像生成**
2. **配置文件增强** (magentic_ui_config.py)
3. **任务团队优化** (task_team.py)
4. **编排器改进** (_orchestrator.py)
5. **提示词定制** (_prompts.py)

## 🛠️ 标准同步流程

### 第一步：创建安全备份
```bash
# 创建当前时间戳备份
git checkout -b backup-before-sync-$(date +%Y%m%d-%H%M%S)
git checkout main
```

### 第二步：获取最新更新
```bash
# 获取所有远程更新
git fetch upstream
git fetch origin

# 检查是否有新的上游提交
git log --oneline HEAD..upstream/main
```

### 第三步：智能合并策略
```bash
# 如果有新的上游提交，使用合并策略
git merge upstream/main --no-ff -m "🔄 Sync with upstream while preserving custom features"

# 或者使用 rebase 策略（适用于简单更新）
git rebase upstream/main
```

### 第四步：冲突解决原则
1. **配置文件冲突**: 保留我们的配置增强
2. **核心功能冲突**: 优先保留官方逻辑，集成我们的增强
3. **新功能冲突**: 合并两者优势

### 第五步：推送更新
```bash
# 推送到自己的仓库
git push origin main

# 如果使用了rebase，可能需要强制推送
git push origin main --force-with-lease
```

## 🔍 特殊分支关注

### upstream/fix_latency 分支
- **功能**: 延迟优化改进
- **价值**: 可能提升系统性能
- **集成建议**: 
  ```bash
  # 检查该分支的具体改进
  git show upstream/fix_latency --name-only
  git cherry-pick <specific-commit>
  ```

### 其他有价值分支
- **further_experiments**: 实验性功能
- **latency_db**: 数据库延迟优化
- **sentinel/add-planstep**: 计划步骤改进

## 🚨 冲突解决指南

### 常见冲突文件
1. `_orchestrator.py` - 编排器逻辑
2. `_prompts.py` - 提示词定制
3. `task_team.py` - 任务团队配置
4. `magentic_ui_config.py` - 配置文件

### 解决策略
```bash
# 查看冲突文件
git status

# 编辑冲突文件，保留：
# - 官方的核心逻辑更新
# - 我们的功能增强
# - 合并两者的优势

# 标记冲突已解决
git add <resolved-file>
git commit
```

## 🎯 最佳实践

### 1. 渐进式同步
```bash
# 先同步主分支
git merge upstream/main

# 然后选择性集成特定功能
git cherry-pick upstream/fix_latency~2..upstream/fix_latency
```

### 2. 功能分离
- 保持官方核心功能完整
- 将自定义增强作为插件式集成
- 使用配置文件控制功能开关

### 3. 测试验证
```bash
# 同步后进行完整测试
python run_local.py
# 验证核心功能
# 验证自定义增强功能
```

## 📋 检查清单

### 同步前检查
- [ ] 创建备份分支
- [ ] 提交所有本地更改
- [ ] 获取最新上游更新
- [ ] 检查冲突预期

### 同步后验证
- [ ] 核心功能正常
- [ ] 自定义功能保留
- [ ] 配置文件正确
- [ ] 依赖项兼容
- [ ] 测试通过

## 🔄 持续同步建议

### 定期同步
- **频率**: 每周检查一次
- **时机**: 官方有重大更新时
- **方式**: 使用此文档的标准流程

### 监控上游
```bash
# 设置上游监控
git remote set-url --add --push upstream no-push
git fetch upstream --tags
```

## 🚀 下一步行动

1. **当前无需同步** - 您已是最新状态
2. **关注fix_latency分支** - 可能有性能改进
3. **定期检查** - 建议每周执行一次检查
4. **保持备份** - 重要更改前创建备份

---

**📝 创建时间**: 2025年1月
**📊 状态**: 已同步，无需立即行动
**�� 建议**: 定期监控，按需集成新功能 