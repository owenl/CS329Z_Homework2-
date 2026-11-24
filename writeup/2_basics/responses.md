# Section 2: Basics

## 2.2.1 Docker ensures reproducibility

**Problem 1 (`docker-setup`)**

1. Paste the commands you used to pull `ubuntu:22.04` and start an interactive container, followed by the output from inside the container that confirms its operating system (e.g., `cat /etc/os-release`).

   ```text
   $ docker pull ubuntu:22.04
   22.04: Pulling from library/ubuntu
   fe6484161c0f: Pull complete
   aeba9e147e22: Download complete
   Digest: sha256:9abcaffc92a5279fff3a6a41635c0800ea33e528425fb389658806476e7defde
   Status: Downloaded newer image for ubuntu:22.04
   docker.io/library/ubuntu:22.04

   $ docker run -it --rm ubuntu:22.04 bash
   root@7f3588ffba34:/# cat /etc/os-release
   PRETTY_NAME="Ubuntu 22.04.5 LTS"
   NAME="Ubuntu"
   VERSION_ID="22.04"
   VERSION="22.04.5 LTS (Jammy Jellyfish)"
   VERSION_CODENAME=jammy
   ID=ubuntu
   ID_LIKE=debian
   HOME_URL="https://www.ubuntu.com/"
   SUPPORT_URL="https://help.ubuntu.com/"
   BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
   PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
   UBUNTU_CODENAME=jammy
   root@7f3588ffba34:/# exit
   ```

## 2.2.2 Harbor defines evaluation primitives

**Problem 2 (`harbor-setup`)**

1. Paste the output of `uv run harbor --version` and `docker version`.

   ```text
   $ uv run harbor --version
0.18.0

$ docker version
Client:
 Version:           29.9.2
 ...
Server: Docker Desktop 4.97.0 (244584)
 ...
   ```

2. From `uv run harbor --help`, which commands start an evaluation job and browse completed results?

   `harbor run` starts an evaluation job. It is an alias for `harbor job start`, and it launches trials of an agent on a dataset or task inside Docker. `harbor view` starts a local web server for browsing completed results, including trajectory files from finished jobs. Related command groups: `harbor job` manages jobs, `harbor trial` manages individual trials, and `harbor analyze` analyzes trial trajectories.
