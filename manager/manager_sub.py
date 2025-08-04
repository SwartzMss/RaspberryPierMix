#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
传感器数据管理器主程序
用于systemd服务启动
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from manager.manager import main

if __name__ == "__main__":
    main() 