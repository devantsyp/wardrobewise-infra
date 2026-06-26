# WardrobeWise — Infrastructure

Self-hosted deployment of [WardrobeWise](https://github.com/camronpatel/LaundryAdvisor) on AWS EC2.

## Stack

- **EC2** (Amazon Linux 2023, t2.micro) — application server
- **Docker + Docker Compose** — containerized Django/Gunicorn + PostgreSQL
- **Nginx** — reverse proxy on port 80
- **AWS ECR** — Docker image registry
- **GitHub Actions** — builds and pushes image to ECR on every push to `master`
- **Ansible** — provisions the server and deploys the application

## Prerequisites

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

**2. Deploy the application:**

```bash
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook playbooks/deploy.yml \
  -i inventory/hosts.ini \
  --private-key ~/.ssh/laundry-advisor.pem \
  --ask-vault-pass -e @vault.yml
```

## Deploying Updates

1. Push to `master` — GitHub Actions builds and pushes a new image to ECR automatically
2. Run the deploy playbook (step 2 above) to pull the new image and restart the app

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
| Security group `laundry-advisor` | Allows SSH (22) and HTTP (80) |
| IAM role `laundry-advisor-ec2-role` | Keyless ECR pulls from EC2 |
| IAM user `github-actions-ecr` | GitHub Actions pushes to ECR |
| ECR repo `laundryadvisor` | Stores Docker images |
| S3 bucket | User-uploaded media files |
