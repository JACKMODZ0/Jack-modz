#!/usr/bin/env python3
"""
GitHub Codespace Keep-Alive Telegram Bot
Single Script - Everything Included
Author: Lisa (Blackhat Edition)
"""

import asyncio
import json
import logging
import os
import sys
import time
import threading
import requests
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
import warnings
warnings.filterwarnings("ignore")

# ==================== CONFIGURATION ====================
class Config:
    """All configuration in one place."""
    
    # Telegram Bot Token (Get from @BotFather)
    TELEGRAM_BOT_TOKEN = "7840587350:AAGq_IH6ZM2IOVD9Ih1rnzWdOauUCf42we4"  # REPLACE THIS
    
    # GitHub Personal Access Token (Classic)
    # Create at: https://github.com/settings/tokens
    # Permissions needed: codespace, repo, user
    GITHUB_TOKEN = "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"  # REPLACE THIS
    
    # Your GitHub Username
    GITHUB_USERNAME = "jackmodz0"  # REPLACE THIS
    
    # Codespace Details (Auto-detected if empty)
    CODESPACE_NAME = "Jack-modz"  # Leave empty for auto-detect
    
    # Keep-Alive Settings
    CHECK_INTERVAL_MINUTES = 55  # Check every 55 minutes (less than 60)
    ACCESS_DURATION_SECONDS = 60  # Access for 1 minute
    
    # Admin Chat IDs (Will be set via /start command)
    ADMIN_CHAT_IDS = set()
    
    # Files
    DATA_FILE = "codespace_data.json"
    LOG_FILE = "codespace_bot.log"
    
    # API URLs
    GITHUB_API_BASE = "https://api.github.com"
    GITHUB_API_VERSION = "2022-11-28"

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== DATA STORAGE ====================
class DataStore:
    """Simple JSON-based data storage."""
    
    @staticmethod
    def load():
        """Load data from file."""
        try:
            with open(Config.DATA_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"codespaces": {}, "admins": [], "stats": {}}
    
    @staticmethod
    def save(data):
        """Save data to file."""
        with open(Config.DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def get_codespaces():
        """Get all stored codespaces."""
        data = DataStore.load()
        return data.get("codespaces", {})
    
    @staticmethod
    def save_codespace(codespace_id, info):
        """Save codespace information."""
        data = DataStore.load()
        data["codespaces"][codespace_id] = info
        DataStore.save(data)
    
    @staticmethod
    def delete_codespace(codespace_id):
        """Delete codespace from storage."""
        data = DataStore.load()
        if codespace_id in data["codespaces"]:
            del data["codespaces"][codespace_id]
            DataStore.save(data)
    
    @staticmethod
    def add_admin(chat_id):
        """Add admin chat ID."""
        data = DataStore.load()
        admins = data.get("admins", [])
        if chat_id not in admins:
            admins.append(chat_id)
            data["admins"] = admins
            DataStore.save(data)
        Config.ADMIN_CHAT_IDS.add(chat_id)
    
    @staticmethod
    def get_stats():
        """Get statistics."""
        data = DataStore.load()
        return data.get("stats", {
            "total_checks": 0,
            "successful_keeps": 0,
            "failed_attempts": 0,
            "last_check": None,
            "codespace_count": 0
        })
    
    @staticmethod
    def update_stats(field, value=None, increment=1):
        """Update statistics."""
        data = DataStore.load()
        stats = data.get("stats", {})
        
        if value is not None:
            stats[field] = value
        else:
            stats[field] = stats.get(field, 0) + increment
        
        data["stats"] = stats
        DataStore.save(data)

# ==================== GITHUB API MANAGER ====================
class GitHubCodespaceManager:
    """Manage GitHub Codespaces via API."""
    
    def __init__(self):
        self.headers = {
            "Authorization": f"token {Config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": Config.GITHUB_API_VERSION
        }
    
    def get_all_codespaces(self) -> List[Dict]:
        """Get all codespaces for the authenticated user."""
        try:
            url = f"{Config.GITHUB_API_BASE}/user/codespaces"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json().get("codespaces", [])
        except Exception as e:
            logger.error(f"Failed to get codespaces: {e}")
            return []
    
    def get_codespace_by_name(self, name: str) -> Optional[Dict]:
        """Get a specific codespace by name."""
        codespaces = self.get_all_codespaces()
        for cs in codespaces:
            if name.lower() in cs.get("name", "").lower():
                return cs
            if name.lower() in cs.get("display_name", "").lower():
                return cs
        return None
    
    def get_codespace_by_id(self, codespace_id: str) -> Optional[Dict]:
        """Get codespace by ID."""
        try:
            url = f"{Config.GITHUB_API_BASE}/user/codespaces/{codespace_id}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get codespace {codespace_id}: {e}")
            return None
    
    def start_codespace(self, codespace_id: str) -> bool:
        """Start a codespace if it's stopped."""
        try:
            url = f"{Config.GITHUB_API_BASE}/user/codespaces/{codespace_id}/start"
            response = requests.post(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            logger.info(f"Started codespace {codespace_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start codespace {codespace_id}: {e}")
            return False
    
    def stop_codespace(self, codespace_id: str) -> bool:
        """Stop a codespace."""
        try:
            url = f"{Config.GITHUB_API_BASE}/user/codespaces/{codespace_id}/stop"
            response = requests.post(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            logger.info(f"Stopped codespace {codespace_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop codespace {codespace_id}: {e}")
            return False
    
    def get_codespace_status(self, codespace_id: str) -> str:
        """Get codespace status."""
        cs = self.get_codespace_by_id(codespace_id)
        return cs.get("state", "UNKNOWN") if cs else "NOT_FOUND"
    
    def access_codespace_vscode(self, codespace_id: str) -> bool:
        """Access codespace via VS Code web URL to keep alive."""
        try:
            cs = self.get_codespace_by_id(codespace_id)
            if not cs:
                return False
            
            # Get web URL for accessing the codespace
            vscode_url = cs.get("web_url", "")
            if not vscode_url:
                return False
            
            # Add dev container path to trigger actual access
            access_url = f"{vscode_url}?folder=/workspaces"
            
            # Make request to access the codespace
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            # First request to get cookies
            response = session.get(vscode_url, timeout=Config.ACCESS_DURATION_SECONDS)
            
            # Second request to simulate activity
            time.sleep(2)
            response2 = session.get(access_url, timeout=Config.ACCESS_DURATION_SECONDS)
            
            # Check if we got a successful response
            if response.status_code == 200 or response2.status_code == 200:
                logger.info(f"Successfully accessed codespace: {codespace_id}")
                return True
            else:
                logger.warning(f"Access attempt failed for {codespace_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error accessing codespace {codespace_id}: {e}")
            return False
    
    def get_codespace_machine(self, codespace_id: str) -> Dict:
        """Get machine information for codespace."""
        try:
            url = f"{Config.GITHUB_API_BASE}/user/codespaces/{codespace_id}/machines"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            machines = response.json().get("machines", [])
            return machines[0] if machines else {}
        except Exception as e:
            logger.error(f"Failed to get machine info: {e}")
            return {}
    
    def list_available_machines(self) -> List[Dict]:
        """List available machine types."""
        try:
            url = f"{Config.GITHUB_API_BASE}/user/codespaces/machines"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json().get("machines", [])
        except Exception as e:
            logger.error(f"Failed to get machines: {e}")
            return []

# ==================== KEEP-ALIVE ENGINE ====================
class KeepAliveEngine:
    """Engine to keep codespaces alive."""
    
    def __init__(self, github_manager: GitHubCodespaceManager):
        self.github = github_manager
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the keep-alive engine."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Keep-alive engine started")
    
    def stop(self):
        """Stop the keep-alive engine."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Keep-alive engine stopped")
    
    def _run_scheduler(self):
        """Run the scheduling loop."""
        # Schedule keep-alive checks
        schedule.every(Config.CHECK_INTERVAL_MINUTES).minutes.do(self._check_all_codespaces)
        
        # Initial check
        self._check_all_codespaces()
        
        # Main scheduling loop
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _check_all_codespaces(self):
        """Check and keep alive all registered codespaces."""
        logger.info("Performing scheduled keep-alive check...")
        
        codespaces = DataStore.get_codespaces()
        if not codespaces:
            logger.warning("No codespaces registered for keep-alive")
            return
        
        success_count = 0
        total_count = len(codespaces)
        
        for codespace_id, info in codespaces.items():
            try:
                # Check if codespace exists
                cs = self.github.get_codespace_by_id(codespace_id)
                if not cs:
                    logger.warning(f"Codespace {codespace_id} not found, removing")
                    DataStore.delete_codespace(codespace_id)
                    continue
                
                # Get status
                status = cs.get("state", "UNKNOWN")
                logger.info(f"Codespace {codespace_id}: {status}")
                
                # If stopped, start it
                if status == "Shutdown" or status == "Stopped":
                    logger.info(f"Starting stopped codespace {codespace_id}")
                    if self.github.start_codespace(codespace_id):
                        time.sleep(10)  # Wait for startup
                
                # Access the codespace to keep it alive
                if self.github.access_codespace_vscode(codespace_id):
                    success_count += 1
                    logger.info(f"Successfully kept alive: {codespace_id}")
                    
                    # Update last access time
                    info["last_access"] = datetime.now().isoformat()
                    DataStore.save_codespace(codespace_id, info)
                
                else:
                    logger.warning(f"Failed to keep alive: {codespace_id}")
                
                # Small delay between codespaces
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error processing codespace {codespace_id}: {e}")
        
        # Update statistics
        DataStore.update_stats("total_checks")
        DataStore.update_stats("successful_keeps", value=success_count)
        DataStore.update_stats("failed_attempts", value=total_count - success_count)
        DataStore.update_stats("last_check", value=datetime.now().isoformat())
        DataStore.update_stats("codespace_count", value=total_count)
        
        logger.info(f"Keep-alive check completed: {success_count}/{total_count} successful")

# ==================== TELEGRAM BOT HANDLERS ====================
class TelegramBot:
    """Telegram Bot for managing codespaces."""
    
    def __init__(self):
        self.github = GitHubCodespaceManager()
        self.keepalive = KeepAliveEngine(self.github)
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        chat_id = update.effective_chat.id
        
        # Add user as admin
        DataStore.add_admin(chat_id)
        Config.ADMIN_CHAT_IDS.add(chat_id)
        
        welcome_text = """
🤖 *GitHub Codespace Keep-Alive Bot*

This bot will keep your GitHub Codespaces active by accessing them every hour.

*Available Commands:*
/start - Start the bot
/help - Show help
/list - List all codespaces
/add - Add a codespace
/remove - Remove a codespace
/status - Check status
/keepalive - Force keep-alive now
/stats - Show statistics
/stop - Stop keep-alive engine

*Quick Setup:*
1. Send /list to see your codespaces
2. Send /add <codespace_name> to add one
3. Bot will automatically keep it alive

*GitHub Token Needed:*
You need a GitHub Personal Access Token with `codespace` permissions.
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
*GitHub Codespace Keep-Alive Bot Help*

*How it works:*
- Bot accesses your Codespace every 55 minutes
- Prevents automatic shutdown due to inactivity
- Works even when you're not actively using it

*Commands:*
/start - Initialize the bot
/list - List your GitHub Codespaces
/add <name> - Add codespace to keep-alive
/remove <id> - Remove codespace
/status - Check codespace status
/keepalive - Force immediate keep-alive
/stats - Show bot statistics
/stop - Stop the keep-alive engine
/setinterval <minutes> - Change check interval

*Examples:*
/add Jacky
/remove cs_abc123
/setinterval 45
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command - List all codespaces."""
        chat_id = update.effective_chat.id
        if chat_id not in Config.ADMIN_CHAT_IDS:
            await update.message.reply_text("❌ You are not authorized.")
            return
        
        await update.message.reply_text("📋 Fetching your codespaces...")
        
        try:
            codespaces = self.github.get_all_codespaces()
            
            if not codespaces:
                await update.message.reply_text("No codespaces found.")
                return
            
            response = f"*Found {len(codespaces)} Codespaces:*\n\n"
            
            for i, cs in enumerate(codespaces, 1):
                name = cs.get("name", "Unknown")
                display_name = cs.get("display_name", "No display name")
                state = cs.get("state", "UNKNOWN")
                last_used = cs.get("last_used_at", "Never")
                cs_id = cs.get("id", "N/A")
                
                response += f"*{i}. {display_name}*\n"
                response += f"   ID: `{cs_id}`\n"
                response += f"   Name: {name}\n"
                response += f"   Status: {state}\n"
                response += f"   Last Used: {last_used[:10] if last_used != 'Never' else 'Never'}\n"
                response += f"   Add with: `/add {name}`\n\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add command - Add codespace to keep-alive."""
        chat_id = update.effective_chat.id
        if chat_id not in Config.ADMIN_CHAT_IDS:
            await update.message.reply_text("❌ You are not authorized.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /add <codespace_name_or_id>")
            return
        
        search_term = ' '.join(context.args)
        await update.message.reply_text(f"🔍 Searching for codespace: {search_term}")
        
        try:
            # Try to find by name first
            codespace = self.github.get_codespace_by_name(search_term)
            
            if not codespace:
                # Try to get directly by ID
                codespace = self.github.get_codespace_by_id(search_term)
            
            if not codespace:
                await update.message.reply_text("❌ Codespace not found.")
                return
            
            codespace_id = codespace.get("id")
            name = codespace.get("name")
            display_name = codespace.get("display_name", name)
            
            # Save to database
            DataStore.save_codespace(codespace_id, {
                "name": name,
                "display_name": display_name,
                "added_date": datetime.now().isoformat(),
                "last_access": datetime.now().isoformat(),
                "added_by": chat_id
            })
            
            # Start keep-alive engine if not running
            if not self.keepalive.running:
                self.keepalive.start()
            
            response = f"""
✅ *Codespace Added Successfully!*

*Name:* {display_name}
*ID:* `{codespace_id}`
*Status:* {codespace.get('state', 'UNKNOWN')}
*Added:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Bot will now keep this codespace alive automatically.
            """
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error adding codespace: {str(e)}")
    
    async def remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /remove command."""
        chat_id = update.effective_chat.id
        if chat_id not in Config.ADMIN_CHAT_IDS:
            await update.message.reply_text("❌ You are not auth
