#!/usr/bin/env python3
"""
GitHub Codespace Keep-Alive Telegram Bot - FIXED VERSION
Line 550 Syntax Error Fixed
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
from datetime import datetime
from typing import Dict, List, Optional

# Try to import telegram modules
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("❌ python-telegram-bot not installed. Run: pip install python-telegram-bot")
    TELEGRAM_AVAILABLE = False
    sys.exit(1)

import warnings
warnings.filterwarnings("ignore")

# ==================== CONFIGURATION ====================
class Config:
    """All configuration in one place."""
    
    # REPLACE THESE WITH YOUR ACTUAL TOKENS
    TELEGRAM_BOT_TOKEN = "7840587350:AAGq_IH6ZM2IOVD9Ih1rnzWdOauUCf42we4"  # Get from @BotFather
    GITHUB_TOKEN = "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"     # GitHub Personal Access Token
    GITHUB_USERNAME = "jackmodz0"    # Your GitHub username
    
    # Keep-Alive Settings
    CHECK_INTERVAL_MINUTES = 55
    ACCESS_DURATION_SECONDS = 60
    
    # Admin Chat IDs
    ADMIN_CHAT_IDS = set()
    
    # Files
    DATA_FILE = "codespace_data.json"
    LOG_FILE = "codespace_bot.log"
    
    # API
    GITHUB_API_BASE = "https://api.github.com"
    GITHUB_API_VERSION = "2022-11-28"

# ==================== LOGGING ====================
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
    """Simple JSON data storage."""
    
    @staticmethod
    def load():
        try:
            with open(Config.DATA_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"codespaces": {}, "admins": [], "stats": {}}
    
    @staticmethod
    def save(data):
        with open(Config.DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def get_codespaces():
        data = DataStore.load()
        return data.get("codespaces", {})
    
    @staticmethod
    def save_codespace(codespace_id, info):
        data = DataStore.load()
        data["codespaces"][codespace_id] = info
        DataStore.save(data)
    
    @staticmethod
    def delete_codespace(codespace_id):
        data = DataStore.load()
        if codespace_id in data["codespaces"]:
            del data["codespaces"][codespace_id]
            DataStore.save(data)
    
    @staticmethod
    def add_admin(chat_id):
        data = DataStore.load()
        admins = data.get("admins", [])
        if chat_id not in admins:
            admins.append(chat_id)
            data["admins"] = admins
            DataStore.save(data)
        Config.ADMIN_CHAT_IDS.add(chat_id)
    
    @staticmethod
    def get_stats():
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
        data = DataStore.load()
        stats = data.get("stats", {})
        
        if value is not None:
            stats[field] = value
        else:
            stats[field] = stats.get(field, 0) + increment
        
        data["stats"] = stats
        DataStore.save(data)

# ==================== GITHUB MANAGER ====================
class GitHubCodespaceManager:
    """GitHub Codespace API Manager."""
    
    def __init__(self):
        self.headers = {
            "Authorization": f"token {Config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": Config.GITHUB_API_VERSION
        }
    
    def get_all_codespaces(self):
        try:
            url = f"{Config.GITHUB_API_BASE}/user/codespaces"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json().get("codespaces", [])
        except Exception as e:
            logger.error(f"Failed to get codespaces: {e}")
            return []
    
    def get_codespace_by_name(self, name):
        codespaces = self.get_all_codespaces()
        for cs in codespaces:
            if name.lower() in cs.get("name", "").lower():
                return cs
            if name.lower() in cs.get("display_name", "").lower():
                return cs
        return None
    
    def get_codespace_by_id(self, codespace_id):
        try:
            url = f"{Config.GITHUB_API_BASE}/user/codespaces/{codespace_id}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get codespace {codespace_id}: {e}")
            return None
    
    def start_codespace(self, codespace_id):
        try:
            url = f"{Config.GITHUB_API_BASE}/user/codespaces/{codespace_id}/start"
            response = requests.post(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            logger.info(f"Started codespace {codespace_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start codespace {codespace_id}: {e}")
            return False
    
    def access_codespace_vscode(self, codespace_id):
        try:
            cs = self.get_codespace_by_id(codespace_id)
            if not cs:
                return False
            
            vscode_url = cs.get("web_url", "")
            if not vscode_url:
                return False
            
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            response = session.get(vscode_url, timeout=Config.ACCESS_DURATION_SECONDS)
            
            time.sleep(2)
            access_url = f"{vscode_url}?folder=/workspaces"
            response2 = session.get(access_url, timeout=Config.ACCESS_DURATION_SECONDS)
            
            if response.status_code == 200 or response2.status_code == 200:
                logger.info(f"Accessed codespace: {codespace_id}")
                return True
            else:
                logger.warning(f"Access failed for {codespace_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error accessing codespace {codespace_id}: {e}")
            return False

# ==================== KEEP-ALIVE ENGINE ====================
class KeepAliveEngine:
    """Keep-alive engine."""
    
    def __init__(self, github_manager):
        self.github = github_manager
        self.running = False
        self.thread = None
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Keep-alive engine started")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Keep-alive engine stopped")
    
    def _run_scheduler(self):
        schedule.every(Config.CHECK_INTERVAL_MINUTES).minutes.do(self._check_all_codespaces)
        
        self._check_all_codespaces()
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)
    
    def _check_all_codespaces(self):
        logger.info("Performing scheduled keep-alive check...")
        
        codespaces = DataStore.get_codespaces()
        if not codespaces:
            logger.warning("No codespaces registered")
            return
        
        success_count = 0
        total_count = len(codespaces)
        
        for codespace_id, info in codespaces.items():
            try:
                cs = self.github.get_codespace_by_id(codespace_id)
                if not cs:
                    logger.warning(f"Codespace {codespace_id} not found")
                    DataStore.delete_codespace(codespace_id)
                    continue
                
                status = cs.get("state", "UNKNOWN")
                logger.info(f"Codespace {codespace_id}: {status}")
                
                if status == "Shutdown" or status == "Stopped":
                    logger.info(f"Starting stopped codespace {codespace_id}")
                    if self.github.start_codespace(codespace_id):
                        time.sleep(10)
                
                if self.github.access_codespace_vscode(codespace_id):
                    success_count += 1
                    logger.info(f"Kept alive: {codespace_id}")
                    
                    info["last_access"] = datetime.now().isoformat()
                    DataStore.save_codespace(codespace_id, info)
                
                else:
                    logger.warning(f"Failed to keep alive: {codespace_id}")
                
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error processing codespace {codespace_id}: {e}")
        
        DataStore.update_stats("total_checks")
        DataStore.update_stats("successful_keeps", value=success_count)
        DataStore.update_stats("failed_attempts", value=total_count - success_count)
        DataStore.update_stats("last_check", value=datetime.now().isoformat())
        DataStore.update_stats("codespace_count", value=total_count)
        
        logger.info(f"Keep-alive check completed: {success_count}/{total_count} successful")

# ==================== TELEGRAM BOT ====================
class TelegramBot:
    """Telegram Bot."""
    
    def __init__(self):
        self.github = GitHubCodespaceManager()
        self.keepalive = KeepAliveEngine(self.github)
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        
        DataStore.add_admin(chat_id)
        Config.ADMIN_CHAT_IDS.add(chat_id)
        
        welcome_text = """
🤖 *GitHub Codespace Keep-Alive Bot*

*Commands:*
/start - Start bot
/help - Show help
/list - List codespaces
/add - Add codespace
/remove - Remove codespace
/status - Check status
/keepalive - Force keep-alive
/stats - Show statistics
/stop - Stop engine
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
*Bot Help*

*Commands:*
/start - Initialize bot
/list - List GitHub Codespaces
/add <name> - Add codespace
/remove <id> - Remove codespace
/status - Check status
/keepalive - Force keep-alive
/stats - Show statistics
/stop - Stop engine
/setinterval <minutes> - Change interval
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if chat_id not in Config.ADMIN_CHAT_IDS:
            await update.message.reply_text("❌ You are not authorized.")
            return
        
        await update.message.reply_text("📋 Fetching codespaces...")
        
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
        chat_id = update.effective_chat.id
        if chat_id not in Config.ADMIN_CHAT_IDS:
            await update.message.reply_text("❌ You are not authorized.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /add <codespace_name_or_id>")
            return
        
        search_term = ' '.join(context.args)
        await update.message.reply_text(f"🔍 Searching: {search_term}")
        
        try:
            codespace = self.github.get_codespace_by_name(search_term)
            
            if not codespace:
                codespace = self.github.get_codespace_by_id(search_term)
            
            if not codespace:
                await update.message.reply_text("❌ Codespace not found.")
                return
            
            codespace_id = codespace.get("id")
            name = codespace.get("name")
            display_name = codespace.get("display_name", name)
            
            DataStore.save_codespace(codespace_id, {
                "name": name,
                "display_name": display_name,
                "added_date": datetime.now().isoformat(),
                "last_access": datetime.now().isoformat(),
                "added_by": chat_id
            })
            
            if not self.keepalive.running:
                self.keepalive.start()
            
            response = f"""
✅ *Codespace Added!*

*Name:* {display_name}
*ID:* `{codespace_id}`
*Status:* {codespace.get('state', 'UNKNOWN')}
*Added:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if chat_id not in Config.ADMIN_CHAT_IDS:
            await update.message.reply_text("❌ You are not authorized.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /remove <codespace_id>")
            return
        
        codespace_id = context.args[0]
        
        DataStore.delete_codespace(codespace_id)
        
        await update.message.reply_text(f"✅ Removed: `{codespace_id}`", parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if chat_id not in Config.ADMIN_CHAT_IDS:
            await update.message.reply_text("❌ You are not authorized.")
            return
        
        codespaces = DataStore.get_codespaces()
        
        if not codespaces:
            await update.message.reply_text("No codespaces being kept alive.")
            return
        
        response = f"*Monitoring {len(codespaces)} Codespaces:*\n\n"
        
        for cs_id, info in codespaces.items():
            cs = self.github.get_codespace_by_id(cs_id)
            status = cs.get("state", "UNKNOWN") if cs else "NOT_FOUND"
            last_access = info.get("last_access", "Never")
            name = info.get("display_name", cs_id)
            
            if last_access != "Never":
                try:
                    last_dt = datetime.fromisoformat(last_access.replace('Z', '+00:00'))
                    last_str = last_dt.strftime('%H:%M:%S')
                except:
                    last_str = last_access
            
            response += f"*{name}*\n"
            response += f"Status: {status}\n"
            response += f"Last Access: {last_str}\n"
            response += f"ID: `{cs_id}`\n"
            response += f"Remove: /remove {cs_id}\n\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def keepalive_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if chat_id not in Config.ADMIN_CHAT_IDS:
            await update.message.reply_text("❌ You are not authorized.")
            return
        
        await update.message.reply_text("🔄 Force keeping alive...")
        
        def run_keepalive():
            self.keepalive._check_all_codespaces()
        
        thread = threading.Thread(target=run_keepalive, daemon=True)
        thread.start()
        
        await update.message.reply_text("✅ Keep-alive initiated.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if chat_id not in Config.ADMIN_CHAT_IDS:
            await update.message.reply_text("❌ You are not authorized.")
            return
        
        stats = DataStore.get_stats()
        codespaces = DataStore.get_codespaces()
        
        response = f"""
📊 *Bot Statistics*

*General:*
• Total Codespaces: {len(codespaces)}
• Admin Chats: {len(Config.ADMIN_CHAT_IDS)}
• Check Interval: {Config.CHECK_INTERVAL_MINUTES} minutes
• Engine Running: {'✅ Yes' if self.keepalive.running else '❌ No'}

*Keep-Alive Stats:*
• Total Checks: {stats.get('total_checks', 0)}
• Successful Keeps: {stats.get('successful_keeps', 0)}
• Failed Attempts: {stats.get('failed_attempts', 0)}
• Last Check: {stats.get('last_check', 'Never')}
        """
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if chat_id not in Config.ADMIN_CHAT_IDS:
            await update.message.reply_text("❌ You are not authorized.")
            return
        
        self.keepalive.stop()
        await update.message.reply_text("🛑 Keep-alive engine stopped.")
    
    async def setinterval_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if chat_id not in Config.ADMIN_CHAT_IDS:
            await update.message.reply_text("❌ You are not authorized.")
            return
        
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("Usage: /setinterval <minutes>")
            return
        
        minutes = int(context.args[0])
        
        if minutes < 5 or minutes > 120:
            await update.message.reply_text("Interval must be between 5 and 120 minutes.")
            return
        
        Config.CHECK_INTERVAL_MINUTES = minutes
        
        if self.keepalive.running:
            self.keepalive.stop()
            time.sleep(2)
            self.keepalive.start()
        
        await update.message.reply_text(f"✅ Interval set to {minutes} minutes.")
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
     
