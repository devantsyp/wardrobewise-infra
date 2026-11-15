# WardrobeWise — Infrastructure

Self-hosted deployment of [WardrobeWise](https://github.com/camronpatel/LaundryAdvisor) on AWS EC2.

## Stack

- **EC2** (Amazon Linux 2023, t2.micro) — application server
- **Docker + Docker Compose** — containerized Django/Gunicorn + PostgreSQL
- **Nginx** — reverse proxy; TLS termination with Let's Encrypt certs (auto-renewed by a systemd timer)
- **AWS ECR** — Docker image registry
- **GitHub Actions** — on every push to `main`: builds the image, pushes it to ECR, and runs the Ansible deploy
- **Ansible** — provisions the server and deploys the application
- **UptimeRobot** — external HTTP monitoring of `/healthz/`, which checks the app *and* its database connection

## Deploying Updates

Push to `main`. That's it — the GitHub Actions workflow (`.github/workflows/deploy.yml`) runs two jobs:

1. **build-and-push** — builds the Docker image and pushes it to ECR
2. **deploy** — runs `ansible/playbooks/deploy.yml` against the EC2 instance, which writes `.env.prod` from the vault, pulls the new image, and restarts the containers

Verify with `curl http://<ec2-host>/healthz/` — expect `{"status": "ok", "database": "ok"}`.

### GitHub Secrets used by the pipeline

| Secret | Purpose |
|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | `github-actions-ecr` IAM user, pushes to ECR |
| `EC2_SSH_PRIVATE_KEY` | SSH key the deploy job uses to reach the instance |
| `ANSIBLE_VAULT_PASSWORD` | Decrypts `ansible/vault.yml` during deploy |

## When You Need Ansible Locally

Day-to-day deploys need nothing but `git push`. Run Ansible yourself (Linux/WSL) only to:

- **Provision a new or replacement instance** — `provision.yml` is not part of CI (see First-Time Setup)
- **Change a secret** — `ansible-vault edit ansible/vault.yml`, then commit and push; CI deploys it
- **Debug a failed deploy** — rerun the playbook locally with `-vvv` for faster iteration

## Prerequisites (local Ansible runs)

- Ansible installed (Linux/WSL)
- SSH key at `~/.ssh/laundry-advisor.pem`
- `ansible/vault.yml` created with your secrets (see below)

## First-Time Setup

**1. Provision the server** (run once on a fresh EC2 instance):

```bash
cd ansible
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook playbooks/provision.yml \
  -i inventory/hosts.ini \
  --private-key ~/.ssh/laundry-advisor.pem \
  --ask-vault-pass -e @vault.yml
```

**2. Deploy the application** — push to `main` to let CI deploy, or run it manually:

```bash
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook playbooks/deploy.yml \
  -i inventory/hosts.ini \
  --private-key ~/.ssh/laundry-advisor.pem \
  --ask-vault-pass -e @vault.yml
```

If the instance's IP changed, update `ansible/inventory/hosts.ini` (and `ec2_host` in the vault) before deploying.

## Vault Setup

Create `ansible/vault.yml` with:

```bash
ansible-vault create ansible/vault.yml
```

Required keys:

```yaml
secret_key: ""
ec2_host: ""
postgres_password: ""
aws_bucket: ""
aws_access_key_id: ""
aws_secret_access_key: ""
openai_api_key: ""
ecr_registry: ""
```

To edit later: `ansible-vault edit ansible/vault.yml`

## AWS Resources

| Resource | Purpose |
|---|---|
| EC2 instance | Runs the application |
| Security group `laundry-advisor` | Allows SSH (22), HTTP (80), HTTPS (443) |
| Elastic IP | Stable public IP the domain's DNS records point at |
| IAM role `laundry-advisor-ec2-role` | Keyless ECR pulls from EC2 |
| IAM user `github-actions-ecr` | GitHub Actions pushes to ECR |
| ECR repo `laundryadvisor` | Stores Docker images |
| S3 bucket | User-uploaded media files |
