# 🚀 Stress Testing - Sistema de Alertas

Esta documentación describe los scripts de stress testing disponibles para probar el sistema de alertas por Kafka cuando el servicio de órdenes falla o se sobrecarga.

## 📊 Scripts Disponibles

### 1. 🧪 `test-alerts.sh` - Test Básico
**Propósito:** Generar algunos errores específicos para probar el sistema de alertas.
```bash
./scripts/test-alerts.sh
```

**Qué hace:**
- Envía 3 tipos diferentes de requests problemáticos
- Valida que las alertas aparezcan en el dashboard
- Muestra las alertas generadas

### 2. ⚡ `quick-stress-test.sh` - Test Rápido
**Propósito:** Stress test ligero y rápido para validación continua.
```bash
# Uso básico (50 requests, 10 concurrentes)
./scripts/quick-stress-test.sh

# Personalizado
./scripts/quick-stress-test.sh [requests] [concurrent]

# Ejemplos:
./scripts/quick-stress-test.sh 100 20  # 100 requests, 20 concurrentes
./scripts/quick-stress-test.sh 30 5    # Test ligero
```

**Características:**
- ✅ Test rápido (< 1 minuto)
- ✅ Genera datos inválidos tipo-incompatibles 
- ✅ Cuenta alertas antes/después
- ✅ Perfecto para CI/CD

### 3. 🔥 `stress-test-orders.sh` - Test Completo
**Propósito:** Stress test comprehensivo con múltiples vectores de ataque.
```bash
./scripts/stress-test-orders.sh
```

**Características:**
- **200 requests** por defecto con **20 concurrentes**
- **5 tipos de ataques diferentes:**
  1. **Datos inválidos** (type errors, causa 500s)
  2. **Memory bombs** (strings enormes)
  3. **Valores negativos** (edge cases)
  4. **SQL injection attempts** (security test)
  5. **Órdenes válidas masivas** (volume test)

**Métricas que reporta:**
- Requests exitosos/fallidos por tipo
- Error rates y performance
- Alertas generadas
- Duración y RPS

### 4. 💀 `extreme-stress-test.sh` - Test Extremo 
**Propósito:** Intentar tumbar completamente el servicio para probar robustez.
```bash
./scripts/extreme-stress-test.sh [requests] [concurrent]

# Ejemplo extremo:
./scripts/extreme-stress-test.sh 2000 100
```

**⚠️ ADVERTENCIAS:**
- **MUY AGRESIVO** - puede tumbar el servicio temporalmente
- Requiere confirmación del usuario
- **1000+ requests** con **50+ concurrentes** por defecto
- Usa técnicas de ataque avanzadas

**Tipos de ataques:**
- 💣 **Memory bombs** (strings de 50K+ chars)
- 🔀 **Type confusion** (arrays como strings, etc)
- 🌪️ **Unicode bombs** (emojis y caracteres especiales)
- ♾️ **Numeric overflow** (valores extremos)

## 📊 Interpretación de Resultados

### Alertas Esperadas
- **0-5 alertas:** Sistema muy robusto
- **5-20 alertas:** Normal, sistema funcionando
- **20-50 alertas:** Alta carga, alertas funcionando bien
- **50+ alertas:** Sistema bajo estrés extremo

### Códigos de Estado HTTP
- **500 Internal Server Error:** ✅ Perfecto - genera alertas por Kafka
- **400 Bad Request:** ⚠️ Validación funcionando, no genera alerta Kafka
- **201 Created:** ❌ Request exitoso, no deseado en stress test
- **000/timeout:** 💀 Servicio caído temporalmente

### Monitoreo en Tiempo Real

**Dashboard:** http://localhost/monitor/dashboard
- Se actualiza **cada 1 segundo**
- Sección **"Alertas Recientes"** muestra errores en tiempo real
- Gráficas muestran impacto en performance

**API Directa:** http://localhost/monitor/api/monitor/dashboard
```bash
# Ver alertas actuales
curl -s http://localhost/monitor/api/monitor/dashboard | jq '.total_alerts, .recent_alerts[-3:]'
```

## 🛠️ Configuración de Tests

### Variables Personalizables

**Quick Test:**
```bash
REQUESTS=30     # Número total de requests
CONCURRENT=5    # Requests concurrentes máximos
```

**Stress Test:**
```bash
TOTAL_REQUESTS=200      # Total de requests a enviar
CONCURRENT_REQUESTS=20  # Máximos concurrentes
ERROR_TYPES=5          # Tipos de ataques diferentes
```

**Extreme Test:**
```bash
REQUESTS=1000   # Requests por batch
CONCURRENT=50   # Batches concurrentes
# Genera 1000 * 50 = 50,000 requests!
```

## 🎯 Casos de Uso

### Durante Desarrollo
```bash
# Validación rápida después de cambios
./scripts/quick-stress-test.sh 20 3
```

### Testing de Integración  
```bash
# Test completo antes de deploy
./scripts/stress-test-orders.sh
```

### Pruebas de Robustez
```bash
# Test extremo para validar límites
./scripts/extreme-stress-test.sh 500 25
```

### Debugging de Alertas
```bash
# Test específico para debuggear alerts
./scripts/test-alerts.sh
```

## 📈 Ejemplos de Salida

### ✅ Test Exitoso
```
📊 Final Results:
Total Requests: 200
Successful (201): 0
Server Errors (500): 180  ← ¡Perfecto!
Client Errors (400): 20

🚨 Alert System Results:
NEW ALERTS GENERATED: 45  ← ¡Sistema funcionando!

✅ SUCCESS: Alert system is working!
```

### 🔥 Extreme Test Exitoso
```
💀 EXTREME STRESS TEST RESULTS
Duration: 15 seconds
NEW ALERTS GENERATED: 156

🔥 MISSION ACCOMPLISHED: Service was severely stressed!
   Generated 156 alerts - Alert system is ROBUST!

🔍 Service health check:
✅ Service is responding (HTTP 405)
```

## 🚨 Troubleshooting

### ❌ No se generan alertas
1. Verificar que el servicio monitor esté funcionando
2. Comprobar conectividad Kafka
3. Revisar logs del servicio orders

### ⚠️ Servicio no responde después del test
```bash
# Reiniciar servicios
docker-compose restart orders-service monitor-service

# Verificar estado
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### 📊 Dashboard no actualiza
- Verificar URL: http://localhost/monitor/dashboard
- Comprobar logs del browser (F12)
- El dashboard se actualiza cada 1 segundo automáticamente

## 🎯 Métricas de Éxito

**Sistema de Alertas FUNCIONANDO si:**
- ✅ Errores 500 generan alertas por Kafka
- ✅ Alertas aparecen en dashboard < 5 segundos  
- ✅ Dashboard se actualiza en tiempo real
- ✅ Servicio se recupera después del test

**Sistema ROBUSTO si:**
- ✅ Survives 200+ requests concurrentes
- ✅ Genera alertas apropiadas sin colapsar
- ✅ Se recupera rápidamente post-test
- ✅ Monitor sigue funcionando durante estrés

¡El sistema de alertas está diseñado para funcionar **especialmente** bajo estrés! 🚀
