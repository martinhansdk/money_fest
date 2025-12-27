#!/bin/bash
# Test login flow

BASE_URL="http://localhost:1111"

echo "Testing Money Fest Login..."
echo "=========================="
echo ""

# Test 1: Login
echo "1. Testing login endpoint..."
RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"martin","password":"test1234"}' \
  -c /tmp/cookies.txt \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ Login successful"
  echo "  Response: $BODY"
else
  echo "✗ Login failed with HTTP $HTTP_CODE"
  echo "  Response: $BODY"
  exit 1
fi

echo ""

# Test 2: Get current user
echo "2. Testing /auth/me endpoint..."
RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
  -b /tmp/cookies.txt \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ Auth verification successful"
  echo "  User: $BODY"
else
  echo "✗ Auth verification failed with HTTP $HTTP_CODE"
  echo "  Response: $BODY"
  exit 1
fi

echo ""

# Test 3: List batches
echo "3. Testing /batches endpoint..."
RESPONSE=$(curl -s -X GET "$BASE_URL/batches" \
  -b /tmp/cookies.txt \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ Batches endpoint successful"
  echo "  Response: $BODY"
else
  echo "✗ Batches endpoint failed with HTTP $HTTP_CODE"
  echo "  Response: $BODY"
  exit 1
fi

echo ""
echo "=========================="
echo "All tests passed! ✓"
