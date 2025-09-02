#!/bin/bash

echo "🌱 Seeding sample data..."

BASE_URL="http://localhost"

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Create sample products
echo "📦 Creating sample products..."

curl -X POST "$BASE_URL/api/inventory/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop Gaming",
    "description": "Laptop para gaming de alta gama",
    "price": 1500.00,
    "stock_quantity": 25,
    "min_stock_level": 5
  }'

curl -X POST "$BASE_URL/api/inventory/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mouse Inalámbrico",
    "description": "Mouse ergonómico inalámbrico",
    "price": 45.99,
    "stock_quantity": 100,
    "min_stock_level": 20
  }'

curl -X POST "$BASE_URL/api/inventory/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Teclado Mecánico",
    "description": "Teclado mecánico RGB",
    "price": 89.99,
    "stock_quantity": 50,
    "min_stock_level": 10
  }'

curl -X POST "$BASE_URL/api/inventory/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monitor 4K",
    "description": "Monitor 4K 27 pulgadas",
    "price": 350.00,
    "stock_quantity": 15,
    "min_stock_level": 3
  }'

curl -X POST "$BASE_URL/api/inventory/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Auriculares Gaming",
    "description": "Auriculares gaming con micrófono",
    "price": 79.99,
    "stock_quantity": 30,
    "min_stock_level": 8
  }'

echo ""
echo "🛒 Creating sample orders..."

# Create sample sell order
curl -X POST "$BASE_URL/api/orders/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "order_type": "sell",
    "customer_name": "Juan Pérez",
    "customer_email": "juan.perez@email.com",
    "items": [
      {
        "product_id": 1,
        "product_name": "Laptop Gaming",
        "quantity": 2,
        "unit_price": 1500.00
      },
      {
        "product_id": 2,
        "product_name": "Mouse Inalámbrico",
        "quantity": 2,
        "unit_price": 45.99
      }
    ]
  }'

# Create sample buy order
curl -X POST "$BASE_URL/api/orders/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "order_type": "buy",
    "customer_name": "Proveedor Tech",
    "customer_email": "proveedor@techcorp.com",
    "items": [
      {
        "product_id": 3,
        "product_name": "Teclado Mecánico",
        "quantity": 20,
        "unit_price": 65.00
      },
      {
        "product_id": 4,
        "product_name": "Monitor 4K",
        "quantity": 10,
        "unit_price": 280.00
      }
    ]
  }'

echo ""
echo "✅ Sample data created successfully!"
echo ""
echo "📊 You can now check:"
echo "  - Products: $BASE_URL/api/inventory/products"
echo "  - Orders: $BASE_URL/api/orders/orders"
echo "  - Dashboard: $BASE_URL/api/monitor/dashboard"
