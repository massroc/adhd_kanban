#!/usr/bin/env node
/**
 * Build Configuration Script
 * Generates config.js from template with environment variables
 *
 * Usage:
 *   node scripts/build-config.js              # defaults to development
 *   node scripts/build-config.js development  # localhost
 *   node scripts/build-config.js production   # Railway production
 *   API_BASE=https://custom.api.com node scripts/build-config.js  # custom
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcDir = path.join(__dirname, '..', 'src', 'js');

// Default configurations
const DEFAULTS = {
    development: {
        API_BASE: 'http://localhost:8000/api/v1',
    },
    production: {
        API_BASE: 'https://adhdkanban-production.up.railway.app/api/v1',
    },
};

// Get environment from args or NODE_ENV
const env = process.argv[2] || process.env.NODE_ENV || 'development';
const customApiBase = process.env.API_BASE;

// Determine config values
const config = { ...DEFAULTS[env] } || { ...DEFAULTS.development };
if (customApiBase) {
    config.API_BASE = customApiBase;
}

console.log(`Building config for environment: ${env}`);
console.log(`API_BASE: ${config.API_BASE}`);

// Read template
const templatePath = path.join(srcDir, 'config.template.js');
let template = fs.readFileSync(templatePath, 'utf8');

// Replace placeholders
template = template.replace('%%API_BASE%%', config.API_BASE);

// Write config
const outputPath = path.join(srcDir, 'config.js');
fs.writeFileSync(outputPath, template);

console.log(`Config written to ${outputPath}`);
