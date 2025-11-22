#!/bin/bash
set -e

APP_NAME="csye6225"
APP_DIR="/opt/${APP_NAME}"
ENV_FILE="${APP_DIR}/.env"
APP_PORT=8000

echo "==== Bootstrapping ${APP_NAME} ===="

# Create application directory if missing
mkdir -p $APP_DIR

sudo apt-get update -y
sudo apt-get install -y jq unzip curl
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo unzip awscliv2.zip
sudo ./aws/install

# -------------------------------
# Fetch DB credentials securely from Secrets Manager
# -------------------------------
echo "Fetching DB credentials from Secrets Manager..."
DB_SECRET_JSON=$(aws secretsmanager get-secret-value \
  --secret-id ${db_secret_arn} \
  --query SecretString \
  --output text \
  --region ${region})

MYSQL_USER=$(echo "$DB_SECRET_JSON" | jq -r .username)
MYSQL_PASSWORD=$(echo "$DB_SECRET_JSON" | jq -r .password)

# -------------------------------
# Write environment variables
# -------------------------------
echo "Writing environment variables to $ENV_FILE..."

cat > $ENV_FILE <<EOF
# Django + Database Configuration
MYSQL_DATABASE=${db_name}
MYSQL_USER=$MYSQL_USER
MYSQL_PASSWORD=$MYSQL_PASSWORD
MYSQL_HOST=${db_host}
MYSQL_PORT=3306

# S3 Configuration
S3_BUCKET_NAME=${s3_bucket_name}
AWS_REGION=${region}
SNS_TOPIC_ARN=${sns_topic_arn}

# Django Settings
DJANGO_SETTINGS_MODULE=webapp.settings
DEBUG=False
EOF

chmod 640 $ENV_FILE

# -------------------------------
# Create application user
# -------------------------------
if ! id -u $APP_NAME >/dev/null 2>&1; then
  useradd -r -s /usr/sbin/nologin $APP_NAME
fi
chown -R $APP_NAME:$APP_NAME $APP_DIR

# -------------------------------
# Reload and restart systemd service
# -------------------------------
echo "Reloading systemd and restarting ${APP_NAME} service..."
systemctl daemon-reload
systemctl enable ${APP_NAME}.service

# -------------------------------
# Run Django Migrations
# -------------------------------
echo "Running Django database migrations..."
MAX_RETRIES=5
RETRY_DELAY=5
COUNTER=1

# Wait for RDS to become available
until mysql -h "${db_host}" -u "$${MYSQL_USER}" -p"$${MYSQL_PASSWORD}" -e "SELECT 1;" &>/dev/null; do
  echo "Waiting for RDS to be ready... attempt $${COUNTER}/$${MAX_RETRIES}"
  sleep $${RETRY_DELAY}
  ((COUNTER++))
  if [ $${COUNTER} -gt $${MAX_RETRIES} ]; then
    echo "⚠️ RDS not reachable, skipping migrations."
    break
  fi
done

echo "Running Django migrations..."
sudo -u ${APP_NAME} ${APP_DIR}/venv/bin/python ${APP_DIR}/manage.py migrate --noinput

echo "Restarting Django service..."
systemctl restart ${APP_NAME}.service



# -------------------------------
# Verify service status
# -------------------------------
sleep 10
if systemctl is-active --quiet ${APP_NAME}.service; then
  echo "${APP_NAME} is running successfully on port ${APP_PORT}"
else
  echo "⚠️ ${APP_NAME} failed to start. Checking logs..."
  journalctl -u ${APP_NAME}.service --no-pager | tail -n 50
fi

echo "==== ${APP_NAME} setup complete! ===="

sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s

