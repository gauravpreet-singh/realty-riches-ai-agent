from supabase import Client, create_client

from .config import SUPABASE_SECRET_KEY, SUPABASE_URL

# This is backend-only code. Never expose SUPABASE_SECRET_KEY to a browser.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
