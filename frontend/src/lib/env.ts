export type AppEnv = {
  apiBaseUrl: string
  supabaseUrl: string
  supabaseAnonKey: string
}

function requireEnv(name: keyof ImportMetaEnv): string {
  const value = import.meta.env[name]?.trim()
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`)
  }
  return value
}

export function getEnv(): AppEnv {
  return {
    apiBaseUrl: requireEnv("VITE_API_BASE_URL").replace(/\/$/, ""),
    supabaseUrl: requireEnv("VITE_SUPABASE_URL"),
    supabaseAnonKey: requireEnv("VITE_SUPABASE_ANON_KEY"),
  }
}
