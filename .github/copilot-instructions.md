# GitHub Copilot Instructions for public-docker

## Repository Overview

This repository uses **GitOps principles** to manage Docker images for a Kubernetes-based homelab environment. All images are automatically built, versioned, and published to GitHub Container Registry (GHCR) through declarative workflows.

## GitOps Principles

### Core Philosophy
- **Declarative Configuration**: All infrastructure and image definitions are stored as code in this repository
- **Git as Single Source of Truth**: All changes go through Git, enabling audit trails and rollback capabilities
- **Automated Synchronization**: GitHub Actions automatically builds and publishes images when Dockerfiles change
- **Version Control Everything**: Every change is tracked, reviewed, and versioned

### Workflow Pattern
1. Make changes to Dockerfiles in the `Dockerfiles/` directory
2. Submit pull request for review
3. PR triggers automated builds and tests
4. Upon merge to main, images are built and pushed to GHCR with semantic versioning
5. Downstream Kubernetes clusters can reference these versioned images

## Docker Image Best Practices

### Image Organization
- Create separate directories under `Dockerfiles/` for each image
- Use lowercase names with hyphens (e.g., `home-assistant`, `kubectl`)
- Keep Dockerfiles focused and single-purpose
- Include inline comments for complex build steps

### Multi-Stage Builds
- Use multi-stage builds to reduce final image size
- Separate build dependencies from runtime dependencies
- Copy only necessary artifacts to final stage

### Base Image Selection
- Prefer official base images from trusted sources
- Use specific version tags, not `latest`, for reproducibility
- Consider Alpine Linux for smaller image sizes when appropriate
- For production runners, use official images (e.g., `actions-runner`)

### Layer Optimization
- Group related RUN commands to minimize layers
- Put frequently changing instructions at the end
- Leverage build cache effectively
- Clean up package manager caches in the same layer

### Security Practices
- Run containers as non-root users when possible
- Don't embed secrets or credentials in images
- Regularly update base images via Renovate
- Scan images for vulnerabilities (CodeQL integration available)

## Kubernetes Homelab Best Practices

### Image Versioning for K8s
- Use semantic versioning tags for stable deployments
- Tag images with: `latest`, semantic version (e.g., `v1.2.3`), and git SHA
- Pin specific versions in production manifests for reproducibility
- Use `latest` only for development environments

### Deployment Patterns
```yaml
# Production: Use specific version tags
spec:
  containers:
  - name: runner
    image: ghcr.io/mike12806/public-docker/runner:v1.2.3
    imagePullPolicy: IfNotPresent

# Development: Use latest with Always pull policy
spec:
  containers:
  - name: runner
    image: ghcr.io/mike12806/public-docker/runner:latest
    imagePullPolicy: Always
```

### Resource Management
- Set appropriate resource requests and limits
- Use horizontal pod autoscaling for workloads with variable load
- Consider node selectors or affinity for specialized workloads

### Configuration Management
- Use ConfigMaps for non-sensitive configuration
- Use Secrets (sealed or encrypted) for sensitive data
- Mount configuration as volumes rather than environment variables when possible
- Keep configuration separate from image definitions

### Image Pull Secrets
```yaml
# For private images (if needed)
imagePullSecrets:
- name: ghcr-credentials
```

## CI/CD Integration

### Automated Testing
- All Dockerfiles are tested on pull requests
- Smoke tests verify basic functionality
- Runner image tests verify toolchain installations

### Automated Releases
- Semantic versioning via mathieudutour/github-tag-action
- Automated changelog generation
- GitHub releases created for each version
- Images tagged with version, SHA, and latest

### Dependency Updates
- Renovate automatically updates base images
- Minor/patch updates auto-merge
- Major updates require manual review
- Daily checks for new versions

## Development Guidelines

### Adding New Images

1. Create directory structure:
```
Dockerfiles/
  YourImageName/
    Dockerfile
    README.md (optional)
```

2. Follow naming conventions:
   - Directory name determines image name
   - Use lowercase with hyphens
   - Be descriptive but concise

3. Write clear Dockerfile:
   - Comment purpose and rationale
   - Document any non-obvious build steps
   - Specify tool versions when critical

4. Update main README.md:
   - Add image to "Available Images" section
   - Include usage examples
   - Document included tools and features

### Modifying Existing Images

1. Make minimal, focused changes
2. Test locally before submitting PR:
   ```bash
   docker build -t test-image Dockerfiles/YourImage/
   docker run --rm test-image <validation-command>
   ```

3. Consider backward compatibility
4. Update documentation if behavior changes

### Pull Request Guidelines

- Provide clear description of changes
- Explain why changes are needed
- Include testing steps performed
- Link related issues if applicable
- Ensure CI checks pass before requesting review

## Kubernetes-Specific Considerations

### Runner Images
- Designed for self-hosted GitHub Actions runners in K8s
- Pre-installed tooling reduces workflow execution time
- Consider memory/CPU requirements for CodeQL and builds

### Utility Images (kubectl, curl)
- Use in Kubernetes Jobs for automation tasks
- Keep lightweight for fast scheduling
- Mount ServiceAccount tokens for K8s API access

### Application Images (home-assistant)
- May require privileged access or host network mode
- Document networking requirements clearly
- Consider storage requirements and persistent volumes

## ArgoCD/GitOps Tool Integration

While this repository manages Docker images, downstream GitOps repositories should:
- Reference images by specific version tags
- Use Renovate or Dependabot to track image updates
- Implement promotion workflows (dev → staging → prod)
- Keep Kubernetes manifests in separate repositories
- Use ArgoCD, FluxCD, or similar tools for cluster synchronization

### Image Update Automation
```yaml
# In your ArgoCD/FluxCD repo
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: runner-policy
spec:
  imageRepositoryRef:
    name: runner
  policy:
    semver:
      range: 1.x.x  # Auto-update patch versions
```

## Common Patterns

### Self-Hosted Runners
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: github-runner
spec:
  template:
    spec:
      containers:
      - name: runner
        image: ghcr.io/mike12806/public-docker/runner:v1.0.0
        env:
        - name: RUNNER_TOKEN
          valueFrom:
            secretKeyRef:
              name: github-runner-token
              key: token
```

### Kubernetes Jobs
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-backup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: ghcr.io/mike12806/public-docker/kubectl:latest
            command: ["/bin/sh", "-c"]
            args:
            - |
              kubectl get all -A > /backup/cluster-state.yaml
          restartPolicy: OnFailure
```

## Security Considerations

### Image Scanning
- Enable GitHub Advanced Security for CodeQL scanning
- Review Renovate PRs for security updates promptly
- Monitor GitHub Security Advisories

### Secret Management
- Never commit secrets to Dockerfiles
- Use build-time secrets with BuildKit
- Reference secrets via environment variables or mounted files

### Supply Chain Security
- Verify base image signatures when possible
- Pin base images to specific digests for critical images
- Review Renovate updates carefully for unexpected changes

## Troubleshooting

### Build Failures
1. Check GitHub Actions logs for specific errors
2. Test locally with same base image versions
3. Verify syntax with `docker build --dry-run`

### Image Pull Errors
1. Verify image exists in GHCR
2. Check Kubernetes imagePullSecrets
3. Confirm network access to ghcr.io

### Runtime Issues
1. Check container logs: `kubectl logs <pod-name>`
2. Exec into container: `kubectl exec -it <pod-name> -- /bin/sh`
3. Verify environment variables and mounted volumes

## Additional Resources

- [GitOps Principles](https://opengitops.dev/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Renovate Documentation](https://docs.renovatebot.com/)
