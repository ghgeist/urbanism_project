#!/bin/bash
# Quick validation script - runs all checks before committing
# Usage: ./scripts/quick_check.sh

set -e  # Exit on error

echo "🔍 Running quick validation checks..."
echo ""

# Backend checks
echo "📦 Backend: Checking Python lint..."
python -m ruff check --no-cache api services scripts tests || {
    echo "❌ Backend lint failed"
    exit 1
}

echo "✅ Backend lint passed"
echo ""

# Frontend checks
echo "📦 Frontend: Checking TypeScript types..."
cd frontend
npm run typecheck || {
    echo "❌ Frontend type check failed"
    exit 1
}

echo "✅ Frontend type check passed"
echo ""

echo "📦 Frontend: Checking ESLint..."
npm run lint || {
    echo "❌ Frontend lint failed"
    exit 1
}

echo "✅ Frontend lint passed"
echo ""

echo "✨ All checks passed! Ready to commit."