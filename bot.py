import os
import threading
from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv

# 加载本地的 .env 文件（如果在 Render 云端，它会自动读取后台的环境变量）
load_dotenv()

# ==================== 1. Flask 保活服务配置 ====================
app = Flask('')


@app.route('/')
def home():
  return 'Bot is active and running!'


def run_flask():
  # 绑定 0.0.0.0 和 8080 端口供 Render 健康检查
  app.run(host='0.0.0.0', port=8080)


def keep_alive():
  t = threading.Thread(target=run_flask)
  t.daemon = True
  t.start()


# ==================== 2. Discord Bot 核心逻辑 ====================
intents = discord.Intents.default()
intents.message_content = True  # 允许读取消息内容（必须在开发者后台勾选）

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
  print(f'✅ 已成功登录为: {bot.user} (ID: {bot.user.id})')
  print('-----------------------------------------')


# 测试命令：!ping
@bot.command(name='ping')
async def ping(ctx):
  latency = round(bot.latency * 1000)
  await ctx.send(f'🏓 Pong! 延迟为: `{latency}ms`')


# ==================== 3. 主程序入口 ====================
if __name__ == '__main__':
  # 1. 启动 Flask 保活线程
  keep_alive()

  # 2. 安全获取 Token
  TOKEN = os.getenv('DISCORD_TOKEN')
  if not TOKEN:
    raise ValueError(
        '未找到 DISCORD_TOKEN 环境变量，请检查本地 .env 或云端环境变量配置！'
    )

  # 3. 启动 Bot
  bot.run(TOKEN)
