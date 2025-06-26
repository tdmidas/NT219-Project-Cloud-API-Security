#!/bin/bash

# Build and Push Docker Images to Single ECR Registry
# Usage: ./build-and-push.sh [ECR_REGISTRY] [AWS_REGION] [IMAGE_TAG]

set -e

# Configuration
ECR_REGISTRY=${1:-"323619679467.dkr.ecr.us-east-1.amazonaws.com/voux-microservice"}
AWS_REGION=${2:-"us-east-1"}
IMAGE_TAG=${3:-"latest"}

echo "🚀 Building and pushing Docker images to single ECR registry..."
echo "Registry: $ECR_REGISTRY"
echo "Region: $AWS_REGION"
echo "Tag: $IMAGE_TAG"

# Microservices to build
SERVICES=(
    "api-gateway"
    "auth-service"
    "user-service"
    "voucher-service"
    "cart-service"
)

# Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Function to build and push a service
build_and_push_service() {
    local service=$1
    local service_dir="../microservice-python"
    local dockerfile_path="$service_dir/$service/Dockerfile"
    local local_image_name="voux-$service"
    local service_tag="$service-$IMAGE_TAG"
    local full_image_name="$ECR_REGISTRY:$service_tag"
    
    echo ""
    echo "📦 Building $service..."
    
    # Check if service directory exists
    if [[ ! -d "$service_dir/$service" ]]; then
        echo "❌ Service directory not found: $service_dir/$service"
        return 1
    fi
    
    # Check if Dockerfile exists
    if [[ ! -f "$dockerfile_path" ]]; then
        echo "❌ Dockerfile not found: $dockerfile_path"
        return 1
    fi
    
    # Build Docker image from microservice-python directory with service-specific dockerfile
    echo "Building: docker build -f $service/Dockerfile -t $local_image_name $service_dir"
    cd $service_dir
    docker build -f $service/Dockerfile -t $local_image_name .
    cd - > /dev/null
    
    # Tag for ECR with service-specific tag
    echo "Tagging: docker tag $local_image_name $full_image_name"
    docker tag $local_image_name $full_image_name
    
    # Push to ECR
    echo "Pushing: docker push $full_image_name"
    docker push $full_image_name
    
    echo "✅ Successfully pushed $full_image_name"
}

# Create single ECR repository if it doesn't exist
echo ""
echo "📝 Creating ECR repository..."
REPO_NAME=$(echo $ECR_REGISTRY | sed 's|.*/||')
echo "Creating repository: $REPO_NAME"

aws ecr create-repository \
    --repository-name $REPO_NAME \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256 \
    2>/dev/null || echo "Repository $REPO_NAME already exists"

# Build and push all services
echo ""
echo "🏗️ Building and pushing all services to single registry..."
for service in "${SERVICES[@]}"; do
    build_and_push_service $service
done

echo ""
echo "🎉 All images successfully built and pushed to single registry!"
echo ""
echo "📋 Images pushed to registry: $ECR_REGISTRY"
for service in "${SERVICES[@]}"; do
    echo "  - $ECR_REGISTRY:$service-$IMAGE_TAG"
done

echo ""
echo "💡 Next steps:"
echo "1. Update terraform.tfvars with these image URLs:"
for service in "${SERVICES[@]}"; do
    echo "   ${service}_image = \"$ECR_REGISTRY:$service-$IMAGE_TAG\""
done
echo "2. Run: terraform apply"
echo "3. ECS services will now start with your images" 