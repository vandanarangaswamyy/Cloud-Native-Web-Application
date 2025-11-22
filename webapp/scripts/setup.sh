#!/bin/bash
set -e  # Exit on error

APP_NAME="csye6225"
APP_DIR="/opt/$APP_NAME"
ENV_FILE="$APP_DIR/.env"
APP_PORT="${APP_PORT:-8000}"

# -------------------------------
# Root privilege check
# -------------------------------
if [[ $EUID -ne 0 ]]; then
   echo " This script must be run as root (use sudo)."
   exit 1
fi

echo "Starting setup for $APP_NAME"

# -------------------------------
# 1. Update & Install Dependencies
# -------------------------------
apt update -y && apt upgrade -y
apt install -y unzip python3 python3-venv python3-pip build-essential libmysqlclient-dev

# -------------------------------
# 2. Load environment file (optional fallback)
# -------------------------------
if [ -f /tmp/.env ]; then
  echo " Loading environment variables from /tmp/.env"
  mkdir -p $APP_DIR
  mv /tmp/.env $ENV_FILE
  chown root:root $ENV_FILE
else
  echo ".env not found at /tmp/.env — proceeding, values expected from /etc/environment"
fi

# -------------------------------
# 3. Create Linux Group & User
# -------------------------------
if ! getent group $APP_NAME >/dev/null; then
    groupadd $APP_NAME
fi
if ! id -u $APP_NAME >/dev/null 2>&1; then
    useradd -r -s /usr/sbin/nologin -g $APP_NAME $APP_NAME || true
fi

# -------------------------------
# 4. Deploy Application Files
# -------------------------------
mkdir -p $APP_DIR
TMP_DIR=$(mktemp -d)

if [[ -f /tmp/app.zip ]]; then
    unzip -o /tmp/app.zip -d $TMP_DIR
else
    echo " No /tmp/app.zip found. The app artifact must be copied before AMI build."
    exit 1
fi

entries=($TMP_DIR/*)
if [[ ${#entries[@]} -eq 1 && -d "${entries[0]}" ]]; then
    mv "${entries[0]}"/* $APP_DIR/
else
    mv $TMP_DIR/* $APP_DIR/
fi
rm -rf $TMP_DIR

chown -R $APP_NAME:$APP_NAME $APP_DIR
chmod -R 750 $APP_DIR

# -------------------------------
# 5. Python Virtual Environment
# -------------------------------
cd $APP_DIR
sudo -u $APP_NAME python3 -m venv venv
sudo -u $APP_NAME venv/bin/pip install --upgrade pip

if [[ -f requirements.txt ]]; then
    sudo -u $APP_NAME venv/bin/pip install -r requirements.txt
else
    echo " requirements.txt not found — skipping pip install"
fi

# -------------------------------
# 6. Django Migration Safety Check (optional)
# -------------------------------
echo "Django will connect to RDS; skipping migrations during AMI build."
# NOTE: During EC2 launch, Django will auto-migrate or migrate via GitHub Actions integration test.

# -------------------------------
# 7. Systemd Service for Django
# -------------------------------
cat > /etc/systemd/system/${APP_NAME}.service <<EOF
[Unit]
Description=Django Web Application (RDS)
After=network.target
ConditionPathExists=${APP_DIR}/.env

[Service]
User=$APP_NAME
Group=$APP_NAME
WorkingDirectory=$APP_DIR
EnvironmentFile=-/etc/environment
EnvironmentFile=-$ENV_FILE
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/manage.py runserver 0.0.0.0:${APP_PORT}
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${APP_NAME}.service
sudo mkdir -p /var/log/webapp
sudo chown csye6225:csye6225 /var/log/webapp
sudo chmod 755 /var/log/webapp
systemctl start ${APP_NAME}.service
echo "Setup complete!"
echo "Webapp is running and will auto-start on boot."