#!/bin/bash
# Script to create a Certificate Signing Request (CSR) for Mac App Store certificates

CSR_FILE="$HOME/Desktop/SithAppStore.certSigningRequest"
PRIVATE_KEY="$HOME/Desktop/SithAppStore.key"

echo "Creating Certificate Signing Request..."
echo ""
echo "This will create:"
echo "  - CSR file: $CSR_FILE"
echo "  - Private key: $PRIVATE_KEY"
echo ""

# Generate private key and CSR
openssl req -new -newkey rsa:2048 -nodes \
  -keyout "$PRIVATE_KEY" \
  -out "$CSR_FILE" \
  -subj "/emailAddress=parker@parkervr.com/CN=Parker Van Roy/C=US"

if [ $? -eq 0 ]; then
    echo "✓ CSR created successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Import the private key into Keychain:"
    echo "   open $PRIVATE_KEY"
    echo ""
    echo "2. Upload the CSR to developer.apple.com:"
    echo "   File location: $CSR_FILE"
    echo ""
    echo "IMPORTANT: Keep the private key file safe until certificates are installed!"
else
    echo "✗ Error creating CSR"
    exit 1
fi
