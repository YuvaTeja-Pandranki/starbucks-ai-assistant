#!/bin/bash
set -e

LAYER_NAME="starbucks-ai-dependencies"
S3_BUCKET="${S3_BUCKET:-starbucks-ai-lambda-layers}"
REGION="${AWS_REGION:-us-east-1}"
BUILD_DIR="$(dirname "$0")/../build"

echo "Creating Lambda layer: $LAYER_NAME"

# Create build directory structure
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/python"

# Install all production dependencies into the layer
echo "Installing packages from requirements-lambda.txt..."
pip install \
  -r "$(dirname "$0")/../requirements-lambda.txt" \
  --target "$BUILD_DIR/python" \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.11 \
  --only-binary=:all: \
  --upgrade

echo "Packages installed: $(ls "$BUILD_DIR/python" | wc -l) top-level entries"

# Zip the layer
echo "Zipping layer..."
cd "$BUILD_DIR"
zip -r layer.zip python/ -q
echo "Layer zip size: $(du -sh layer.zip | cut -f1)"

# Upload to S3
echo "Uploading to s3://$S3_BUCKET/layers/$LAYER_NAME.zip ..."
aws s3 cp layer.zip "s3://$S3_BUCKET/layers/$LAYER_NAME.zip" --region "$REGION"

# Publish Lambda layer
echo "Publishing Lambda layer..."
LAYER_ARN=$(aws lambda publish-layer-version \
  --layer-name "$LAYER_NAME" \
  --description "Starbucks AI Assistant Python dependencies" \
  --content "S3Bucket=$S3_BUCKET,S3Key=layers/$LAYER_NAME.zip" \
  --compatible-runtimes python3.11 \
  --compatible-architectures x86_64 \
  --region "$REGION" \
  --query 'LayerVersionArn' \
  --output text)

echo ""
echo "Layer published successfully!"
echo "Layer ARN: $LAYER_ARN"
echo ""
echo "Add this to template.yaml under StarbucksAIFunction > Properties > Layers:"
echo "  - $LAYER_ARN"
