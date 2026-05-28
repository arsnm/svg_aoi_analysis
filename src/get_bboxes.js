const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function extractBBoxes(svgRelativePath) {
    const absolutePath = path.resolve(svgRelativePath);
    
    if (!fs.existsSync(absolutePath)) {
        console.error(`Error: File not found at ${absolutePath}`);
        return;
    }

    console.log(`Launching headless browser to render: ${path.basename(absolutePath)}...`);
    
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();

    // 1. Load the SVG file directly
    await page.goto(`file://${absolutePath}`);

    // 2. Execute script in the browser context to get built-in BBoxes
    const results = await page.evaluate(() => {
        // Select all typical visual elements and groups
        const elements = document.querySelectorAll('path, rect, circle, ellipse, line, polyline, polygon, text, g');
        
        return Array.from(elements).map(el => {
            // Native browser method for precise geometric bounding boxes
            const bbox = el.getBBox();
            
            return {
                id: el.id || "",
                tag: el.tagName,
                x: parseFloat(bbox.x.toFixed(2)),
                y: parseFloat(bbox.y.toFixed(2)),
                width: parseFloat(bbox.width.toFixed(2)),
                height: parseFloat(bbox.height.toFixed(2)),
                text: el.tagName === 'text' ? el.textContent.trim() : ""
            };
        });
    });

    await browser.close();

    // 3. Save to a JSON file
    const outputName = `geometry_${path.basename(absolutePath, '.svg')}.json`;
    fs.writeFileSync(outputName, JSON.stringify(results, null, 2));

    console.log(`\nSUCCESS! Extracted ${results.length} perfect bounding boxes.`);
    console.log(`Saved to: ${outputName}`);
    console.log(`\nNOTE: These coordinates include perfect font-rendering widths from Chrome.`);
}

// Get the SVG path from command line arguments
const targetSvg = process.argv[2];

if (!targetSvg) {
    console.log("Usage: node get_bboxes.js <path_to_svg>");
} else {
    extractBBoxes(targetSvg);
}
