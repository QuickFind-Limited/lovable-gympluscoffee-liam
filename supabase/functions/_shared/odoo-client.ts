// Revert to custom implementation but fix the parameter handling
import { createClient } from '../_shared/xmlrpc-client.ts';

export class OdooClient {
  private url: string;
  private db: string;
  private username: string;
  private password: string;
  private uid?: number;

  constructor() {
    // Get Odoo credentials from environment variables (Supabase secrets)
    const url = Deno.env.get('ODOO_URL');
    const db = Deno.env.get('ODOO_DATABASE');
    const username = Deno.env.get('ODOO_USERNAME');
    const password = Deno.env.get('ODOO_PASSWORD');
    
    if (!url || !db || !username || !password) {
      throw new Error('Missing required Odoo environment variables. Please configure ODOO_URL, ODOO_DATABASE, ODOO_USERNAME, and ODOO_PASSWORD in Supabase secrets.');
    }
    
    this.url = url.replace(/\/$/,'');
    this.db = db;
    this.username = username;
    this.password = password;

    console.log('Odoo configuration:', {
      url: this.url,
      db: this.db,
      username: this.username,
      password: '***hidden***',
      source: Deno.env.get('ODOO_URL') ? 'environment' : 'fallback'
    });

    if (!this.url || !this.db || !this.username || !this.password) {
      throw new Error('Missing required Odoo configuration');
    }
  }

  async connect(): Promise<number> {
    if (this.uid) return this.uid;

    try {
      console.log('🔵 Connecting to Odoo using custom XML-RPC client...');
      
      // Use custom XML-RPC client for authentication
      const common = createClient(`${this.url}/xmlrpc/2/common`);
      
      this.uid = await common.methodCall('authenticate', [
        this.db,
        this.username,
        this.password,
        {}
      ]);

      if (!this.uid) {
        throw new Error('Authentication failed');
      }

      console.log('✅ Connected to Odoo, UID:', this.uid);
      return this.uid;
    } catch (error) {
      console.error('Odoo connection error:', error);
      throw new Error(`Failed to connect to Odoo: ${error.message}`);
    }
  }

  async execute(model: string, method: string, args: any[]): Promise<any> {
    if (!this.uid) {
      await this.connect();
    }

    console.log(`OdooClient.execute: ${model}.${method}`);
    console.log('Args:', JSON.stringify(args, null, 2));

    const object = createClient(`${this.url}/xmlrpc/2/object`);
    const result = await object.methodCall('execute_kw', [
      this.db,
      this.uid,
      this.password,
      model,
      method,
      args
    ]);
    
    console.log('OdooClient.execute result:', result);
    return result;
  }

  async searchRead(
    model: string,
    domain: any[] = [],
    fields: string[] = [],
    offset: number = 0,
    limit: number = 100
  ): Promise<any[]> {
    // Always include fields to avoid memory errors
    // If no fields specified, use a minimal set
    const fieldsToUse = fields.length > 0 ? fields : ['id', 'name'];
    
    console.log(`OdooClient.searchRead: ${model} with domain:`, JSON.stringify(domain));
    console.log(`Fields:`, fieldsToUse, `Offset:`, offset, `Limit:`, limit);
    
    if (!this.uid) {
      await this.connect();
    }

    // Use custom XML-RPC client with the EXACT same structure as working tests
    const object = createClient(`${this.url}/xmlrpc/2/object`);
    
    console.log('🔵 Using custom XML-RPC client with working parameter structure');
    
    // Use the EXACT same structure that works in our Node.js tests
    // execute_kw parameters: [db, uid, password, model, method, args, kwargs]
    const result = await object.methodCall('execute_kw', [
      this.db,
      this.uid,
      this.password,
      model,
      'search_read',
      [domain],  // args: domain wrapped in array (EXACT same as working test)
      {          // kwargs: options as separate parameter (EXACT same as working test)
        fields: fieldsToUse,
        offset: offset,
        limit: limit
      }
    ]);
    
    console.log(`✅ OdooClient.searchRead result:`, result?.length || 0, 'records');
    return result || [];
  }

  async searchCount(model: string, domain: any[] = []): Promise<number> {
    return await this.execute(model, 'search_count', [domain]);
  }

  async create(model: string, values: any): Promise<number> {
    return await this.execute(model, 'create', [values]);
  }

  async write(model: string, ids: number[], values: any): Promise<boolean> {
    return await this.execute(model, 'write', [ids, values]);
  }

  async unlink(model: string, ids: number[]): Promise<boolean> {
    return await this.execute(model, 'unlink', [ids]);
  }
}