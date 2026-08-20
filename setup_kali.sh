#!/bin/bash
# CHAOS TYPE ZERO — Kali Linux WSL2 Setup
# Run: chmod +x setup_kali.sh && ./setup_kali.sh
#
# This script sets up a Kali Linux WSL2 environment with security tools
# for CTZ integration. Run from PowerShell as Administrator or from
# an existing WSL2 shell.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

NEXUS_DIR="$(cd "$(dirname "$0")" && pwd)"
TOOLS_DIR="/opt/ctz-tools"

echo ""
echo -e "${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║  CHAOS TYPE ZERO — Kali Linux WSL2 Setup    ║"
echo "  ║  Security Toolkit Installer v1.0            ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Detect environment
IS_WSL=false
if grep -qiE "(microsoft|wsl)" /proc/version 2>/dev/null; then
    IS_WSL=true
fi

# --- Step 1: Check if we're in Kali ---
echo -e "${CYAN}[1/7] Checking environment...${NC}"
if [ -f /etc/os-release ] && grep -qi "kali" /etc/os-release; then
    echo -e "  ${GREEN}[OK] Running in Kali Linux${NC}"
elif [ "$IS_WSL" = true ]; then
    echo -e "  ${YELLOW}[INFO] Running in WSL2 (non-Kali distro)${NC}"
    echo -e "  ${CYAN}Attempting to install Kali Linux distribution...${NC}"

    if command -v wsl.exe &>/dev/null; then
        wsl.exe --list --verbose 2>/dev/null | grep -qi kali
        if [ $? -ne 0 ]; then
            echo -e "  ${CYAN}Installing Kali Linux (this may take a few minutes)...${NC}"
            powershell.exe -Command "wsl --install -d kali-linux" 2>/dev/null || true
            echo -e "  ${YELLOW}[ACTION REQUIRED]${NC}"
            echo -e "  Kali Linux has been installed. Please:"
            echo -e "    1. Open Kali Linux from Start Menu"
            echo -e "    2. Complete initial setup (create username/password)"
            echo -e "    3. Re-run this script from inside Kali Linux:"
            echo -e "       ${BOLD}./setup_kali.sh${NC}"
            exit 0
        fi
        echo -e "  ${GREEN}[OK] Kali Linux found in WSL2${NC}"
        echo -e "  ${YELLOW}Switch to Kali and re-run this script:${NC}"
        echo -e "    wsl -d kali-linux"
        echo -e "    cd $(wslpath -u "$(pwd)" 2>/dev/null || echo "$NEXUS_DIR")"
        echo -e "    ./setup_kali.sh"
        exit 0
    else
        echo -e "  ${RED}[ERROR] Not in WSL2 and not Kali. Cannot auto-install.${NC}"
        echo -e "  Install WSL2 manually: wsl --install"
        exit 1
    fi
else
    echo -e "  ${YELLOW}[WARN] Not detected as WSL2 or Kali. Proceeding anyway...${NC}"
fi

# --- Step 2: Update system ---
echo -e "${CYAN}[2/7] Updating package lists...${NC}"
sudo apt-get update -qq 2>&1 | tail -1
echo -e "  ${GREEN}[OK] Package lists updated${NC}"

# --- Step 3: Install base packages ---
echo -e "${CYAN}[3/7] Installing base packages...${NC}"
BASE_PKGS=(
    python3 python3-pip python3-venv
    git curl wget
    build-essential libssl-dev libffi-dev
    jq unzip
)
sudo apt-get install -y -qq "${BASE_PKGS[@]}" 2>&1 | tail -3
echo -e "  ${GREEN}[OK] Base packages installed${NC}"

# --- Step 4: Install security tools ---
echo -e "${CYAN}[4/7] Installing security tools...${NC}"

SECURITY_PKGS=(
    nmap
    nikto
    sqlmap
    gobuster
    dirb
    enum4linux
    whatweb
    wafw00f
    amass
    recon-ng
)

# Install from apt
for pkg in "${SECURITY_PKGS[@]}"; do
    if dpkg -s "$pkg" &>/dev/null; then
        echo -e "  ${GREEN}[OK] $pkg already installed${NC}"
    else
        echo -e "  ${CYAN}Installing $pkg...${NC}"
        sudo apt-get install -y -qq "$pkg" 2>/dev/null && \
            echo -e "  ${GREEN}[OK] $pkg installed${NC}" || \
            echo -e "  ${YELLOW}[WARN] $pkg failed to install from apt${NC}"
    fi
done

# --- Step 5: Install Go-based tools ---
echo -e "${CYAN}[5/7] Installing Go-based security tools...${NC}"
if ! command -v go &>/dev/null; then
    echo -e "  ${CYAN}Installing Go...${NC}"
    GO_VERSION="1.22.5"
    wget -q "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" -O /tmp/go.tar.gz
    sudo tar -C /usr/local -xzf /tmp/go.tar.gz 2>/dev/null
    rm -f /tmp/go.tar.gz
    export PATH=$PATH:/usr/local/go/bin
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    echo -e "  ${GREEN}[OK] Go installed${NC}"
fi

# nuclei
if ! command -v nuclei &>/dev/null; then
    echo -e "  ${CYAN}Installing nuclei...${NC}"
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest 2>&1 | tail -1
    echo -e "  ${GREEN}[OK] nuclei installed${NC}"
else
    echo -e "  ${GREEN}[OK] nuclei already installed${NC}"
fi

# httpx
if ! command -v httpx &>/dev/null; then
    echo -e "  ${CYAN}Installing httpx...${NC}"
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest 2>&1 | tail -1
    echo -e "  ${GREEN}[OK] httpx installed${NC}"
else
    echo -e "  ${GREEN}[OK] httpx already installed${NC}"
fi

# subfinder
if ! command -v subfinder &>/dev/null; then
    echo -e "  ${CYAN}Installing subfinder...${NC}"
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest 2>&1 | tail -1
    echo -e "  ${GREEN}[OK] subfinder installed${NC}"
else
    echo -e "  ${GREEN}[OK] subfinder already installed${NC}"
fi

# ffuf
if ! command -v ffuf &>/dev/null; then
    echo -e "  ${CYAN}Installing ffuf...${NC}"
    go install -v github.com/ffuf/ffuf/v2@latest 2>&1 | tail -1
    echo -e "  ${GREEN}[OK] ffuf installed${NC}"
else
    echo -e "  ${GREEN}[OK] ffuf already installed${NC}"
fi

# --- Step 6: Setup CTZ tool symlinks ---
echo -e "${CYAN}[6/7] Creating CTZ symlinks...${NC}"
mkdir -p "$TOOLS_DIR"

# Add Go bin to PATH for symlinks
export PATH=$PATH:$(go env GOPATH)/bin:/usr/local/go/bin

TOOLS=(nuclei httpx subfinder ffuf nmap sqlmap gobuster nikto amass)
for tool in "${TOOLS[@]}"; do
    TOOL_PATH=$(command -v "$tool" 2>/dev/null || \
                echo "$(go env GOPATH)/bin/$tool" 2>/dev/null || \
                echo "/usr/bin/$tool")
    if [ -f "$TOOL_PATH" ] || [ -x "$TOOL_PATH" ]; then
        ln -sf "$TOOL_PATH" "$TOOLS_DIR/$tool" 2>/dev/null
        echo -e "  ${GREEN}[OK] Linked $tool${NC}"
    else
        echo -e "  ${YELLOW}[WARN] $tool not found, skipping link${NC}"
    fi
done

# Create a PATH wrapper
CTZ_PATH_FILE="$TOOLS_DIR/ctz-path.sh"
cat > "$CTZ_PATH_FILE" <<PATHEOF
# Add CTZ tools to PATH
export PATH="$TOOLS_DIR:$PATH"
export PATH="\$(go env GOPATH)/bin:\$PATH"
export PATH="/usr/local/go/bin:\$PATH"
PATHEOF
echo -e "  ${GREEN}[OK] Created PATH wrapper at $CTZ_PATH_FILE${NC}"

# Add to bashrc if not present
if ! grep -q "ctz-path.sh" ~/.bashrc 2>/dev/null; then
    echo "source $CTZ_PATH_FILE 2>/dev/null" >> ~/.bashrc
    echo -e "  ${GREEN}[OK] Added to ~/.bashrc${NC}"
fi

# --- Step 7: Verify ---
echo -e "${CYAN}[7/7] Verifying installation...${NC}"
echo ""

INSTALLED=0
FAILED=0
for tool in nmap nikto sqlmap gobuster subfinder httpx nuclei ffuf amass; do
    if command -v "$tool" &>/dev/null || [ -x "$TOOLS_DIR/$tool" ]; then
        echo -e "  ${GREEN}[OK] $tool${NC}"
        INSTALLED=$((INSTALLED + 1))
    else
        echo -e "  ${RED}[--] $tool not available${NC}"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo -e "${GREEN}${BOLD}  ════════════════════════════════════════════════"
echo "  KALI LINUX SETUP COMPLETE"
echo -e "  ════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}Tools installed:  $INSTALLED${NC}"
echo -e "  ${YELLOW}Tools unavailable: $FAILED${NC}"
echo ""
echo -e "  ${CYAN}Quick reference:${NC}"
echo "    nmap -sV -sC <target>       # Service scan"
echo "    nuclei -u <url>             # Vuln scan"
echo "    subfinder -d <domain>       # Subdomain enum"
echo "    httpx -l subs.txt           # HTTP probe"
echo "    ffuf -u <url>/FUZZ -w <wordlist>  # Fuzzing"
echo "    sqlmap -u '<url>?id=1'      # SQL injection"
echo "    gobuster dir -u <url> -w <wordlist>  # Dir bust"
echo "    nikto -h <host>             # Web vuln scan"
echo "    amass enum -d <domain>      # OSINT recon"
echo ""
echo -e "  ${CYAN}Tools dir: $TOOLS_DIR${NC}"
echo -e "  ${CYAN}CTZ dir:   $NEXUS_DIR${NC}"
echo ""
