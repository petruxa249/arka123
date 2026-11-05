#!/bin/sh
# Сборка 3D-режима: three@0.170.0 + esbuild, результат ../arka3d.js (корень сайта) (один файл, без CDN).
# Один раз: npm install (в этой папке), затем npm run build
cd "$(dirname "$0")"
npx esbuild arka3d.js --bundle --minify --format=iife --target=es2020 --legal-comments=none --outfile=../arka3d.js
