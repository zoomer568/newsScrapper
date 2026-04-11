#!/bin/bash
set -e

echo "📦 Extracting BART model..."
unzip -q bart_xsum_model-20260411T023916Z-3-001.zip -d models/
echo "✓ Extraction complete"

echo ""
echo "📁 Extracted files:"
ls -lh models/ | head -15

echo ""
echo "📊 Models directory size:"
du -sh models/

echo ""
echo "🔧 Configuring git LFS..."
git lfs track "models/**"
git add .gitattributes

echo ""
echo "✅ Adding files to git..."
git add models/
git status

echo ""
echo "💾 Committing changes..."
git commit -m "Add BART XSUM model files via git LFS"

echo ""
echo "📤 Pushing to repository..."
git push origin main

echo ""
echo "✨ All done!"
