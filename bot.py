import os
import threading
from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# ==================== 1. Flask 保活服务 ====================
app = Flask('')

@app.route('/')
def home():
    return 'Voice Bot is active and running!'

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# ==================== 2. Discord Bot 配置 ====================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True  # 必须开启语音状态意图（在开发者后台也要勾选！）

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ 语音陪伴 Bot 已成功登录: {bot.user}')
    print('-----------------------------------------')

# ==================== 3. 语音挂机陪伴指令 ====================

# 指令 1：让 Bot 进来你当前所在的语音频道挂机
@bot.command(name='join', help='让 Bot 进入你当前所在的语音频道陪伴挂机')
async def join(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send('❌ 你得先加入一个语音频道，我才能去找你呀！')
        return

    voice_channel = ctx.author.voice.channel
    
    # 如果已经在其他语音里，先断开
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(voice_channel)
        await ctx.send(f'🔀 已经切换到语音频道: **{voice_channel.name}** 陪你啦！')
    else:
        # 连接到语音频道
        await voice_channel.connect()
        await ctx.send(f'🎧 成功加入语音频道: **{voice_channel.name}**，开始 24 小时陪伴！')

# 指令 2：让 Bot 离开语音频道
@bot.command(name='leave', help='让 Bot 退出语音频道')
async def leave(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        await ctx.send('👋 已经断开语音连接，下次见啦！')
    else:
        await ctx.send('❌ 我现在不在任何语音频道里哦。')

# 自动防掉线/重连事件：如果被意外踢出或断开，尝试恢复
@bot.event
async def on_voice_state_update(member, before, after):
    # 如果是 bot 自己被移出了频道，可以在这里处理
    if member.id == bot.user.id:
        if before.channel is not None and after.channel is None:
            print('⚠️ 监测到 Bot 被移出语音频道。')

# ==================== 4. 主程序入口 ====================
if __name__ == '__main__':
    keep_alive()
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        raise ValueError('未找到 DISCORD_TOKEN 环境变量！')
    bot.run(TOKEN)
