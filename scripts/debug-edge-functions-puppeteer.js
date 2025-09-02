import puppeteer from 'puppeteer';
import { SUPABASE_URL, SERVICE_ROLE_KEY } from './config.js';

async function debugWithPuppeteer() {
  console.log('🔍 Starting Puppeteer debug session...\n');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();
    
    // Enable request interception to add headers
    await page.setRequestInterception(true);
    
    // Intercept requests to add auth headers
    page.on('request', (request) => {
      const headers = {
        ...request.headers(),
        'Authorization': `Bearer ${SERVICE_ROLE_KEY}`,
        'apikey': SERVICE_ROLE_KEY,
        'Content-Type': 'application/json'
      };
      request.continue({ headers });
    });

    // Listen to console messages
    page.on('console', msg => {
      console.log('Browser Console:', msg.type(), msg.text());
    });

    // Listen to page errors
    page.on('pageerror', error => {
      console.log('Page Error:', error.message);
    });

    // Listen to response
    page.on('response', response => {
      console.log(`Response: ${response.status()} ${response.url()}`);
    });

    console.log('📊 Testing debug-odoo-connection endpoint...\n');
    
    // Test the debug endpoint
    const debugUrl = `${SUPABASE_URL}/functions/v1/debug-odoo-connection`;
    
    // Navigate to the URL and get the response
    const response = await page.goto(debugUrl, {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

    const responseText = await response.text();
    
    try {
      const data = JSON.parse(responseText);
      console.log('Debug Response:', JSON.stringify(data, null, 2));
      
      // Analyze the results
      if (data.steps) {
        console.log('\n📋 Analysis of steps:');
        data.steps.forEach(step => {
          const icon = step.status === 'success' ? '✅' : '❌';
          console.log(`${icon} ${step.step}: ${step.status}`);
          if (step.error) {
            console.log(`   Error: ${step.error}`);
          }
          if (step.result) {
            console.log(`   Result:`, step.result);
          }
        });
      }
    } catch (e) {
      console.log('Raw Response:', responseText);
    }

    // Test odoo-products endpoint
    console.log('\n\n📦 Testing odoo-products endpoint...\n');
    
    const productsUrl = `${SUPABASE_URL}/functions/v1/odoo-products?limit=1`;
    const productsResponse = await page.goto(productsUrl, {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

    const productsText = await productsResponse.text();
    console.log('Products Response:', productsText);

    // Check network activity
    console.log('\n📡 Checking network requests...\n');
    
    // Clear previous requests
    const requests = [];
    page.on('request', request => {
      if (request.url().includes('xmlrpc')) {
        requests.push({
          url: request.url(),
          method: request.method(),
          headers: request.headers(),
          postData: request.postData()
        });
      }
    });

    // Make another request to capture network activity
    await page.goto(`${SUPABASE_URL}/functions/v1/debug-odoo`, {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

    console.log('XML-RPC Requests captured:', requests);

  } catch (error) {
    console.error('Error during Puppeteer testing:', error);
  } finally {
    await browser.close();
  }
}

// Run the debug session
debugWithPuppeteer().catch(console.error);