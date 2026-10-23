// Requires puppeteer@23.11.1. Uses a temporary browser profile, no device access.
const puppeteer = require('puppeteer');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
(async () => {
  const browser = await puppeteer.launch({headless: true,
    ...(process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH} : {})});
  try {
    const page = await browser.newPage();
    await page.setViewport({width:1800,height:900,deviceScaleFactor:1});
    for (const name of ['architecture','update-flow']) {
      await page.goto(pathToFileURL(path.join(__dirname, `${name}.svg`)).href);
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({path:path.join(__dirname, `${name}.png`)});
    }
  } finally { await browser.close(); }
})().catch(e => {console.error(e);process.exitCode=1;});
