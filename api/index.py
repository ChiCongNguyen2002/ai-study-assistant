"""Vercel serverless function entry point."""
from src.main import app

# Export for Vercel
handler = app
