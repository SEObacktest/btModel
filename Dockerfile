# 使用官方 Gitpod 基础镜像
FROM gitpod/workspace-full

# 切换到 gitpod 用户
USER gitpod

# 更新包列表并安装必要的依赖
RUN sudo apt-get update && sudo apt-get install -y \
    software-properties-common \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libffi-dev \
    liblzma-dev \
    git

# 添加 Deadsnakes PPA 并安装 Python 3.8
RUN sudo add-apt-repository ppa:deadsnakes/ppa -y && \
    sudo apt-get update && \
    sudo apt-get install -y python3.8 python3.8-venv python3.8-dev && \
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1

# 设置 pip3 指向 Python 3.8 的 pip
RUN sudo apt-get install -y python3-pip && \
    python3.8 -m pip install --upgrade pip && \
    sudo update-alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3 1

# 验证安装
RUN python3 --version
RUN pip3 --version
