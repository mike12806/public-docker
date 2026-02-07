# Public Docker Images

A collection of custom Docker images published to GitHub Container Registry (GHCR) for personal and community use. These images are automatically built, tested, and published via GitHub Actions workflows.

## 📦 Available Images

All images are published to `ghcr.io/mike12806/public-docker/[image-name]` and are available in the following variants:
- `latest` - Latest build from the main branch
- `v*.*.*` - Semantic versioned releases
- `<git-sha>` - Specific commit builds

### 🏃 Runner

**Image:** `ghcr.io/mike12806/public-docker/runner`

A feature-rich self-hosted GitHub Actions runner image designed for Kubernetes environments. This image extends the official GitHub Actions runner with pre-installed tools and dependencies commonly needed in CI/CD workflows.

**Base Image:** `ghcr.io/actions/actions-runner`

**Included Tools:**
- **CodeQL** - Pre-installed in toolcache layout for security scanning
- **AWS CLI v2** - For AWS resource management
- **Docker Compose Plugin** - For multi-container applications
- **Python 3** with pip, venv, and pipx
- **Ansible** (via pipx) - For configuration management
- **Linode CLI** (via pipx) - For Linode cloud management
- **Backblaze B2 CLI** - For B2 cloud storage operations
- **yq** - YAML processor for parsing and manipulating YAML files
- **jq** - JSON processor (from base image)
- **psql** - PostgreSQL client for database operations
- **sshpass** - Non-interactive SSH password authentication
- **rsync** - File synchronization utility
- **curl, wget** - HTTP clients for downloading files
- **OpenSSH client** - For SSH operations

**Key Features:**
- CodeQL pre-installed in the standard toolcache layout (`/opt/hostedtoolcache/CodeQL`)
- Toolcache directory owned by runner user for proper permissions
- Python packages installed via pipx for isolation
- Optimized for self-hosted runners in Kubernetes

**Usage Example:**
```yaml
# In your Kubernetes runner deployment
spec:
  containers:
  - name: runner
    image: ghcr.io/mike12806/public-docker/runner:latest
```

**Use Cases:**
- Self-hosted GitHub Actions runners
- CI/CD pipelines requiring AWS, Ansible, or CodeQL
- Security scanning workflows with CodeQL
- Infrastructure automation tasks

---

### ⎈ Kubectl

**Image:** `ghcr.io/mike12806/public-docker/kubectl`

A kubectl image with Redis tools for Kubernetes operations that require Redis interactions.

**Base Image:** `docker.io/alpine/kubectl`

**Included Tools:**
- **kubectl** - Kubernetes command-line tool
- **redis-cli** - Redis command-line interface for Redis operations
- **redis-server** - Redis server (available but not typically run in this image)
- **curl** - HTTP client for API calls and downloads (included in base image)

**Usage Example:**
```yaml
# In a Kubernetes Job
apiVersion: batch/v1
kind: Job
metadata:
  name: kubectl-redis-job
spec:
  template:
    spec:
      containers:
      - name: kubectl
        image: ghcr.io/mike12806/public-docker/kubectl:latest
        command: ["kubectl", "get", "pods"]
      restartPolicy: Never
```

**Use Cases:**
- Kubernetes maintenance jobs with Redis operations
- CI/CD pipelines for Kubernetes deployments
- Scripted Kubernetes operations requiring Redis client access
- Database migration or initialization scripts that interact with both Kubernetes and Redis

---

### 🌐 Curl

**Image:** `ghcr.io/mike12806/public-docker/curl`

A lightweight Alpine-based image with curl, jq, and bash for making HTTP requests and processing JSON responses.

**Base Image:** `docker.io/alpine`

**Included Tools:**
- **curl** - Command-line tool for transferring data with URLs
- **jq** - Lightweight and flexible command-line JSON processor
- **bash** - Bourne Again SHell for scripting

**Usage Example:**
```yaml
# In a Kubernetes Job or CI/CD pipeline
apiVersion: batch/v1
kind: Job
metadata:
  name: api-check
spec:
  template:
    spec:
      containers:
      - name: curl
        image: ghcr.io/mike12806/public-docker/curl:latest
        command: ["sh", "-c"]
        args:
          - |
            curl -s https://api.example.com/data | jq '.results'
      restartPolicy: Never
```

**Use Cases:**
- API health checks and monitoring
- JSON data processing in CI/CD pipelines
- Lightweight HTTP client for scripts and automation
- Quick data fetching and transformation tasks

---

### 🏠 Home Assistant

**Image:** `ghcr.io/mike12806/public-docker/home-assistant`

A custom Home Assistant image with DNS fixes for common networking issues. This image patches the aiodns library to disable EDNS cookies by default and optionally disables IPv6 connections to prevent `Network unreachable` errors on IPv4-only networks.

**Base Image:** `ghcr.io/home-assistant/home-assistant`

**Key Features:**
- **EDNS cookie fix** — Patches aiodns to disable EDNS cookies by default, preventing DNS timeouts with forwarding resolvers (dnsmasq, pihole, unbound)
- **IPv6 disable support** — Set `DISABLE_IPV6=true` to force all connections to IPv4, preventing `Network unreachable` errors on networks without IPv6 connectivity
- Based on upstream Home Assistant core with minimal modifications
- Compatible with standard Home Assistant configuration and add-ons

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `DISABLE_IPV6` | _(unset)_ | Set to `true`, `1`, or `yes` to force all network connections to IPv4 only. Prevents `[Errno 101] Network unreachable` errors when DNS returns AAAA records but the network has no IPv6 connectivity. |

**Technical Details:**

The image applies runtime patches to `homeassistant/runner.py` at startup:

1. **EDNS fix** — Wraps the aiodns query method to set EDNS flags to `0` by default. This resolves issues introduced in c-ares 1.33.0+ where EDNS cookies are enabled by default and cause timeouts with certain DNS server configurations.

2. **IPv6 disable** (opt-in via `DISABLE_IPV6`) — Monkey-patches `socket.getaddrinfo` to force `AF_INET` for all lookups (covers `requests`, `urllib3`, and all stdlib-based resolution) and patches `aiohttp.TCPConnector` to default to `AF_INET` (covers `aiohttp`, `aiodns`, and `c-ares` async resolution). This is necessary because kernel-level IPv6 disable (`sysctl net.ipv6.conf.all.disable_ipv6`) is often unavailable in containers, but Python still resolves and attempts AAAA records.

**Usage Example:**
```yaml
# In docker-compose.yml or Kubernetes
version: '3'
services:
  homeassistant:
    image: ghcr.io/mike12806/public-docker/home-assistant:latest
    container_name: homeassistant
    privileged: true
    restart: unless-stopped
    environment:
      - TZ=America/New_York
      - DISABLE_IPV6=true  # Optional: force IPv4-only connections
    volumes:
      - ./config:/config
    network_mode: host
```

```yaml
# In Kubernetes
env:
- name: TZ
  value: America/New_York
- name: DISABLE_IPV6
  value: "true"
```

**Use Cases:**
- Running Home Assistant with DNS servers that don't properly handle EDNS cookies
- Environments using dnsmasq, pihole, or unbound as DNS forwarders
- Networks without IPv6 connectivity (common in home lab Kubernetes clusters)
- Resolving `Network unreachable` errors for integrations like Tuya, Rheem/EcoNet, Ring (PubNub), HACS, and mobile_app notifications
- Alternative to manual DNS configuration workarounds

---

## 🔨 Building Images

Images are automatically built and published when:
- Changes are pushed to the `Dockerfiles/**` directory on the main branch
- Manually triggered via workflow_dispatch
- Daily via scheduled cron job at 10:00 AM UTC

The build process:
1. Discovers all Dockerfiles in the `Dockerfiles/` directory
2. Builds each image using Docker Buildx
3. Tags with `latest`, semantic version, and git SHA
4. Pushes to GitHub Container Registry
5. Creates a GitHub release with changelog

## 🧪 Testing

Pull requests automatically trigger Docker build verification:
- All Dockerfiles are discovered and built
- Smoke tests are run to verify basic functionality
- Runner image tests verify Python and CodeQL installations
- Other images test basic shell functionality

## 🔄 Dependency Management

This repository uses [Renovate](https://docs.renovatebot.com/) for automated dependency updates:
- Base images in Dockerfiles are automatically updated
- Minor and patch updates are auto-merged
- Major updates require manual review
- Daily checks for new versions

## 📝 Contributing

To add a new Docker image:
1. Create a new directory under `Dockerfiles/[YourImageName]/`
2. Add your `Dockerfile` in that directory
3. Optionally add a `README` file with image-specific documentation
4. Submit a pull request
5. The CI will automatically build and test your image
6. Once merged, the image will be published to GHCR

## 📄 License

This repository is maintained by [@mike12806](https://github.com/mike12806). Individual Docker images may contain software with their own licenses. Please review the Dockerfiles for specific licensing information.

## 🔗 Related Links

- [GitHub Container Registry](https://github.com/orgs/mike12806/packages?repo_name=public-docker)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [CodeQL Documentation](https://codeql.github.com/docs/)
