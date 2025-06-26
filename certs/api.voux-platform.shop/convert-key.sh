#!/bin/bash

# Convert ECDSA private key to PKCS#8 format for AWS ACM
echo "Converting ECDSA private key to PKCS#8 format..."

# Convert to PKCS#8
openssl pkcs8 -topk8 -nocrypt -in api.voux-platform.shop.key -out api.voux-platform.shop-pkcs8.key

echo "Verifying converted key..."
openssl pkey -in api.voux-platform.shop-pkcs8.key -text -noout | head -3

echo "Key converted successfully!"
echo "Now use api.voux-platform.shop-pkcs8.key for ACM import" 