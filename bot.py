import os
import json
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
    return 'Voice & Account Bot is active and running!'

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
intents.voice_states = True

bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot 已成功登录: {bot.user}')
    print('-----------------------------------------')

# ==================== 3. 语音陪伴挂机指令 ====================

@bot.command(name='join', help='让 Bot 进入你当前所在的语音频道')
async def join(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send('❌ 你得先加入一个语音频道，我才能去找你呀！')
        return

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(voice_channel)
        await ctx.send(f'🔀 已经切换到语音频道: **{voice_channel.name}** 陪你啦！')
    else:
        await voice_channel.connect()
        await ctx.send(f'🎧 成功加入语音频道: **{voice_channel.name}**！')

@bot.command(name='leave', help='让 Bot 退出语音频道')
async def leave(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        await ctx.send('👋 已经断开语音连接，下次见啦！')
    else:
        await ctx.send('❌ 我现在不在任何语音频道哦。')

# ==================== 4. 带分类与持久化存储的记账助手 ====================

DATA_FILE = "account.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # 默认初始数据（增加 category_earn 和 category_spend 统计字典）
    return {
        "total_earn": 0.0,
        "total_spend": 0.0,
        "category_earn": {},
        "category_spend": {},
        "details": []
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@bot.command(name='earn', help='记录收入。用法：.earn 200 工资 兼职收入')
async def earn(ctx, amount: float, category: str, *, note: str = "未备注"):
    if amount <= 0:
        await ctx.send('❌ 金额必须大于 0 哟！')
        return
    
    data = load_data()
    data["total_earn"] += amount
    
    # 统计分类收入
    if category not in data["category_earn"]:
        data["category_earn"][category] = 0.0
    data["category_earn"][category] += amount
    
    data["details"].append(f"🟢 收入: `+¥{amount}` | 分类: **[{category}]** | 备注: {note} | 记录人: {ctx.author.name}")
    save_data(data)
    
    await ctx.send(f'📝 成功记入收入：`+¥{amount}` (分类: **{category}**，备注: {note})，目前总收入：`¥{data["total_earn"]}`')

@bot.command(name='spend', help='记录花销。用法：.spend 35 餐饮 午饭')
async def spend(ctx, amount: float, category: str, *, note: str = "未备注"):
    if amount <= 0:
        await ctx.send('❌ 金额必须大于 0 哟！')
        return
    
    data = load_data()
    data["total_spend"] += amount
    
    # 统计分类支出
    if category not in data["category_spend"]:
        data["category_spend"][category] = 0.0
    data["category_spend"][category] += amount
    
    data["details"].append(f"🔴 支出: `-¥{amount}` | 分类: **[{category}]** | 备注: {note} | 记录人: {ctx.author.name}")
    save_data(data)
    
    await ctx.send(f'📝 成功记入支出：`-¥{amount}` (分类: **{category}**，备注: {note})，目前总支出：`¥{data["total_spend"]}`')

@bot.command(name='balance', help='查看当前账单结余、分类统计与最近明细')
async def balance(ctx):
    data = load_data()
    earn_total = data["total_earn"]
    spend_total = data["total_spend"]
    net = earn_total - spend_total
    
    # 整理分类收入字符串
    earn_cat_str = ""
    if data["category_earn"]:
        earn_cat_str = " | ".join([f"{cat}: ¥{amt}" for cat, amt in data["category_earn"].items()])
    else:
        earn_cat_str = "暂无收入分类"

    # 整理分类支出字符串
    spend_cat_str = ""
    if data["category_spend"]:
        spend_cat_str = " | ".join([f"{cat}: ¥{amt}" for cat, amt in data["category_spend"].items()])
    else:
        spend_cat_str = "暂无支出分类"

    recent_details = data["details"][-5:]
    details_str = "\n".join(recent_details) if recent_details else "暂无记账记录"
    
    msg = (
        f"📊 **当前财务账单面板**\n"
        f"-----------------------------------\n"
        f"🟢 总收入: `¥{earn_total}` ({earn_cat_str})\n"
        f"🔴 总支出: `¥{spend_total}` ({spend_cat_str})\n"
        f"💰 当前结余: **`¥{net}`**\n"
        f"-----------------------------------\n"
        f"📜 **最近动态 (最近5条):**\n{details_str}"
    )
    await ctx.send(msg)

@bot.command(name='clear', help='清空并重置当前所有账单数据')
async def clear_account(ctx):
    empty_data = {
        "total_earn": 0.0,
        "total_spend": 0.0,
        "category_earn": {},
        "category_spend": {},
        "details": []
    }
    save_data(empty_data)
    await ctx.send('🗑️ 账单已成功清空，所有分类、收入、支出和明细已重置为 0！')

# ==================== 5. 主程序入口 ====================
if __name__ == '__main__':
    keep_alive()
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        raise ValueError('未找到 DISCORD_TOKEN 环境变量！')
    bot.run(TOKEN)
