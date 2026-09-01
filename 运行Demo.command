#!/bin/bash

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 打开终端并执行命令
osascript -e "tell application \"Terminal\"
    do script \"cd '$DIR' && source .venv/bin/activate && python3 -m research_pipeline demo && open outputs/demo/dashboard.html && echo '' && echo '✅ 完成！结果已打开' && echo '' && echo '按任意键关闭...' && read -n 1\"
    activate
end tell"
