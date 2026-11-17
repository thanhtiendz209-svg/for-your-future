// Rebuild after changing utility classes in public HTML, JavaScript or JSON.
// Uses the existing web dependencies; no browser compiler or new dependency.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const web = path.join(root, 'apps/web');
const postcss = require(path.join(web, 'node_modules/postcss'));
const tailwind = require(path.join(web, 'node_modules/tailwindcss'));
const config = require(path.join(web, 'tailwind.static.cjs'));

async function build() {
  const result = await postcss([tailwind({
    ...config,
    content: [
      path.join(web, 'public/index.html'),
      path.join(web, 'public/app.js'),
      path.join(web, 'public/data/*.json'),
    ],
  })]).process('@tailwind base;\n@tailwind components;\n@tailwind utilities;', {from: undefined});
  for (const folder of ['public', 'dist']) {
    fs.writeFileSync(path.join(web, folder, 'utilities.css'), result.css);
  }
  console.log(`Built utilities.css: ${Buffer.byteLength(result.css)} bytes (public/dist).`);
}
build().catch(error => { console.error(error.message); process.exitCode = 1; });
