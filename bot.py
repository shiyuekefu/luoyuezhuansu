import os
import json
import threading
import asyncio
import datetime
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

bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'✅ Bot 已成功登录: {bot.user}')
    print('-----------------------------------------')

# ==================== 3. 自定义 .help 帮助菜单 ====================
@bot.command(name='help', help='查看所有可用的指令帮助菜单')
async def custom_help(ctx):
    embed = discord.Embed(
        title="🤖 机器人指令帮助指南",
        description="这里是当前所有可用的功能指令列表，快来试试吧！",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="🎧 语音陪伴",
        value=(
            "`.join` - 让 Bot 加入你当前所在的语音频道\n"
            "`.leave` - 让 Bot 退出语音频道"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📊 分类记账本",
        value=(
            "`.earn <金额> <分类> <备注>` - 记录收入\n"
            "`.spend <金额> <分类> <备注>` - 记录支出\n"
            "`.balance` - 查看总账、分类汇总与最近明细\n"
            "`.clear` - 清空并重置所有账单数据"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⏰ 工具与互动",
        value=(
            "`.timer <时间(支持s/m/h/d)> <提醒内容>` - 设置倒计时提醒\n"
            "`.checkin <心情>` - 每日心情打卡与连续签到"
        ),
        inline=False
    )
    
    embed.set_footer(text="✨ Powered by Python & Render | 随时陪伴你哦~")
    await ctx.send(embed=embed)

# ==================== 4. 语音陪伴挂机指令 ====================

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

# ==================== 5. 带分类与持久化存储的记账助手 ====================

DATA_FILE = "account.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "total_earn": 0.0,
        "total_spend": 0.0,
        "category_earn": {},
        "category_spend": {},
        "details": [],
        "checkins": {}
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@bot.command(name='earn', help='记录收入。用法：.earn 500 工资 兼职收入')
async def earn(ctx, amount: float, category: str, *, note: str = "未备注"):
    if amount <= 0:
        await ctx.send('❌ 金额必须大于 0 哟！')
        return
    
    data = load_data()
    data["total_earn"] += amount
    
    if category not in data["category_earn"]:
        data["category_earn"][category] = 0.0
    data["category_earn"][category] += amount
    
    data["details"].append(f"🟢 收入: `+¥{amount}` | 分类: **[{category}]** | 备注: {note} | 记录人: {ctx.author.name}")
    save_data(data)
    
    await ctx.send(f'📝 成功记入收入：`+¥{amount}` (分类: **{category}**，备注: {note})，目前总收入：`¥{data["total_earn"]}`')

@bot.command(name='spend', help='记录花销。用法：.spend 45 餐饮 午饭')
async def spend(ctx, amount: float, category: str, *, note: str = "未备注"):
    if amount <= 0:
        await ctx.send('❌ 金额必须大于 0 哟！')
        return
    
    data = load_data()
    data["total_spend"] += amount
    
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
    
    earn_cat_str = " | ".join([f"{cat}: ¥{amt}" for cat, amt in data["category_earn"].items()]) if data["category_earn"] else "暂无收入分类"
    spend_cat_str = " | ".join([f"{cat}: ¥{amt}" for cat, amt in data["category_spend"].items()]) if data["category_spend"] else "暂无支出分类"

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
    data = load_data()
    data["total_earn"] = 0.0
    data["total_spend"] = 0.0
    data["category_earn"] = {}
    data["category_spend"] = {}
    data["details"] = []
    save_data(data)
    await ctx.send('🗑️ 账单已成功清空，所有分类、收入、支出和明细已重置为 0！')

# ==================== 6. 智能倒计时提醒与签到打卡 ====================

@bot.command(name='timer', help='设置倒计时。用法：.timer 2d 记得打卡 或 .timer 5m 泡面好了')
async def timer(ctx, time_str: str, *, message: str = "时间到！"):
    seconds = 0
    time_str = time_str.lower()
    
    try:
        if time_str.endswith('s'):
            seconds = int(time_str[:-1])
        elif time_str.endswith('m'):
            seconds = int(time_str[:-1]) * 60
        elif time_str.endswith('h'):
            seconds = int(time_str[:-1]) * 3600
        elif time_str.endswith('d'):
            seconds = int(time_str[:-1]) * 86400
        else:
            seconds = int(time_str)
    except ValueError:
        await ctx.send('❌ 时间格式写错啦！请使用数字加上单位，例如：`30s`（秒）、`5m`（分钟）、`2h`（小时）、`1d`（天）。')
        return

    if seconds <= 0:
        await ctx.send('❌ 倒计时时间必须大于 0 哟！')
        return
        
    await ctx.send(f'⏳ 计时器已启动！将在 **{time_str}** 后提醒你：{message}')
    await asyncio.sleep(seconds)
    await ctx.send(f'⏰ **{ctx.author.mention} 叮咚！时间到啦：** {message}')

@bot.command(name='checkin', help='每日心情签到。用法：.checkin 开心')
async def checkin(ctx, *, mood: str = "正常"):
    data = load_data()
    if "checkins" not in data:
        data["checkins"] = {}
    
    user_id = str(ctx.author.id)
    today = datetime.date.today().isoformat()
    
    user_record = data["checkins"].get(user_id, {"last_date": "", "streak": 0, "mood": ""})
    
    if user_record["last_date"] == today:
        await ctx.send(f'✨ {ctx.author.name}，你今天已经签到过了哦！今日心情：`{user_record["mood"]}`')
        return
    
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    if user_record["last_date"] == yesterday:
        user_record["streak"] += 1
    else:
        user_record["streak"] = 1
        
    user_record["last_date"] = today
    user_record["mood"] = mood
    data["checkins"][user_id] = user_record
    save_data(data)
    
    await ctx.send(f'✅ **签到成功！**\n👤 签到人: `{ctx.author.name}`\n🌈 今日心情: `{mood}`\n🔥 连续签到: `{user_record["streak"]} 天`')
    # ==================== 7. 虚拟宠物养成系统 ====================

@bot.command(name='pet', help='查看你的专属虚拟宠物状态')
async def pet_status(ctx):
    data = load_data()
    if "pet" not in data:
        data["pet"] = {"name": "团子", "hunger": 80, "affection": 50, "level": 1, "exp": 0}
        save_data(data)
    
    pet = data["pet"]
    msg = (
        f"🐾 **你的专属虚拟宠物：{pet['name']}**\n"
        f"-----------------------------------\n"
        f"⭐ 等级: `Lv.{pet['level']}` (经验: {pet['exp']}/100)\n"
        f"🍖 饱食度: `{pet['hunger']}/100`\n"
        f"💖 好感度: `{pet['affection']}/100`\n"
        f"-----------------------------------\n"
        f"💡 提示：使用 `.feed` 喂食，使用 `.play` 和它玩耍！"
    )
    await ctx.send(msg)

@bot.command(name='feed', help='给宠物喂食，增加饱食度和好感度')
async def pet_feed(ctx):
    data = load_data()
    if "pet" not in data:
        data["pet"] = {"name": "团子", "hunger": 80, "affection": 50, "level": 1, "exp": 0}
    
    pet = data["pet"]
    if pet["hunger"] >= 100:
        await ctx.send(f"🐾 **{pet['name']}** 已经吃得饱饱的啦，暂时吃不下啦！")
        return
        
    pet["hunger"] = min(100, pet["hunger"] + 20)
    pet["affection"] = min(100, pet["affection"] + 5)
    save_data(data)
    
    await ctx.send(f"🍖 你给 **{pet['name']}** 喂了一份美味的食物！饱食度 `+20`，好感度 `+5` 💖")

@bot.command(name='play', help='和宠物玩耍，增加经验和等级')
async def pet_play(ctx):
    data = load_data()
    if "pet" not in data:
        data["pet"] = {"name": "团子", "hunger": 80, "affection": 50, "level": 1, "exp": 0}
    
    pet = data["pet"]
    if pet["hunger"] < 15:
        await ctx.send(f"🐾 **{pet['name']}** 肚子饿扁啦，快先用 `.feed` 喂它吃东西再玩吧！")
        return
        
    pet["hunger"] = max(0, pet["hunger"] - 15)
    pet["exp"] += 30
    pet["affection"] = min(100, pet["affection"] + 10)
    
    # 升级判定
    level_up_msg = ""
    if pet["exp"] >= 100:
        pet["level"] += 1
        pet["exp"] -= 100
        level_up_msg = f"\n🎉 **太棒了！宠物升级到了 Lv.{pet['level']}！**"
        
    save_data(data)
    
    await ctx.send(f"🎾 你开心地和 **{pet['name']}** 玩了一会儿！经验 `+30`，好感度 `+10`，饱食度 `-15`。{level_up_msg}")

# ==================== 7. 主程序入口 ====================
if __name__ == '__main__':
    keep_alive()
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        raise ValueError('未找到 DISCORD_TOKEN 环境变量！')
    bot.run(TOKEN)
