import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 
  process.env.NEXT_PUBLIC_SUPABASE_URL || 
  process.env.EXPO_PUBLIC_SUPABASE_URL ||
  process.env.SUPABASE_URL || 
  '';

const supabaseAnonKey = 
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 
  process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY ||
  process.env.SUPABASE_ANON_KEY || 
  process.env.SUPABASE_PUBLISHABLE_KEY ||
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
  '';

const supabaseServiceKey = 
  process.env.SUPABASE_SERVICE_ROLE_KEY || 
  process.env.SUPABASE_SECRET_KEY || 
  process.env.SERVICE_ROLE_KEY || 
  process.env.SUPABASE_SERVICE_KEY ||
  '';

export const JWT_SECRET = 
  process.env.JWT_SECRET || 
  process.env.SUPABASE_JWT_SECRET || 
  'anjaneya_secret_key';

if (!supabaseUrl || !supabaseAnonKey) {
  if (typeof window !== 'undefined') {
    console.error('Supabase Client Error: Missing credentials in browser. Ensure variables are set in Vercel.');
  } else {
    console.error('Supabase Server Error: Missing URL or Anon Key. URL:', !!supabaseUrl, 'Key:', !!supabaseAnonKey);
  }
}

let supabaseClient = null;
let supabaseAdminClient = null;

try {
  if (supabaseUrl && supabaseAnonKey) {
    supabaseClient = createClient(supabaseUrl, supabaseAnonKey);
  }
  
  if (supabaseUrl && supabaseServiceKey) {
    supabaseAdminClient = createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    });
  } else if (supabaseClient) {
    supabaseAdminClient = supabaseClient;
  }
} catch (e) {
  console.error("Supabase Init Error:", e);
}

export const supabase = supabaseClient;
export const supabaseAdmin = supabaseAdminClient;
