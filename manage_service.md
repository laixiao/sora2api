# manage_service.sh 使用说明

`manage_service.sh` 用于将项目以 systemd 服务方式运行，支持开机自启、更新、日志查看等。请在服务器上以 root 权限或使用 `sudo` 执行。

## 前提
- 工作目录：`/root/sora2api`
- 启动脚本：`start.sh`（已激活 venv 并启动 main.py）
- systemd 环境可用

## 快速开始
```bash
# 赋予执行权限（首次）
sudo chmod +x /root/sora2api/manage_service.sh /root/sora2api/start.sh

# 安装并开机自启 + 立即启动
sudo /root/sora2api/manage_service.sh install
```

安装后会创建 `/etc/systemd/system/sora2api.service`，自动重启 on-failure，日志写入 journal。

## 常用操作
- 查看状态：
  ```bash
  sudo /root/sora2api/manage_service.sh status
  ```
- 查看实时日志：
  ```bash
  sudo /root/sora2api/manage_service.sh logs
  ```
- 重启服务：
  ```bash
  sudo /root/sora2api/manage_service.sh restart
  ```
- 停用并取消开机自启：
  ```bash
  sudo /root/sora2api/manage_service.sh disable
  ```

## 更新流程
```bash
sudo /root/sora2api/manage_service.sh update
```
行为：
1) 若存在 git 仓库则 `git pull --ff-only`；
2) 若存在 `venv/bin/pip` 与 `requirements.txt` 则安装依赖；
3) 重启服务。

## 参数总览
```text
install : 创建并启用 systemd 服务后启动
update  : git pull + 安装依赖 + 重启
restart : 重启服务
status  : 查看 systemd 状态
logs    : 跟随日志 (journalctl -f)
disable : 停止并取消自启
```

## 常见问题
- 端口占用：检查 `main.py` 使用的端口，确保未被其他进程占用。
- 权限问题：所有操作需 root/sudo；脚本和 start.sh 需有执行权限。
- 日志位置：通过 `logs` 查看 journal，或 `journalctl -u sora2api -r` 查看最近日志。

## 自定义
- 修改服务名/工作目录：编辑脚本开头 `SERVICE_NAME` 与 `WORKDIR`。
- 变更启动方式：调整 `start.sh` 内容或在脚本中修改 `ExecStart` 指向。
