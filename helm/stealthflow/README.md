# StealthFlow Helm Chart

This Helm chart deploys StealthFlow, a multi-layer anti-censorship system with REALITY/Trojan protocols and P2P fallback capabilities, on a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- cert-manager (for automatic SSL certificate management)
- Ingress controller (nginx recommended)

## Installation

### Add the Helm repository

```bash
helm repo add stealthflow https://charts.stealthflow.org
helm repo update
```

### Install the chart

```bash
helm install stealthflow stealthflow/stealthflow \
  --namespace stealthflow \
  --create-namespace \
  --set config.domain=your-domain.com \
  --set config.email=admin@your-domain.com
```

### Install with custom values

```bash
# Create a values file
cat > values.yaml << EOF
config:
  domain: "proxy.example.com"
  email: "admin@example.com"

ingress:
  hosts:
    - host: proxy.example.com
      paths:
        - path: /
          pathType: Prefix
    - host: cdn1.proxy.example.com
      paths:
        - path: /
          pathType: Prefix

monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true

persistence:
  enabled: true
  size:
    config: 2Gi
    logs: 10Gi
    certs: 2Gi

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi
EOF

# Install with custom values
helm install stealthflow stealthflow/stealthflow \
  --namespace stealthflow \
  --create-namespace \
  --values values.yaml
```

## Configuration

### Essential Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `config.domain` | Primary domain name | `example.com` |
| `config.email` | Email for SSL certificates | `admin@example.com` |
| `secrets.uuid` | VLESS UUID (auto-generated if empty) | `""` |
| `secrets.trojanPassword` | Trojan password (auto-generated if empty) | `""` |

### Service Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `service.type` | Kubernetes service type | `LoadBalancer` |
| `service.ports.http` | HTTP port | `80` |
| `service.ports.https` | HTTPS port | `443` |
| `service.ports.reality` | REALITY port | `444` |

### Ingress Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.annotations` | Ingress annotations | See values.yaml |
| `ingress.hosts` | Ingress hosts configuration | See values.yaml |
| `ingress.tls` | TLS configuration | See values.yaml |

### Monitoring Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `monitoring.enabled` | Enable monitoring stack | `false` |
| `monitoring.prometheus.enabled` | Enable Prometheus | `false` |
| `monitoring.grafana.enabled` | Enable Grafana | `false` |
| `monitoring.grafana.adminPassword` | Grafana admin password | `stealthflow123` |

### Persistence Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistent storage | `true` |
| `persistence.storageClass` | Storage class name | `""` |
| `persistence.size.config` | Config volume size | `1Gi` |
| `persistence.size.logs` | Logs volume size | `5Gi` |
| `persistence.size.certs` | Certificates volume size | `1Gi` |

### Resource Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `250m` |
| `resources.requests.memory` | Memory request | `256Mi` |

### Security Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `podSecurityContext.fsGroup` | Pod security context FS group | `1000` |
| `securityContext.runAsUser` | Container security context user ID | `1000` |
| `securityContext.runAsNonRoot` | Run as non-root user | `true` |
| `networkPolicy.enabled` | Enable network policies | `true` |

## Upgrading

### Upgrade to a new version

```bash
helm repo update
helm upgrade stealthflow stealthflow/stealthflow \
  --namespace stealthflow
```

### Upgrade with new values

```bash
helm upgrade stealthflow stealthflow/stealthflow \
  --namespace stealthflow \
  --values values.yaml
```

## Uninstalling

```bash
helm uninstall stealthflow --namespace stealthflow
```

To also remove the namespace:

```bash
kubectl delete namespace stealthflow
```

## Troubleshooting

### Check pod status

```bash
kubectl get pods -n stealthflow
```

### View logs

```bash
# Server logs
kubectl logs -l app.kubernetes.io/name=stealthflow -n stealthflow

# Signaling server logs
kubectl logs -l app.kubernetes.io/name=stealthflow-signaling -n stealthflow
```

### Check services

```bash
kubectl get svc -n stealthflow
```

### Check ingress

```bash
kubectl get ingress -n stealthflow
```

### Debug connectivity

```bash
# Port forward for local testing
kubectl port-forward svc/stealthflow-server-service 8080:80 -n stealthflow

# Test health endpoint
kubectl port-forward svc/stealthflow-health-service 9000:9000 -n stealthflow
curl http://localhost:9000/health
```

### Common Issues

#### 1. SSL Certificate Issues

If SSL certificates are not being issued:

```bash
# Check cert-manager
kubectl get certificaterequests -n stealthflow
kubectl get certificates -n stealthflow

# Check ingress annotations
kubectl describe ingress stealthflow-ingress -n stealthflow
```

#### 2. Service Not Accessible

If the service is not accessible externally:

```bash
# Check service type and external IP
kubectl get svc stealthflow-server-service -n stealthflow

# Check ingress controller
kubectl get pods -n ingress-nginx
```

#### 3. Pod Startup Issues

If pods are not starting:

```bash
# Check pod events
kubectl describe pod <pod-name> -n stealthflow

# Check resource constraints
kubectl top pods -n stealthflow
```

## Security Considerations

1. **Secrets Management**: Use external secret management systems like HashiCorp Vault or AWS Secrets Manager for production deployments.

2. **Network Policies**: Enable network policies to restrict pod-to-pod communication.

3. **Pod Security**: Review and adjust pod security contexts based on your security requirements.

4. **Resource Limits**: Set appropriate resource limits to prevent resource exhaustion.

5. **Image Security**: Regularly scan container images for vulnerabilities.

## Monitoring and Observability

### Prometheus Metrics

The chart exposes metrics at `/metrics` endpoint for Prometheus scraping:

- `stealthflow_up`: Service availability
- `stealthflow_uptime_seconds`: Service uptime
- `stealthflow_connections_total`: Total connections

### Grafana Dashboards

If monitoring is enabled, Grafana dashboards are automatically provisioned:

- StealthFlow Overview Dashboard
- System Metrics Dashboard
- Network Traffic Dashboard

### Alerting

Configure alerting rules for:

- Service downtime
- High resource usage
- SSL certificate expiration
- Failed connections

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `helm lint` and `helm template`
5. Submit a pull request

## License

This chart is licensed under the MIT License. See LICENSE file for details.
