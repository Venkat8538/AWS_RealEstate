#!/bin/bash
# ============================================================
# STIG-Approved EC2 Bootstrap Script (RHEL 8.1)
# Purpose:
#  - Bamboo-ready EC2 instance
#  - Rootless Docker (NO Podman)
#  - SELinux Enforcing
#  - Kubernetes tooling
#  - GovCloud / SAIC compliant
# ============================================================

set -euo pipefail

HOSTNAME_PREFIX="linux-bamboo"
BAMBOO_USER="bamboo"

# ------------------------------------------------------------
# Packages (STIG-safe, RHEL 8.1)
# ------------------------------------------------------------
PACKAGES_TO_INSTALL=(
  jq
  curl
  unzip
  net-tools
  uidmap
  slirp4netns
  dbus-user-session
  yum-utils
  cloud-utils-growpart
  xfsprogs
  policycoreutils-python-utils
)

# ------------------------------------------------------------
# Ensure Bamboo user exists
# ------------------------------------------------------------
ensure_bamboo_user() {
  if ! id "${BAMBOO_USER}" &>/dev/null; then
    useradd -m -s /bin/bash "${BAMBOO_USER}"
  fi
}

# ------------------------------------------------------------
# Hostname from EC2 Name tag (best-effort)
# ------------------------------------------------------------
create_and_set_hostname() {
  local TOKEN INSTANCEID NAME NUMBER SUFFIX

  TOKEN="$(curl -sS -X PUT \
    http://169.254.169.254/latest/api/token \
    -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' || true)"

  INSTANCEID="$(curl -sS \
    -H "X-aws-ec2-metadata-token: ${TOKEN}" \
    http://169.254.169.254/latest/meta-data/instance-id || true)"

  if [[ -n "${INSTANCEID}" ]] && command -v aws >/dev/null 2>&1; then
    NAME="$(aws ec2 describe-tags \
      --filters "Name=resource-id,Values=${INSTANCEID}" \
      | jq -r '.Tags[] | select(.Key=="Name").Value' 2>/dev/null || true)"

    NUMBER="$(echo "${NAME}" | sed -r 's/.*-([0-9]+)/\1/' || true)"
  fi

  SUFFIX="${NUMBER:-$(date +%s)}"
  hostnamectl set-hostname "${HOSTNAME_PREFIX}-${SUFFIX}" || true
}

# ------------------------------------------------------------
# FIPS / STIG SSH hardening
# ------------------------------------------------------------
fix_sshd_conf() {
  sed -r -i 's/^(HostKey.*ed25519.*)/#\1/g' /etc/ssh/sshd_config || true
  systemctl restart sshd || true
}

# ------------------------------------------------------------
# Install base packages
# ------------------------------------------------------------
install_packages() {
  yum makecache -y || true
  yum install -y "${PACKAGES_TO_INSTALL[@]}"
}

# ------------------------------------------------------------
# Rootless Docker kernel tuning (STIG allowed)
# ------------------------------------------------------------
configure_sysctl() {
  if grep -q '^user.max_user_namespaces=' /etc/sysctl.conf; then
    sed -i 's/^user.max_user_namespaces=.*/user.max_user_namespaces=49512/' /etc/sysctl.conf
  else
    echo "user.max_user_namespaces=49512" >> /etc/sysctl.conf
  fi
  sysctl -p || true
}

# ------------------------------------------------------------
# Docker install (INTERNAL REPO REQUIRED)
# ------------------------------------------------------------
install_docker() {
  # 🔒 STIG NOTE:
  # Replace the repo URL below with your APPROVED INTERNAL REPOSITORY
  yum-config-manager --add-repo \
    https://<INTERNAL_ARTIFACTORY_OR_MIRROR>/docker-ce-rhel8.repo

  yum install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-ce-rootless-extras
}

# ------------------------------------------------------------
# Required for rootless Docker
# ------------------------------------------------------------
configure_subuids() {
  grep -q "^${BAMBOO_USER}:" /etc/subuid || \
    echo "${BAMBOO_USER}:100000:65536" >> /etc/subuid

  grep -q "^${BAMBOO_USER}:" /etc/subgid || \
    echo "${BAMBOO_USER}:100000:65536" >> /etc/subgid
}

# ------------------------------------------------------------
# Rootless Docker configuration
# ------------------------------------------------------------
configure_rootless_docker() {
  loginctl enable-linger "${BAMBOO_USER}" || true

  local UID
  UID="$(id -u ${BAMBOO_USER})"

  mkdir -p "/run/user/${UID}"
  chown "${BAMBOO_USER}:${BAMBOO_USER}" "/run/user/${UID}"
  chmod 700 "/run/user/${UID}"

  sudo -iu "${BAMBOO_USER}" bash <<'EOF'
set -euo pipefail
export XDG_RUNTIME_DIR="/run/user/$(id -u)"

dockerd-rootless-setuptool.sh install

systemctl --user daemon-reload
systemctl --user enable docker
systemctl --user start docker
EOF

  # SELinux (STIG-friendly)
  setsebool -P container_use_devices 1 || true

  cat <<EOF > /etc/profile.d/docker-rootless.sh
export DOCKER_HOST=unix:///run/user/${UID}/docker.sock
EOF
  chmod 644 /etc/profile.d/docker-rootless.sh
}

# ------------------------------------------------------------
# Root volume extension (safe / best-effort)
# ------------------------------------------------------------
extend_root_volume() {
  if command -v growpart &>/dev/null && command -v xfs_growfs &>/dev/null; then
    ROOT_DEV=$(findmnt -n -o SOURCE /)
    if [[ "$ROOT_DEV" =~ nvme ]]; then
      growpart /dev/nvme0n1 1 || true
      xfs_growfs / || true
    fi
  fi
}

# ------------------------------------------------------------
# Kubernetes tooling (repo should also be internal if required)
# ------------------------------------------------------------
install_kubectl() {
  cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://<INTERNAL_ARTIFACTORY_OR_MIRROR>/kubernetes/rpm/
enabled=1
gpgcheck=1
gpgkey=https://<INTERNAL_ARTIFACTORY_OR_MIRROR>/kubernetes/gpg.key
EOF

  yum install -y kubectl
}

install_helm() {
  cd /tmp
  curl -fsSL https://<INTERNAL_ARTIFACTORY_OR_MIRROR>/helm/get-helm.sh -o get_helm.sh
  chmod +x get_helm.sh
  ./get_helm.sh
}

install_kubectl_completion() {
  mkdir -p /etc/bash_completion.d
  kubectl completion bash > /etc/bash_completion.d/kubectl || true
}

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
main() {
  ensure_bamboo_user
  create_and_set_hostname
  fix_sshd_conf
  install_packages
  configure_sysctl
  install_docker
  configure_subuids
  configure_rootless_docker
  extend_root_volume
  install_kubectl
  install_helm
  install_kubectl_completion
}

main

rm -rf /tmp/* || true
