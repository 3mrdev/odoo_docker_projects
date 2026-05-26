# 🚀 Odoo 18 with Docker Compose

This repository provides a ready-to-use **Docker Compose setup** for running **Odoo 18** with **PostgreSQL**.  
It supports custom modules in `custom_addons` and `enterprise_addons`, making it easy to develop and test Odoo apps in a clean environment.

---

## 📂 Project Structure

```
.
├── compose.yaml        # Docker Compose configuration
├── .env                # Environment variables for Postgres & Odoo
├── config/
│   └── odoo.conf       # Odoo configuration (addons paths, db, etc.)
├── custom_addons/      # Your custom modules go here
├── enterprise_addons/  # Enterprise modules (if licensed)
├── odoo-web-data/      # Persistent Odoo filestore
├── odoo-db-data/       # Persistent PostgreSQL data
└── odoo_pg_pass        # Secret file with Postgres password
```

---

## ▶️ Usage


## 🐳 1. Installing Docker & Docker Compose

Before running this project, make sure you have **[Docker](https://www.docker.com/)** and **Docker Compose** installed.

Follow the official installation guides:

- **Windows**: [Install Docker Desktop on Windows](https://docs.docker.com/desktop/setup/install/windows-install/)  
- **macOS**: [Install Docker Desktop on Mac](https://docs.docker.com/desktop/setup/install/mac-install/)  
- **Linux**: [Install Docker Engine on Linux](https://docs.docker.com/desktop/setup/install/linux/)  

After installation, verify by typing this in terminal/cmd:
```bash
docker --version
docker compose version
```

---

### 2. Create a new folder for Odoo in your prefered path
Open your prefered path and create a new folder with the odoo version you want for example:  
- **Windows**: D:/odoo/odoo18
- **macOS**: /Users/firebits/odoo/odoo18
- **Linux**: /odoo/odoo18

Clone the repo in that folder using git:
```bash
git clone --depth 1 --branch 18.0 https://github.com/3mrdev/odoo_docker_compose.git
```

After the clone is finished open the folder and rename the env file to .env

👉 [[Optional] More Advanced Configuration Info](README_MORE.md)

### 3. Start Services
In the same terminal/cmd of the odoo folder that you have cloned in use this command to download odoo and build your container
```bash
docker compose up -d
```

This will start:
- **Odoo** (port `8018`)
- **Postgres** (port `5432` internally)

### 4. Access Odoo
Open your browser and go to:  
👉 [http://localhost:8018](http://localhost:8018)

### 5. Stop Services
```bash
docker compose down
```

---

## Odoo Versions

Supported: Odoo 18, Odoo 17 and Odoo 16

## 📜 License
This setup is provided for development and testing.  
Odoo **Enterprise Addons** require a valid Odoo Enterprise license.