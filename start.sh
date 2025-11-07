#!/bin/bash
# 启动个性番茄钟应用

# 激活 conda 环境并运行程序
eval "$(conda shell.bash hook)"
conda activate pomodoro
python pomodoro.py
