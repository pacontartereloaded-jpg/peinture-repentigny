const fs = require('fs');
const path = require('path');

const root = __dirname;
const out = path.join(root, 'dist');
const ignored = new Set(['.git', '.vercel', 'dist', 'node_modules', '__pycache__']);

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (ignored.has(entry.name)) continue;
    const sourcePath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(sourcePath, destPath);
    } else {
      fs.copyFileSync(sourcePath, destPath);
    }
  }
}

fs.rmSync(out, { recursive: true, force: true });
copyDir(root, out);
console.log('Static site copied to dist');
