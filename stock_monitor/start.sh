#!/bin/bash

# 创建新的tmux会话
tmux new-session -d -s stock_monitor

# 创建两个窗口
tmux rename-window -t stock_monitor:0 'monitor'
tmux new-window -t stock_monitor:1 -n 'dashboard'

# 在第一个窗口运行监控程序
tmux send-keys -t stock_monitor:monitor 'python monitor.py' C-m

# 在第二个窗口运行仪表板
tmux send-keys -t stock_monitor:dashboard 'python dashboard.py' C-m

# 附加到tmux会话
tmux attach-session -t stock_monitor 