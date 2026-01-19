#!/bin/bash
# ============================================================
# Combined Bootstrap Script
# Source: Multiple screenshots provided by user
# Purpose: EC2/Bamboo bootstrap with Docker/Podman/K8s tooling
# ============================================================

set -e

HOSTNAME_PREFIX="linux-bamboo"

PACKAGES_TO_INSTALL=(
  "jq"
  "curl"
  "unzip"
  "net-tools"
)

create_new_hostname() {
  local TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
  local INSTANCEID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)

  if [ -n "$INSTANCEID" ]; then
    local NAME=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$INSTANCEID" | jq -r '.Tags[] | select(.Key | match("^Name$")).Value')
    local NUMBER=$(echo "$NAME" | sed -r 's/.*-([0-9]+)/\1/')
  fi

  local LENGTH=3
  if [ ${#NUMBER} -le $LENGTH ]; then
    local NEW_SUFFIX=$NUMBER
  else
    local SUFFIX=0
    local NEW_SUFFIX="${SUFFIX}${NUMBER}"
  fi

  local NEW_HOSTNAME="${HOSTNAME_PREFIX}-${NEW_SUFFIX}"
  echo "$NEW_HOSTNAME"
}

fix_sshd_conf() {
  sed -r -i 's/^(HostKey.*ed25519.*)/#\1/g' /etc/ssh/sshd_config
}

restart_services() {
  for service in sshd; do
    systemctl restart $service
  done
}

install_packages() {
  for pkg in "${PACKAGES_TO_INSTALL[@]}"; do
    yum install -y "$pkg"
  done
}

configure_docker() {
  sed -i 's/user.max_user_namespaces=.*/user.max_user_namespaces=49512/' /etc/sysctl.conf
  sysctl -p
}

configure_rootless_podman() {
  loginctl enable-linger bamboo
  mkdir -p /home/bamboo/.config/containers

  cat <<EOF > /home/bamboo/.config/containers/storage.conf
[storage]
driver = "overlay"
runroot = "/run/containers/storage"
graphroot = "/home/bamboo/.local/share/containers/storage"

[storage.options]
mount_program = "/usr/bin/fuse-overlayfs"
EOF

  chown -R bamboo:bamboo /home/bamboo/.config
  echo "bamboo ALL=(ALL) NOPASSWD: /usr/bin/podman, /usr/bin/podman-docker" > /etc/sudoers.d/bamboo
  chmod 440 /etc/sudoers.d/bamboo
}

extend_root_volume() {
  growpart /dev/nvme0n1 1
  xfs_growfs /
}

install_kubectl() {
  cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.34/rpm/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.34/rpm/repodata/repomd.xml.key
EOF

  yum install -y kubectl
}

install_helm() {
  cd /tmp
  curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
  chmod +x get_helm.sh
  ./get_helm.sh
}

install_kubectl_bash_completion() {
  kubectl completion bash > /etc/bash_completion.d/kubectl
}

PATH=/bin:/usr/bin:/usr/local/bin:/sbin:/usr/sbin
export PATH

NOW=$(date +%Y-%m-%d-%H-%M-%S)

main() {
  fix_sshd_conf
  restart_services
  install_packages
  configure_docker
  configure_rootless_podman
  extend_root_volume
  install_kubectl
  install_helm
  install_kubectl_bash_completion
}

main

# Cleanup
rm -rf /tmp/*
