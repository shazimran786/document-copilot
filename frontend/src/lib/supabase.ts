import { createClient } from "@supabase/supabase-js"

import { getEnv } from "@/lib/env"

const { supabaseUrl, supabaseAnonKey } = getEnv()

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export async function getAccessToken(): Promise<string | null> {
  const { data, error } = await supabase.auth.getSession()
  if (error) {
    throw error
  }
  return data.session?.access_token ?? null
}
