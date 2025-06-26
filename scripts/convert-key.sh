#!/bin/bash

# Convert ECDSA private key to PKCS#8 format for AWS ACM
cd voux-platform.shop

echo "Converting ECDSA private key to PKCS#8 format..."

# Convert to PKCS#8
openssl pkcs8 -topk8 -nocrypt -in voux-platform.shop.key -out voux-platform.shop-pkcs8.key

echo "Verifying converted key..."
openssl pkey -in voux-platform.shop-pkcs8.key -text -noout | head -3

echo "Key converted successfully!"
echo "Now use voux-platform.shop-pkcs8.key for ACM import" 