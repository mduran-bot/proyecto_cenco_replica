#!/bin/bash
# Script para probar los módulos integrados de Max
# Fase 1.1: Validación de integración

echo "========================================="
echo "Testing Módulos Integrados de Max"
echo "Fase 1.1: JSONFlattener, DataCleaner, DuplicateDetector, ConflictResolver"
echo "========================================="
echo ""

# Cambiar al directorio glue
cd "$(dirname "$0")/.." || exit 1

echo "📦 Instalando dependencias..."
pip install -q pytest pyspark

echo ""
echo "🧪 Ejecutando tests unitarios..."
echo ""

# Test 1: JSONFlattener
echo "1️⃣  Testing JSONFlattener..."
pytest tests/unit/test_json_flattener.py -v --tb=short
if [ $? -eq 0 ]; then
    echo "✅ JSONFlattener: PASSED"
else
    echo "❌ JSONFlattener: FAILED"
    exit 1
fi

echo ""

# Test 2: DataCleaner
echo "2️⃣  Testing DataCleaner..."
pytest tests/unit/test_data_cleaner.py -v --tb=short
if [ $? -eq 0 ]; then
    echo "✅ DataCleaner: PASSED"
else
    echo "❌ DataCleaner: FAILED"
    exit 1
fi

echo ""

# Test 3: DuplicateDetector
echo "3️⃣  Testing DuplicateDetector..."
pytest tests/unit/test_duplicate_detector.py -v --tb=short
if [ $? -eq 0 ]; then
    echo "✅ DuplicateDetector: PASSED"
else
    echo "❌ DuplicateDetector: FAILED"
    exit 1
fi

echo ""

# Test 4: ConflictResolver
echo "4️⃣  Testing ConflictResolver..."
pytest tests/unit/test_conflict_resolver.py -v --tb=short
if [ $? -eq 0 ]; then
    echo "✅ ConflictResolver: PASSED"
else
    echo "❌ ConflictResolver: FAILED"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ TODOS LOS TESTS PASARON"
echo "========================================="
echo ""
echo "Módulos integrados exitosamente:"
echo "  - JSONFlattener"
echo "  - DataCleaner"
echo "  - DuplicateDetector"
echo "  - ConflictResolver"
echo ""
echo "Próximo paso: Fase 1.2 - Fusionar módulos duplicados"
echo ""
