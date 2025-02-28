import os
import sys

# 获取项目根目录路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 将项目根目录添加到Python路径
sys.path.insert(0, root_dir)