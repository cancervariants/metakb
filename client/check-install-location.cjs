const path = require('path');
const process = require('process');

const currentDir = process.cwd();
const projectRoot = path.resolve(__dirname, '..');

if (currentDir !== projectRoot) {
  process.stdout.write('\n');
  console.log('🚫 Please run `pnpm install` from the project root, not from client/. Exiting...\n');
  process.exit(1);
}
