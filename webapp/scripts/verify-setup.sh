#!/bin/bash
echo "=== MySQL ==="
mysql --version && echo "✓ MySQL installed"
systemctl is-active mysql && echo "✓ MySQL running"

echo -e "\n=== Database ==="
sudo mysql -e "SHOW DATABASES LIKE 'webapp_db';" | grep -q webapp_db && echo "✓ Database exists"
sudo mysql -e "SELECT User FROM mysql.user WHERE User='webapp_user';" | grep -q webapp_user && echo "✓ User exists"

echo -e "\n=== User & Group ==="
id csye6225 && echo "✓ User exists"
getent group csye6225 && echo "✓ Group exists"

echo -e "\n=== Application Files ==="
[ -f /opt/csye6225/manage.py ] && echo "✓ manage.py found"
[ -f /opt/csye6225/requirements.txt ] && echo "✓ requirements.txt found"

echo -e "\n=== Permissions ==="
[ "$(stat -c %U /opt/csye6225)" = "csye6225" ] && echo "✓ Correct ownership"
[ "$(stat -c %a /opt/csye6225)" = "750" ] && echo "✓ Correct permissions"

echo -e "\n=== Service ==="
systemctl is-active csye6225 && echo "✓ Service running"
systemctl is-enabled csye6225 && echo "✓ Service enabled"

echo -e "\n=== Application ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/healthz