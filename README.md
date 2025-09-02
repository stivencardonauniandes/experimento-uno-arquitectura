# 🏗️ Arquitectura de Microservicios - Sistema de Inventario y Órdenes

Una arquitectura completa de microservicios que implementa un sistema de gestión de inventario y órdenes con comunicación asíncrona mediante colas de mensajes.

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Arquitectura](#-arquitectura)
- [Servicios](#-servicios)
- [Tecnologías](#-tecnologías)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Uso](#-uso)
- [API Endpoints](#-api-endpoints)
- [Monitoreo](#-monitoreo)
- [Desarrollo](#-desarrollo)
- [Troubleshooting](#-troubleshooting)

## 🎯 Descripción General

Este proyecto implementa una arquitectura de microservicios con las siguientes características:

- **Servicio de Inventario**: Gestiona productos y stock
- **Servicio de Órdenes**: Procesa órdenes de compra y venta
- **Servicio de Monitor**: Monitorea la salud del sistema
- **Comunicación Asíncrona**: Mediante Apache Kafka
- **APIs REST**: Para interacción externa
- **Base de Datos**: PostgreSQL para persistencia
- **Containerización**: Docker y Docker Compose

## 🏛️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Monitor       │    │   Kafka UI      │
│   (Gateway)     │    │   Service       │    │   (Optional)    │
│   Port: 80      │    │   Port: 5003    │    │   Port: 8080    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ├─────────────────────────────────────────────────────────┐
         │                       │                       │         │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│   Inventory     │    │   Orders        │    │   Apache        │ │
│   Service       │    │   Service       │    │   Kafka         │ │
│   Port: 5001    │    │   Port: 5002    │    │   Port: 9092    │ │
└─────────────────┘    └─────────────────┘    └─────────────────┘ │
         │                       │                       │         │
         └─────────────────────────────────────────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   Port: 5432    │
                    └─────────────────┘
```

### Flujo de Comunicación

1. **Creación de Orden**: El servicio de órdenes publica un evento `order-created`
2. **Procesamiento de Stock**: El servicio de inventario consume el evento y actualiza el stock
3. **Confirmación**: El inventario publica `order-processed` con el resultado
4. **Monitoreo**: El servicio monitor observa todos los eventos y estados

## 🚀 Servicios

### 📦 Servicio de Inventario
- **Puerto**: 5001
- **Responsabilidades**:
  - Gestión de productos
  - Control de stock
  - Movimientos de inventario
  - Alertas de stock bajo

### 🛒 Servicio de Órdenes
- **Puerto**: 5002
- **Responsabilidades**:
  - Creación de órdenes de compra/venta
  - Gestión de estados de órdenes
  - Comunicación con inventario
  - Estadísticas de órdenes

### 📊 Servicio de Monitor
- **Puerto**: 5003
- **Responsabilidades**:
  - Health checks de servicios
  - Monitoreo de Kafka
  - Alertas del sistema
  - Dashboard de métricas

## 🛠️ Tecnologías

- **Backend**: Python 3.11, Flask
- **Base de Datos**: PostgreSQL 15
- **Message Broker**: Apache Kafka
- **Containerización**: Docker, Docker Compose
- **Load Balancer**: Nginx
- **Monitoreo**: Custom monitoring service

## 📥 Instalación y Configuración

### Prerrequisitos

- Docker Desktop instalado
- Docker Compose
- Git
- Puertos libres: 80, 5001, 5002, 5003, 5432, 8080, 9092

### Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <repository-url>
   cd experimento-uno
   ```

2. **Iniciar el sistema completo**:
   ```bash
   ./scripts/start-system.sh
   ```

   Este script:
   - Inicia todos los servicios con Docker Compose
   - Configura los topics de Kafka
   - Verifica la salud de los servicios

3. **Poblar con datos de ejemplo** (opcional):
   ```bash
   ./scripts/seed-data.sh
   ```

### Configuración Manual

Si prefieres ejecutar paso a paso:

```bash
# 1. Iniciar servicios
docker-compose up -d

# 2. Esperar que Kafka esté listo
sleep 45

# 3. Configurar topics de Kafka
./scripts/setup-kafka-topics.sh

# 4. Verificar servicios
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

## 🎮 Uso

### Acceso a la Aplicación

- **Dashboard Principal**: http://localhost
- **Kafka UI**: http://localhost:8080

### Endpoints Principales

#### Inventario
```bash
# Listar productos
curl http://localhost/api/inventory/products

# Crear producto
curl -X POST http://localhost/api/inventory/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Producto Test",
    "description": "Descripción del producto",
    "price": 99.99,
    "stock_quantity": 50,
    "min_stock_level": 10
  }'

# Actualizar stock
curl -X POST http://localhost/api/inventory/products/1/stock \
  -H "Content-Type: application/json" \
  -d '{
    "quantity_change": -5,
    "movement_type": "sale",
    "reference_id": "ORDER-123",
    "notes": "Venta de producto"
  }'
```

#### Órdenes
```bash
# Listar órdenes
curl http://localhost/api/orders/orders

# Crear orden de venta
curl -X POST http://localhost/api/orders/orders \
  -H "Content-Type: application/json" \
  -d '{
    "order_type": "sell",
    "customer_name": "Cliente Test",
    "customer_email": "cliente@test.com",
    "items": [
      {
        "product_id": 1,
        "product_name": "Producto Test",
        "quantity": 2,
        "unit_price": 99.99
      }
    ]
  }'

# Ver estadísticas
curl http://localhost/api/orders/orders/stats
```

#### Monitoreo
```bash
# Dashboard completo
curl http://localhost/api/monitor/dashboard

# Estado de servicios
curl http://localhost/api/monitor/services/health

# Alertas del sistema
curl http://localhost/api/monitor/alerts
```

## 📚 API Endpoints

### Servicio de Inventario (`/api/inventory/`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/products` | Listar todos los productos |
| POST | `/products` | Crear nuevo producto |
| GET | `/products/{id}` | Obtener producto específico |
| PUT | `/products/{id}` | Actualizar producto |
| POST | `/products/{id}/stock` | Actualizar stock |
| GET | `/products/{id}/movements` | Historial de movimientos |
| GET | `/products/low-stock` | Productos con stock bajo |
| GET | `/health` | Health check |

### Servicio de Órdenes (`/api/orders/`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/orders` | Listar órdenes (con filtros) |
| POST | `/orders` | Crear nueva orden |
| GET | `/orders/{id}` | Obtener orden específica |
| PUT | `/orders/{id}/status` | Actualizar estado de orden |
| DELETE | `/orders/{id}` | Cancelar orden |
| GET | `/orders/stats` | Estadísticas de órdenes |
| GET | `/health` | Health check |

### Servicio de Monitor (`/api/monitor/`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/dashboard` | Dashboard completo |
| GET | `/services/health` | Estado de todos los servicios |
| GET | `/services/{service}/health` | Estado de servicio específico |
| GET | `/services/{service}/history` | Historial de salud |
| GET | `/kafka/stats` | Estadísticas de Kafka |
| GET | `/alerts` | Alertas del sistema |
| GET | `/health` | Health check |

## 📊 Monitoreo

### Métricas Disponibles

1. **Salud de Servicios**:
   - Estado actual (healthy/unhealthy/down)
   - Tiempo de respuesta
   - Historial de disponibilidad

2. **Estadísticas de Kafka**:
   - Mensajes por topic
   - Throughput de mensajes
   - Errores de comunicación

3. **Alertas del Sistema**:
   - Stock bajo
   - Servicios caídos
   - Errores de procesamiento
   - Órdenes fallidas

### Dashboard

Accede al dashboard principal en http://localhost para ver:
- Estado general del sistema
- Métricas en tiempo real
- Enlaces rápidos a APIs
- Herramientas de monitoreo

## 🔧 Desarrollo

### Estructura del Proyecto

```
experimento-uno/
├── services/
│   ├── inventory/          # Servicio de inventario
│   ├── orders/             # Servicio de órdenes
│   └── monitor/            # Servicio de monitoreo
├── shared/                 # Código compartido
│   ├── database.py         # Configuración de BD
│   ├── kafka_client.py     # Cliente de Kafka
│   ├── models.py           # Modelos de datos
│   └── utils.py            # Utilidades
├── docker/                 # Configuración Docker
├── scripts/                # Scripts de automatización
└── logs/                   # Logs de aplicación
```

### Ejecutar en Modo Desarrollo

```bash
# Instalar dependencias
pip install -r requirements.txt

# Variables de entorno
export POSTGRES_HOST=localhost
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Ejecutar servicio individual
cd services/inventory
python app.py
```

### Agregar Nuevas Funcionalidades

1. **Nuevo Endpoint**: Agregar en el archivo `app.py` del servicio correspondiente
2. **Nuevo Modelo**: Definir en `shared/models.py`
3. **Nueva Comunicación Kafka**: Agregar topic en `shared/kafka_client.py`
4. **Nuevo Monitoreo**: Extender `services/monitor/`

## 🚨 Troubleshooting

### Problemas Comunes

#### Servicios no inician
```bash
# Verificar logs
docker-compose logs inventory-service
docker-compose logs orders-service
docker-compose logs monitor-service

# Reiniciar servicio específico
docker-compose restart inventory-service
```

#### Kafka no funciona
```bash
# Verificar Kafka
docker-compose logs kafka

# Recrear topics
./scripts/setup-kafka-topics.sh

# Verificar topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

#### Base de datos no conecta
```bash
# Verificar PostgreSQL
docker-compose logs postgres

# Conectar manualmente
docker exec -it postgres psql -U postgres
```

#### Puertos ocupados
```bash
# Verificar puertos en uso
lsof -i :5001
lsof -i :5002
lsof -i :5003

# Cambiar puertos en docker-compose.yml si es necesario
```

### Logs y Debugging

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Logs de servicio específico
docker-compose logs -f inventory-service

# Logs de aplicación (dentro del contenedor)
docker exec inventory-service tail -f /app/logs/inventory-service.log
```

### Limpiar el Sistema

```bash
# Parar servicios
./scripts/stop-system.sh

# Limpiar volúmenes (CUIDADO: borra todos los datos)
docker-compose down -v

# Limpiar imágenes
docker-compose down --rmi all

# Limpiar todo Docker (CUIDADO)
docker system prune -a
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

Para soporte o preguntas:
- Crear issue en GitHub
- Revisar logs del sistema
- Consultar documentación de APIs

---

**¡Disfruta construyendo con microservicios! 🚀**
