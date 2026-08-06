#!/bin/bash
# ============================================
# Monitor aaPanel Installation
# Jalankan: watch -n 10 bash /tmp/monitor_aa.sh
# Atau:     tail -f /tmp/aapanel-install.log
# ============================================

echo "=== aaPanel Install Monitor ==="
echo ""

# Check if install is running
PROCS=$(ps aux | grep install_6 | grep -v grep | wc -l)
echo "Install processes: $PROCS"

# Show last log lines
echo ""
echo "Last 5 log lines:"
tail -5 /tmp/aapanel-install.log 2>/dev/null

# Check ports
echo ""
echo "Listening ports:"
sudo ss -tlnp 2>/dev/null | grep -E "8888|32661|80|443|21|2222" || echo "  (none yet)"

# Check disk
echo ""
echo "Disk:"
df -h / | tail -1

# Check RAM
echo "RAM:"
free -h | grep Mem
free -h | grep Swap

echo ""
echo "=== To see live log: tail -f /tmp/aapanel-install.log ==="
