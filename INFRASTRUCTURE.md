# LaundryAdvisor Infrastructure Guide

## Overview

LaundryAdvisor is a Django web application migrated from Render (a managed PaaS) to a
self-hosted AWS EC2 instance. The deployment is fully automated using GitHub Actions for
CI/CD and Ansible for server provisioning and deployment.

---

## Architecture

```
Developer (local machine)
        │
        │  git push
        ▼
  GitHub (wardrobewise-infra repo)
        │
        │  triggers GitHub Actions on every push to master
        ▼
  GitHub Actions Runner (temporary Ubuntu VM)
        │
        ├── checks out code
        ├── docker build  (uses Dockerfile in repo)
        └── docker push ──────────────────────────────────────┐
                                                              │
                                                    AWS ECR (image registry)
                                                              │
                                                    (image stored here)
                                                              │
  Developer runs Ansible deploy playbook ───────────────────►│
        │                                                     │
        ▼                                                     │
  AWS EC2 Instance (3.84.187.52)  ◄── docker pull ──────────┘
        │
        ├── Nginx (port 80) — reverse proxy
        └── Docker Compose
              ├── Django/Gunicorn (port 8000)
              └── PostgreSQL
```

---

## Technology Choices and Why

### AWS EC2
A virtual machine running Amazon Linux 2023. Chosen over managed platforms like Render or
Heroku for full control over the environment, lower long-term cost, and to demonstrate
infrastructure skills. The instance is a `t2.micro` (free tier eligible).

### Docker + Docker Compose
The application and its dependencies (Python, Gunicorn, libraries) are packaged into a
Docker image. This guarantees the app runs identically in development and production.
Docker Compose orchestrates two containers:
- **web** — Django served by Gunicorn
- **db** — PostgreSQL database

### AWS ECR (Elastic Container Registry)
AWS's private Docker image registry. GitHub Actions builds the image and pushes it here.
The EC2 instance pulls from ECR when deploying. ECR was chosen over Docker Hub because
the app already runs in AWS, keeping image pulls within the same network (faster, no
egress costs).

### Nginx
A reverse proxy that sits in front of Gunicorn. Handles:
- Accepting HTTP connections on port 80
- Forwarding requests to Django running on port 8000 (not exposed publicly)
- Setting request headers (`X-Real-IP`, `X-Forwarded-For`) so Django sees the real client IP
- Enforcing a 10MB upload limit for care label photos

Gunicorn is a Python WSGI server — it is not designed to handle raw internet traffic
directly. Nginx handles that and passes clean requests through.

### GitHub Actions
CI/CD pipeline defined in `.github/workflows/deploy.yml`. On every push to `master`:
1. Checks out the code onto a temporary GitHub-hosted Ubuntu runner
2. Authenticates to AWS using credentials stored as GitHub Secrets
3. Builds a Docker image from the `Dockerfile`
4. Pushes the image to ECR tagged as `latest`

This separates building from deploying — the server never needs the source code, only
the pre-built image.

### Ansible
An infrastructure automation tool that SSHes into the EC2 instance and runs tasks
defined in YAML playbooks. Two playbooks:

**provision.yml** (run once when setting up a new server):
- Installs Docker and the Docker Compose plugin
- Installs and configures Nginx
- Creates the app directory

**deploy.yml** (run on every deployment):
- Writes the `.env.prod` file with secrets (database URL, API keys, etc.)
- Copies the `docker-compose.prod.yml` to the server
- Logs Docker into ECR using the EC2 IAM role
- Pulls the latest image from ECR
- Starts the containers with `docker compose up -d`
- Reloads Nginx

### Ansible Vault
Sensitive values (Django secret key, database password, OpenAI API key, AWS credentials)
are stored encrypted in `ansible/vault.yml` using AES-256 encryption. The vault password
is never stored anywhere — only held by the developer. This means secrets can be safely
committed to the repository.

### IAM Roles (No Long-Lived Credentials on the Server)
The EC2 instance has an **IAM instance profile** (`laundry-advisor-ec2-role`) attached,
granting it read-only access to ECR. When `aws ecr get-login-password` runs on the
server, it uses this role automatically — no `AWS_ACCESS_KEY_ID` or
`AWS_SECRET_ACCESS_KEY` is stored on the server for ECR access.

A separate IAM user (`github-actions-ecr`) with ECR push permissions exists only for
GitHub Actions. Its credentials are stored as GitHub Secrets, not in the codebase.

### AWS S3
Media files (care label photos uploaded by users) are stored in an S3 bucket using
`django-storages`. This is stateless storage — the EC2 instance can be replaced or
restarted without losing any uploaded files.

---

## Security Decisions

| Decision | Reason |
|---|---|
| No HTTPS | No custom domain; accessing via raw IP — SSL certificates require a domain name |
| IAM role on EC2 instead of access keys | Eliminates long-lived credentials on the server |
| Ansible Vault for secrets | Secrets never appear in plaintext in the repo or environment |
| Security group limits port 22 to My IP | SSH access restricted; port 80 open to the world |
| `chmod 600` on SSH private key | SSH refuses to use keys readable by other users |

---

## Deployment Flow (Day-to-Day)

1. Make code changes locally
2. `git push wardrobewise master` — GitHub Actions automatically builds and pushes a new
   Docker image to ECR (takes ~2-3 minutes)
3. Run the Ansible deploy playbook to pull the new image and restart the app:
   ```
   ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini \
     --private-key ~/.ssh/laundry-advisor.pem --ask-vault-pass -e @vault.yml
   ```

---

## Key Files

| File | Purpose |
|---|---|
| `Dockerfile` | Defines how the Django app image is built |
| `docker-compose.prod.yml` | Defines the web + db containers for production |
| `nginx/nginx.conf` | Nginx reverse proxy configuration |
| `ansible/playbooks/provision.yml` | One-time server setup playbook |
| `ansible/playbooks/deploy.yml` | Deployment playbook (run on every release) |
| `ansible/inventory/hosts.ini` | EC2 IP address for Ansible to connect to |
| `ansible/vault.yml` | AES-256 encrypted secrets |
| `.github/workflows/deploy.yml` | GitHub Actions CI/CD pipeline |

---

## AWS Resources Summary

| Resource | Name/Value | Purpose |
|---|---|---|
| EC2 Instance | `3.84.187.52` (t2.micro, Amazon Linux 2023) | Runs the application |
| Security Group | `laundry-advisor` | Firewall: allows SSH (22) and HTTP (80) |
| IAM Role | `laundry-advisor-ec2-role` | Lets EC2 pull images from ECR |
| IAM User | `github-actions-ecr` | Lets GitHub Actions push images to ECR |
| ECR Repository | `013121026988.dkr.ecr.us-east-1.amazonaws.com/laundryadvisor` | Stores Docker images |
| S3 Bucket | configured via env var | Stores user-uploaded media files |
