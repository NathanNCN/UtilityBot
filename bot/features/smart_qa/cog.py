from discord.ext import commands
import discord
import random
from typing import List, Tuple, Optional
import logging
import os
import aiohttp

# Chroma could be implemented to support semantic search on large files if needed
#_DISABLE_CHROMA = os.getenv("DISABLE_CHROMA", "").lower() in {"1","true","yes","on"}

logger = logging.getLogger("utilitybot.smart_qa")

def _get_knowledge_document() -> str:
    '''Mock knowledge base. Will be replaced by an actual document in the future.'''
    return (
        "Electrium Mobility is a student design team based at the University of Waterloo. Its goal is to create sustainable and affordable transportation in the form of Personal Electric Vehicles."
        "UtilityBot is a modular Discord bot written in Python using discord.py. "
        "Features are implemented as Cogs and are auto-loaded from bot/features. "
        "The Smart Q&A module answers user questions by consulting relevant notes. "
        "Commands use the '!' prefix (e.g., !qa). Message content intent must be enabled. "
        "Environment variables are provided via a .env file (DISCORD_TOKEN). "
        "Logging is configured through bot/core/logging.py. "
        "To run the bot: activate the venv and execute `python -m bot.main`. "
        "Extensions are discovered and loaded by bot/core/loader.py. "
        "This is a mock knowledge base used only for development without external APIs."
    )

async def _ask_deepseek(question: str, knowledge_document: str) -> Optional[str]:
    """Ask DeepSeek with knowledge context. Returns answer or None on failure."""
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return None

    url = "https://api.deepseek.com/v1/chat/completions"
    payload = {
        "model": "deepseek-chat",
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Answer strictly using the provided knowledge. "
                    "If the answer is not present, say: 'I don't know based on the provided knowledge.'"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Knowledge:\n{knowledge_document}\n\n"
                    f"Question:\n{question}\n\n"
                    "Answer in 1-2 concise sentences."
                ),
            },
        ],
    }

    # Standard header
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    logger.warning("DeepSeek API non-200: %s", resp.status)
                    return None

                # Handles none type at each level
                data = await resp.json()
                choices = (data or {}).get("choices") or []
                if not choices:
                    return None
                content = (((choices[0] or {}).get("message") or {}).get("content") or "").strip()

                return content or None
    except Exception:
        logger.exception("DeepSeek API call failed")
        return None


class SmartQACog(commands.Cog):
    """Smart Q&A feature implementation."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="qa")
    async def qa(self, ctx: commands.Context, *, question: Optional[str] = None):

        if not question or not question.strip():
            await ctx.send("Please ask me a question! For example: `!qa What is Electrium Mobility?`")
            return
            
        # Prefer DeepSeek if available, otherwise returns AI search not available right now. Please try again later.
        answer = await _ask_deepseek(question, _get_knowledge_document())
        if not answer:
            answer = ["AI search not available"]        
        # Send response with normal-sized text in description, compact title label
        embed = discord.Embed(
            title="💡Smart Q&A",
            description=answer,
            color=0x00ff00
        )
        embed.add_field(name="Your Question", value=question, inline=False)
        # No footer (do not include "Asked by ...")
        
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SmartQACog(bot))