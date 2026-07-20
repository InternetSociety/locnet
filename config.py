import os
from dotenv import load_dotenv

# Load environment variables from a .env file (if present)
load_dotenv()

# Grist API Configuration
GRIST_SERVER = os.getenv("GRIST_SERVER")  # Default for local dev
GRIST_DOC_ID = os.getenv("GRIST_DOC_ID")
GRIST_API_KEY = os.getenv("GRIST_API_KEY")

# Confluence API Configuration
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID")
CONFLUENCE_QSG_PAGE_ID = os.getenv("CONFLUENCE_QSG_PAGE_ID")
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")

# Map / MapLibre GL JS Configuration
# Base URL of the upstream map tile provider. This is proxied by the /api/tiles
# endpoint so the browser never talks to the provider directly. In the future this
# can be pointed at a self-hosted tile server by changing this single value.
MAP_TILE_BASE_URL = os.getenv("MAP_TILE_BASE_URL", "https://api.maptiler.com")
# Path (relative to MAP_TILE_BASE_URL) of the MapLibre style document to load.
MAP_STYLE_PATH = os.getenv("MAP_STYLE_PATH", "/maps/hybrid-v4/style.json")
# API key used when requesting tiles from the provider (MapTiler).
MAPTILER_API_KEY = os.getenv("MAPTILER_API_KEY")
# Origin/Referer value sent to the tile provider when requesting tiles.
MAP_TILE_REFERER = os.getenv("MAP_TILE_REFERER", "https://locnet.io")
# Public base URL of this application (scheme + host, no trailing slash), used to
# build ABSOLUTE tile-proxy URLs inside proxied style.json / TileJSON documents.
# MapLibre's Web Worker loads vector tiles, glyphs and the sprite and cannot
# resolve root-relative URLs, so absolute URLs are required. When empty, the URL
# is derived from the incoming request (works when not behind a reverse proxy
# that rewrites the host/scheme).
MAP_PUBLIC_BASE_URL = os.getenv("MAP_PUBLIC_BASE_URL", "")
