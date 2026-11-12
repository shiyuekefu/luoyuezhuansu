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
# ==================== 5. 记账小助手功能 ====================

# 用一个简单的字典或文件来存账目（目前存放在内存中，重启会清空；如果想永久保存，后面可以加文件读写）
# 格式: {"total_earn": 0.0, "total_spend": 0.0, "details": []}
account_data = {
    "total_earn": 0.0,
    "total_spend": 0.0,
    "details": []
}

# 1. 记录花销
@bot.command(name='spend', help='记录花销。用法：!spend 50 喝奶茶')
async def spend(ctx, amount: float, *, note: str = "未备注"):
    if amount <= 0:
        await ctx.send('❌ 金额必须大于 0 哟！')
        return
    
    account_data["total_spend"] += amount
    account_data["details"].append(f"🔴 支出: `-¥{amount}` | 备注: {note} | 记录人: {ctx.author.name}")
    
    await ctx.send(f'📝 成功记一笔支出：`-¥{amount}` ({note})，目前总支出：`¥{account_data["total_spend"]}`')

# 2. 记录收入
@bot.command(name='earn', help='记录收入。用法：!earn 200 卖闲置')
async def earn(ctx, amount: float, *, note: str = "未备注"):
    if amount <= 0:
        await ctx.send('❌ 金额必须大于 0 哟！')
        return
    
    account_data["total_earn"] += amount
    account_data["details"].append(f"🟢 收入: `+¥{amount}` | 备注: {note} | 记录人: {ctx.author.name}")
    
    await ctx.send(f'📝 成功记一笔收入：`+¥{amount}` ({note})，目前总收入：`¥{account_data["total_earn"]}`')

# 3. 查看账单和结余
@bot.command(name='balance', help='查看当前账单结余与明细')
async def balance(ctx):
    earn_total = account_data["total_earn"]
    spend_total = account_data["total_spend"]
    net = earn_total - spend_total
    
    # 获取最近的 5 条明细
    recent_details = account_data["details"][-5:]
    details_str = "\n".join(recent_details) if recent_details else "暂无记账记录"
    
    msg = (
        f"📊 **当前财务账单面板**\n"
        f"-----------------------------------\n"
        f"🟢 总收入: `¥{earn_total}`\n"
        f"🔴 总支出: `¥{spend_total}`\n"
        f"💰 当前结余: **`¥{net}`**\n"
        f"-----------------------------------\n"
        f"📜 **最近动态 (最近5条):**\n{details_str}"
    )
    await ctx.send(msg)
# ==================== 4. 主程序入口 ====================
if __name__ == '__main__':
    keep_alive()
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        raise ValueError('未找到 DISCORD_TOKEN 环境变量！')
    bot.run(TOKEN)
