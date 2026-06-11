#!/bin/bash
#CONTAINER_NAME：定义了一个 Docker 容器的名称，值为 genie_sim_benchmark。
# 通常用于后续 docker exec、docker stop 等命令中指定要操作的目标容器。
#START_SCRIPT：定义了一个脚本路径，$PWD 是当前工作目录，因此它指向当前目录下的 scripts/start_gui.sh 文件。
# 这个脚本很可能用于启动图形界面（GUI）相关的程序。
#TERMINAL_ENV：值为 autorun，可能是用于标识运行环境的变量（例如“自动运行模式”），或者作为参数传递给其他程序。
#PROCESS_CLIENT：值为 teleop|ros，竖线 | 通常表示正则表达式中的“或”，所以这个变量可能用于 grep 或 pgrep 等命令，
# 匹配包含 teleop 或 ros 的进程名。
CONTAINER_NAME="genie_sim_benchmark"
START_SCRIPT="$PWD/scripts_my/start_gui.sh"
TERMINAL_ENV="autorun"
PROCESS_CLIENT="teleop|ros"

# 自动解压 Pinocchio 动态库。
# 它检查指定路径下是否存在 libpinocchio_casadi.so.3.7.0 这个共享库文件，
# 如果不存在，则从同目录下的 libpinocchio.tar.gz 压缩包中解压出来。
# If the pinocchio library does not exist in vendors/lib, extract it
PINOCCHIO_LIB="$PWD/source/teleop/app/vendors/lib/libpinocchio_casadi.so.3.7.0"
PINOCCHIO_TAR="$PWD/source/teleop/app/vendors/lib/libpinocchio.tar.gz"
if [ ! -f "$PINOCCHIO_LIB" ]; then
    echo "Extracting libpinocchio.tar.gz to vendors/lib ..."
    tar -xzvf "$PINOCCHIO_TAR" -C "$PWD/source/teleop/app/vendors/lib"
fi

# 用于检查一个 Docker 容器是否正在运行，如果没有运行则尝试通过启动脚本自动启动它，并等待容器就绪。
if ! docker inspect --format='{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null | grep -q "true"; then
    echo "Warning: Container $CONTAINER_NAME not running, try to start..."

    if [ -x "$START_SCRIPT" ]; then
        echo "Executing script: $START_SCRIPT (in background)"
        "$START_SCRIPT" &
        START_PID=$!
        MAX_WAIT=60
        ELAPSED=0
        while [ $ELAPSED -lt $MAX_WAIT ]; do
            sleep 3
            ELAPSED=$((ELAPSED + 3))
            if docker inspect --format='{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null | grep -q "true"; then
                echo "Info: Container $CONTAINER_NAME started (after ${ELAPSED}s)"
                break
            fi
        done
        if ! docker inspect --format='{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null | grep -q "true"; then
            echo "Error: Container failed to start within ${MAX_WAIT}s"
            echo "Tip: run './scripts_my/start_gui.sh' in foreground to see errors, or inspect with: docker ps -a | grep $CONTAINER_NAME"
            kill $START_PID 2>/dev/null || true
            exit 1
        fi
    else
        echo "Error: Start script $START_SCRIPT not exist or not executable"
        exit 1
    fi
else
    echo "Info: Container $CONTAINER_NAME already running"
fi

# 定义了两个数组：COMMANDS 和 DELAYS，用于在 Docker 容器中依次启动多个进程，并为每个命令设置了启动前的等待延迟。
declare -a COMMANDS=(
    "docker exec -it $CONTAINER_NAME bash -ic 'omni_python ./source/geniesim/app/app.py --config ./source/geniesim/config/teleop.yaml'"
    "docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/jazzy/setup.bash && source /geniesim/main/source/teleop/app/bin/env.sh && python3 ./source/teleop/bridge.py'"
    "docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/jazzy/setup.bash && source /geniesim/main/source/teleop/app/bin/env.sh && /geniesim/main/source/teleop/app/bin/start_mc.sh --no-tool'"
    "docker exec -it $CONTAINER_NAME bash -ic 'source /geniesim/teleop_env/bin/activate && source /opt/ros/jazzy/setup.bash && source /geniesim/main/source/teleop/app/bin/env.sh && python3 ./source/teleop/teleop.py'"
)
declare -a DELAYS=(1 15 3 5 5)

# 自动检测当前系统中可用的终端模拟器，
# 并设置 TERMINAL_CMD 变量为对应的启动命令，
# 以便后续可以在新终端窗口中执行指定的命令（通常是启动某个需要交互式界面的程序）。
# 这样提高了脚本的可移植性，避免硬编码某个特定终端。
TERMINAL_CMD=""
for term in gnome-terminal konsole xterm terminator; do
    if command -v "$term" &>/dev/null; then
        case "$term" in
        gnome-terminal) TERMINAL_CMD="gnome-terminal -- bash -c" ;;
        konsole) TERMINAL_CMD="konsole -e bash -c" ;;
        xterm) TERMINAL_CMD="xterm -e" ;;
        terminator) TERMINAL_CMD="terminator -e" ;;
        esac
        break
    fi
done

# -z 是测试运算符，检查后面的字符串长度是否为 0
# 没有找到任何终端模拟器
if [ -z "$TERMINAL_CMD" ]; then
    echo "No terminal emulator found. Please install one and try again."
    exit 1
fi

# 在多个新终端窗口中依次启动一系列命令
for i in "${!COMMANDS[@]}"; do
    sleep "${DELAYS[$i]}"
    if [[ "$TERMINAL_CMD" == "gnome-terminal"* ]]; then
        gnome-terminal -- bash -c "export TERMINAL_ENV=$TERMINAL_ENV; ${COMMANDS[$i]}; exec bash" &
    else
        $TERMINAL_CMD "${COMMANDS[$i]}" &
    fi
done

echo -e "\nAll terminals started. Press 'y' or 'Y' = teleoperation succeeded, keep data; 'n' or 'N' = failed, do not keep data ..."
while read -n 1 -s input; do
    if [[ "$input" == "Y" || "$input" == "y" ]]; then
        echo "Save the remote operation data.....Congratulations!"
        echo -e "Sending SIGTERM to teleop processes..."
        docker exec "$CONTAINER_NAME" bash -c "pkill -SIGTERM -f '$PROCESS_CLIENT' 2>/dev/null || true"
        sleep 1
        echo "Patching recording_info.json: add teleop_result"
        docker exec "$CONTAINER_NAME" python3 /geniesim/main/source/teleop/data_recording/patch_recording_info.py \
            --config /geniesim/main/source/geniesim/config/teleop.yaml \
            --base /geniesim/main/output/recording_data \
            || true

        break
    elif [[ "$input" == "N" || "$input" == "n" ]]; then
        echo -e "Sending SIGTERM to teleop processes..."
        docker exec "$CONTAINER_NAME" bash -c "pkill -SIGTERM -f '$PROCESS_CLIENT' 2>/dev/null || true"
        sleep 1
        echo "Patching recording_info.json: add teleop_result=false"
        docker exec "$CONTAINER_NAME" python3 /geniesim/main/source/teleop/data_recording/patch_recording_info.py \
            --config /geniesim/main/source/geniesim/config/teleop.yaml \
            --base /geniesim/main/output/recording_data \
            --teleop-result false \
            || true
        break
    fi
done


reset
