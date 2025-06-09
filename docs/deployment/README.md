# Deployment Guide

This guide covers various deployment options for CogniVerve-AI, from local development to production cloud deployments.

## Quick Start

The fastest way to deploy CogniVerve-AI is using our deployment script:

```bash
# Local deployment with Docker Compose
./scripts/deploy.sh local

# Kubernetes deployment
./scripts/deploy.sh k8s

# AWS deployment
./scripts/deploy.sh aws

# Google Cloud deployment
./scripts/deploy.sh gcp
```

## Prerequisites

### Required Software
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **kubectl** (for Kubernetes deployments)
- **Terraform** (for cloud infrastructure)
- **Git** for cloning the repository

### Required Accounts
- **Stripe** account for payment processing
- **OpenAI** API key for AI models
- Cloud provider account (AWS, GCP, or Azure)

## Environment Configuration

### Backend Environment Variables

Create `backend/.env` from the template:

```bash
cp backend/.env.example backend/.env
```

Configure the following variables:

```bash
# Database
DATABASE_URL=postgresql://cogniverve:password@postgres:5432/cogniverve_db
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Providers
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
STRIPE_SECRET_KEY=sk_test_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Environment
ENVIRONMENT=production
DEBUG=false
FRONTEND_URL=https://your-domain.com
```

### Frontend Environment Variables

Create `frontend/.env.local`:

```bash
VITE_API_URL=https://api.your-domain.com
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
```

## Local Development

### Docker Compose Deployment

1. **Clone and configure**:
   ```bash
   git clone https://github.com/yourusername/cogniverve-ai.git
   cd cogniverve-ai
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configuration
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Verify deployment**:
   ```bash
   # Check service status
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   
   # Test health endpoints
   curl http://localhost:8000/health
   ```

4. **Access applications**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Grafana: http://localhost:3001 (admin/admin)
   - Prometheus: http://localhost:9090

### Manual Development Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up database
createdb cogniverve_db
python -c "from app.core.database import engine, Base; Base.metadata.create_all(bind=engine)"

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local
npm run dev
```

## Production Deployment

### Docker Production Build

1. **Build production images**:
   ```bash
   # Backend
   docker build -t cogniverve/backend:latest ./backend
   
   # Frontend
   docker build -t cogniverve/frontend:latest ./frontend
   ```

2. **Push to registry**:
   ```bash
   docker push cogniverve/backend:latest
   docker push cogniverve/frontend:latest
   ```

### Kubernetes Deployment

#### Prerequisites
- Kubernetes cluster (1.20+)
- kubectl configured
- Ingress controller installed
- Cert-manager for SSL (optional)

#### Deploy to Kubernetes

1. **Create namespace**:
   ```bash
   kubectl create namespace cogniverve
   ```

2. **Configure secrets**:
   ```bash
   kubectl create secret generic cogniverve-secrets \
     --from-literal=database-url="postgresql://..." \
     --from-literal=secret-key="your-secret-key" \
     --from-literal=openai-api-key="sk-..." \
     --from-literal=stripe-secret-key="sk_test_..." \
     -n cogniverve
   ```

3. **Deploy infrastructure**:
   ```bash
   kubectl apply -f k8s/infrastructure.yaml -n cogniverve
   ```

4. **Wait for database**:
   ```bash
   kubectl wait --for=condition=ready pod -l app=postgres -n cogniverve --timeout=300s
   ```

5. **Deploy application**:
   ```bash
   kubectl apply -f k8s/deployment.yaml -n cogniverve
   ```

6. **Verify deployment**:
   ```bash
   kubectl get pods -n cogniverve
   kubectl get services -n cogniverve
   kubectl get ingress -n cogniverve
   ```

#### Kubernetes Configuration Files

**Infrastructure (k8s/infrastructure.yaml)**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cogniverve-secrets
type: Opaque
data:
  database-url: <base64-encoded-url>
  secret-key: <base64-encoded-key>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: cogniverve_db
        - name: POSTGRES_USER
          value: cogniverve
        - name: POSTGRES_PASSWORD
          value: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
```

### AWS Deployment

#### Using AWS ECS

1. **Create ECS cluster**:
   ```bash
   aws ecs create-cluster --cluster-name cogniverve-cluster
   ```

2. **Create task definitions**:
   ```json
   {
     "family": "cogniverve-backend",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "backend",
         "image": "cogniverve/backend:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "DATABASE_URL",
             "value": "postgresql://..."
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/cogniverve-backend",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

3. **Create services**:
   ```bash
   aws ecs create-service \
     --cluster cogniverve-cluster \
     --service-name cogniverve-backend \
     --task-definition cogniverve-backend \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
   ```

#### Using Terraform

```hcl
# terraform/aws/main.tf
provider "aws" {
  region = var.aws_region
}

resource "aws_ecs_cluster" "cogniverve" {
  name = "cogniverve-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "cogniverve-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  
  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "cogniverve/backend:latest"
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "DATABASE_URL"
          value = "postgresql://..."
        }
      ]
    }
  ])
}
```

### Google Cloud Deployment

#### Using Cloud Run

1. **Build and push images**:
   ```bash
   # Configure Docker for GCR
   gcloud auth configure-docker
   
   # Build and push
   docker build -t gcr.io/PROJECT_ID/cogniverve-backend ./backend
   docker push gcr.io/PROJECT_ID/cogniverve-backend
   
   docker build -t gcr.io/PROJECT_ID/cogniverve-frontend ./frontend
   docker push gcr.io/PROJECT_ID/cogniverve-frontend
   ```

2. **Deploy to Cloud Run**:
   ```bash
   # Deploy backend
   gcloud run deploy cogniverve-backend \
     --image gcr.io/PROJECT_ID/cogniverve-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="DATABASE_URL=postgresql://..."
   
   # Deploy frontend
   gcloud run deploy cogniverve-frontend \
     --image gcr.io/PROJECT_ID/cogniverve-frontend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. **Set up Cloud SQL**:
   ```bash
   gcloud sql instances create cogniverve-db \
     --database-version=POSTGRES_13 \
     --tier=db-f1-micro \
     --region=us-central1
   
   gcloud sql databases create cogniverve \
     --instance=cogniverve-db
   ```

## SSL/TLS Configuration

### Using Let's Encrypt with Nginx

1. **Install Certbot**:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   ```

2. **Obtain certificate**:
   ```bash
   sudo certbot --nginx -d your-domain.com -d api.your-domain.com
   ```

3. **Auto-renewal**:
   ```bash
   sudo crontab -e
   # Add: 0 12 * * * /usr/bin/certbot renew --quiet
   ```

### Using Cloud Provider SSL

#### AWS Application Load Balancer
```bash
aws elbv2 create-load-balancer \
  --name cogniverve-alb \
  --subnets subnet-12345 subnet-67890 \
  --security-groups sg-12345
```

#### Google Cloud Load Balancer
```bash
gcloud compute ssl-certificates create cogniverve-ssl \
  --domains=your-domain.com,api.your-domain.com
```

## Monitoring and Logging

### Prometheus and Grafana

Included in Docker Compose:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

### Cloud Monitoring

#### AWS CloudWatch
```bash
aws logs create-log-group --log-group-name /ecs/cogniverve-backend
```

#### Google Cloud Monitoring
```bash
gcloud logging sinks create cogniverve-sink \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/cogniverve_logs
```

## Backup and Recovery

### Database Backups

#### Automated PostgreSQL Backups
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > "$BACKUP_DIR/cogniverve_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "cogniverve_*.sql" -mtime +7 -delete
```

#### Cloud Storage Backups
```bash
# AWS S3
aws s3 cp backup.sql s3://cogniverve-backups/

# Google Cloud Storage
gsutil cp backup.sql gs://cogniverve-backups/
```

### Disaster Recovery

1. **Database Recovery**:
   ```bash
   psql $DATABASE_URL < backup.sql
   ```

2. **Application Recovery**:
   ```bash
   # Redeploy from backup images
   docker-compose up -d
   ```

## Performance Optimization

### Database Optimization

1. **Connection Pooling**:
   ```python
   # In backend/app/core/database.py
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_pre_ping=True
   )
   ```

2. **Indexing**:
   ```sql
   CREATE INDEX idx_users_email ON users(email);
   CREATE INDEX idx_tasks_status ON tasks(status);
   CREATE INDEX idx_conversations_user_id ON conversations(user_id);
   ```

### Caching

1. **Redis Configuration**:
   ```python
   # Cache frequently accessed data
   @cache.memoize(timeout=300)
   def get_user_agents(user_id):
       return db.query(Agent).filter(Agent.user_id == user_id).all()
   ```

2. **CDN Setup**:
   ```bash
   # CloudFlare, AWS CloudFront, or Google Cloud CDN
   # Configure for static assets and API responses
   ```

## Security Considerations

### Network Security

1. **Firewall Rules**:
   ```bash
   # Allow only necessary ports
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw allow 22/tcp
   ufw enable
   ```

2. **VPC Configuration**:
   - Private subnets for databases
   - Public subnets for load balancers
   - NAT gateways for outbound traffic

### Application Security

1. **Environment Variables**:
   ```bash
   # Never commit secrets to git
   # Use secret management services
   # Rotate keys regularly
   ```

2. **Rate Limiting**:
   ```nginx
   # In nginx.conf
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
   limit_req zone=api burst=20 nodelay;
   ```

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database status
docker-compose logs postgres

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

#### Memory Issues
```bash
# Check memory usage
docker stats

# Increase memory limits
# In docker-compose.yml:
# mem_limit: 2g
```

#### SSL Certificate Issues
```bash
# Check certificate status
openssl x509 -in cert.pem -text -noout

# Renew Let's Encrypt
sudo certbot renew
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database health
pg_isready -h localhost -p 5432

# Redis health
redis-cli ping
```

## Scaling

### Horizontal Scaling

1. **Load Balancer Configuration**:
   ```nginx
   upstream backend {
       server backend1:8000;
       server backend2:8000;
       server backend3:8000;
   }
   ```

2. **Database Scaling**:
   - Read replicas for read-heavy workloads
   - Connection pooling
   - Query optimization

### Auto-scaling

#### Kubernetes HPA
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cogniverve-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cogniverve-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Support

For deployment support:
- Email: devops@cogniverve.ai
- Discord: #deployment channel
- Documentation: https://docs.cogniverve.ai/deployment

