## ⚙️ Configuration

### 🔑 1. Environment Variables (`.env`)
Example:
```ini
# PostgreSQL
POSTGRES_DB=postgres
POSTGRES_USER=odoo
POSTGRES_PASSWORD_FILE=/run/secrets/postgresql_password
PGDATA=/var/lib/postgresql/data/pgdata

# Odoo
PASSWORD_FILE=/run/secrets/postgresql_password
ODOO_ADDONS_PATH=/mnt/extra-addons,/mnt/enterprise-addons
```

---

### 📝 2. Odoo Config (`config/odoo.conf`)
```ini
[options]
addons_path = /mnt/extra-addons,/mnt/enterprise-addons
data_dir = /var/lib/odoo
admin_passwd = 123
db_host = db
db_port = 5432
db_user = odoo
db_password = ${ODOO_DB_PASSWORD}
```

---

### 🔒 3. Database Password Secret (`odoo_pg_pass`)
Store your Postgres password inside `odoo_pg_pass` (no quotes, no spaces):
```
mysecretpassword
```

---

## 🛠 Useful Commands

Check logs:
```bash
docker compose logs -f web

docker compose exec db psql -d db_name -U odoo docker exec -it o18-web-1 odoo -u module_name -d db_name --stop-after-init --db_host=db --db_user=user --db_password=password 2>&1 | tail -30

docker compose exec -T web odoo -u module_name -d o19_db_2 --db_host=db --db_user=odoo --db_password=openpgpwd --stop-after-init 2>&1
```

Enter Odoo container shell:
```bash
docker compose exec web bash
```

Update a module (hot-reload):
```bash
docker compose exec web odoo -u your_module_name -d o18_db
```

To restart your Odoo server or postgtrs from the UI go to the docker desktop interface and cilck on containers and then you can restart the container from the UI.

---


## 🧑‍💻 Development Workflow

- Place your custom modules inside **`custom_addons/`**.
- Place enterprise modules (if licensed) inside **`enterprise_addons/`**.
- Restart Odoo to detect new modules:
  ```bash
  docker compose restart web
  ```

---

## 🖥️ Cross-Platform Notes

- **Linux/macOS**: works out of the box with Docker Desktop or Podman.  
- **Windows**: use **Docker Desktop + WSL2** for best performance.  
  - Make sure to clone the repo into a **WSL2 filesystem** (`~/projects/odoo18/`) instead of Windows `C:` drive for faster volume performance.  

---