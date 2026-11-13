import os
import json
import threading
import asyncio
import datetime
import random
from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# ==================== 1. Flask 保活服务 ====================
app = Flask('')

@app.route('/')
def home():
    return 'Voice, Account & Pet Bot is active and running!'

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

# 禁用默认 help，使用自定义精美帮助菜单
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'✅ Bot 已成功登录: {bot.user}')
    print('-----------------------------------------')

# ==================== 3. 数据持久化存储函数 ====================
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
        "checkins": {},
        "pet": {"name": "团子", "hunger": 80, "affection": 50, "level": 1, "exp": 0}
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 获取宠物等级称号的辅助函数
def get_pet_title(level):
    if level >= 5:
        return "✨ 神级幻兽 (传说守护)"
    elif level >= 3:
        return "⭐ 进阶灵兽 (资深伙伴)"
    else:
        return "🌱 初级萌宠 (实习可爱)"

# ==================== 4. 自定义 .help 帮助菜单 ====================
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
        name="📊 智能分类记账本",
        value=(
            "`.earn <金额> <分类> <备注>` - 记录收入\n"
            "`.spend <金额> <分类> <备注>` - 记录支出\n"
            "`.balance` - 查看总账、分类净结余（自动收支抵消）与最近明细\n"
            "`.clear` - 清空并重置所有账单数据"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⏰ 工具与联动",
        value=(
            "`.timer <时间(支持s/m/h/d)> <提醒内容>` - 设置倒计时提醒\n"
            "`.checkin <心情>` - 每日心情打卡（**自动联动喂养宠物**）"
        ),
        inline=False
    )

    embed.add_field(
        name="🐾 虚拟宠物养成系统",
        value=(
            "`.pet` - 查看宠物状态面板与实时心声\n"
            "`.feed` - 给宠物喂食（饱食度 +25）\n"
            "`.play` - 和宠物玩耍（经验 +35）\n"
            "`.pat` - 摸摸宠物（好感度 +8）\n"
            "`.explore` - 让宠物出门探险寻宝\n"
            "`.rename <新名字>` - 给宠物修改专属名字"
        ),
        inline=False
    )
    
    embed.set_footer(text="✨ Powered by Python & Render | 随时陪伴你哦~")
    await ctx.send(embed=embed)

# ==================== 5. 语音陪伴挂机指令 ====================
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

# ==================== 6. 记账助手功能（含分类净结余抵消） ====================
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

@bot.command(name='balance', help='查看当前账单结余、分类净值与最近明细')
async def balance(ctx):
    data = load_data()
    earn_total = data["total_earn"]
    spend_total = data["total_spend"]
    net = earn_total - spend_total
    
    # 自动计算每个分类的净结余（收入 - 支出）
    all_categories = set(data["category_earn"].keys()) | set(data["category_spend"].keys())
    cat_net_list = []
    
    for cat in all_categories:
        cat_earn = data["category_earn"].get(cat, 0.0)
        cat_spend = data["category_spend"].get(cat, 0.0)
        cat_net = cat_earn - cat_spend
        
        if cat_net > 0:
            cat_net_list.append(f"🟢 {cat}: `+¥{cat_net}`")
        elif cat_net < 0:
            cat_net_list.append(f"🔴 {cat}: `-¥{abs(cat_net)}`")
        else:
            cat_net_list.append(f"⚪ {cat}: `¥0`")

    cat_summary_str = "\n".join(cat_net_list) if cat_net_list else "暂无分类记录"

    recent_details = data["details"][-5:]
    details_str = "\n".join(recent_details) if recent_details else "暂无记账记录"
    
    msg = (
        f"📊 **当前财务账单面板**\n"
        f"-----------------------------------\n"
        f"🟢 累计总收入: `¥{earn_total}`\n"
        f"🔴 累计总支出: `¥{spend_total}`\n"
        f"💰 当前总结余: **`¥{net}`**\n"
        f"-----------------------------------\n"
        f"🏷️ **各分类净结余 (自动抵消后):**\n{cat_summary_str}\n"
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

# ==================== 7. 智能多单位倒计时与签到联动打卡 ====================
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

@bot.command(name='checkin', help='每日心情签到（顺便喂养宠物）')
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
    
    # 🌟 签到联动宠物：顺便喂养宠物加经验
    if "pet" not in data:
        data["pet"] = {"name": "团子", "hunger": 80, "affection": 50, "level": 1, "exp": 0}
    
    pet = data["pet"]
    pet["hunger"] = min(100, pet["hunger"] + 20)
    pet["affection"] = min(100, pet["affection"] + 5)
    pet["exp"] += 20
    
    level_up_msg = ""
    if pet["exp"] >= 100:
        pet["level"] += 1
        pet["exp"] -= 100
        level_up_msg = f"\n🎉 **签到福利！宠物金光一闪，升级到了 Lv.{pet['level']} ({get_pet_title(pet['level'])})！**"

    save_data(data)
    
    await ctx.send(
        f"✅ **签到成功！**\n"
        f"👤 签到人: `{ctx.author.name}` | 🌈 心情: `{mood}` | 🔥 连续签到: `{user_record['streak']} 天`\n"
        f"🐾 **宠物联动**：因为你完成了签到，顺便喂了 **{pet['name']}** 饱食度 `+20`，好感度 `+5`，宠物经验 `+20`！{level_up_msg}"
    )

# ==================== 8. 进阶虚拟宠物养成系统 ====================
@bot.command(name='pet', help='查看你的专属虚拟宠物状态')
async def pet_status(ctx):
    data = load_data()
    if "pet" not in data:
        data["pet"] = {"name": "团子", "hunger": 80, "affection": 50, "level": 1, "exp": 0}
        save_data(data)
    
    pet = data["pet"]
    name = pet['name']
    title = get_pet_title(pet['level'])
    
    if pet['hunger'] < 30:
        mood_talk = f"呜呜，{name} 的肚子快饿扁啦！快用 `.feed` 喂我好吃的~"
    elif pet['affection'] > 80:
        mood_talk = f"蹭蹭主人~ {name} 最喜欢你啦！✨"
    elif pet['level'] >= 3:
        mood_talk = f"哼哼，本 {name} 现在可是 {title} 呢，快夸夸我！"
    else:
        mood_talk = f"眨巴眼睛看着你，摇了摇尾巴~"

    msg = (
        f"🐾 **你的专属虚拟宠物：{name}**\n"
        f"-----------------------------------\n"
        f"👑 当前称号: **`{title}`**\n"
        f"💬 **宠物心声**: *\"{mood_talk}\"*\n"
        f"⭐ 等级: `Lv.{pet['level']}` (经验: {pet['exp']}/100)\n"
        f"🍖 饱食度: `{pet['hunger']}/100`\n"
        f"💖 好感度: `{pet['affection']}/100`\n"
        f"-----------------------------------\n"
        f"💡 **互动指令**：`.feed` 喂食 | `.play` 玩耍 | `.pat` 摸摸 | `.explore` 探险 | `.rename` 改名"
    )
    await ctx.send(msg)

@bot.command(name='feed', help='给宠物喂食，增加饱食度和好感度')
async def pet_feed(ctx):
    data = load_data()
    if "pet" not in data:
        data["pet"] = {"name": "团子", "hunger": 80, "affection": 50, "level": 1, "exp": 0}
    
    pet = data["pet"]
    if pet["hunger"] >= 100:
        await ctx.send(f"🐾 **{pet['name']}** 摸了摸溜圆的小肚子，打了个饱嗝：\"吃不下啦主人！\"")
        return
        
    pet["hunger"] = min(100, pet["hunger"] + 25)
    pet["affection"] = min(100, pet["affection"] + 5)
    save_data(data)
    
    await ctx.send(f"🍖 你给 **{pet['name']}** 喂了一份美味的食物！饱食度 `+25`，好感度 `+5` 💖 满足地眯起了眼睛~")

@bot.command(name='play', help='和宠物玩耍，增加经验和等级')
async def pet_play(ctx):
    data = load_data()
    if "pet" not in data:
        data["pet"] = {"name": "团子", "hunger": 80, "affection": 50, "level": 1, "exp": 0}
    
    pet = data["pet"]
    if pet["hunger"] < 20:
        await ctx.send(f"🐾 **{pet['name']}** 饿得趴在地上动弹不得：\"先喂我吃东西（`.feed`），才有力气陪你玩嘛……\"")
        return
        
    pet["hunger"] = max(0, pet["hunger"] - 20)
    pet["exp"] += 35
    pet["affection"] = min(100, pet["affection"] + 10)
    
    level_up_msg = ""
    if pet["exp"] >= 100:
        pet["level"] += 1
        pet["exp"] -= 100
        level_up_msg = f"\n🎉 **金光一闪！{pet['name']} 升级到了 Lv.{pet['level']} ({get_pet_title(pet['level'])})！**"
        
    save_data(data)
    
    await ctx.send(f"🎾 你开心地和 **{pet['name']}** 玩了一会儿抛球游戏！经验 `+35`，好感度 `+10`，饱食度 `-20`。{level_up_msg}")

@bot.command(name='pat', help='摸摸你的宠物，增加好感度')
async def pet_pat(ctx):
    data = load_data()
    if "pet" not in data:
        data["pet"] = {"name": "团子", "hunger": 80, "affection": 50, "level": 1, "exp": 0}
    
    pet = data["pet"]
    pet["affection"] = min(100, pet["affection"] + 8)
    save_data(data)
    
    pat_reactions = [
        f"舒舒服服地眯起眼睛，发出呼噜呼噜的声音~ 好感度 `+8` 💖",
        f"开心地转了个圈，用头蹭了蹭你的手心！好感度 `+8` 💖",
        f"尾巴摇得像个小风扇，高兴得快要跳起来啦！好感度 `+8` 💖"
    ]
    await ctx.send(f"👋 你轻轻摸了摸 **{pet['name']}** 的脑袋：{random.choice(pat_reactions)}")

@bot.command(name='explore', help='让宠物出去探险，带回经验和惊喜')
async def pet_explore(ctx):
    data = load_data()
    if "pet" not in data:
        data["pet"] = {"name": "团子", "hunger": 80, "affection": 50, "level": 1, "exp": 0}
    
    pet = data["pet"]
    if pet["hunger"] < 30:
        await ctx.send(f"🐾 **{pet['name']}** 肚子太饿了，拒绝出门探险：\"不吃饱肚子怎么有力气跑远路嘛！\"")
        return
        
    pet["hunger"] = max(0, pet["hunger"] - 25)
    
    exp_gain = random.randint(25, 50)
    pet["exp"] += exp_gain
    
    level_up_msg = ""
    if pet["exp"] >= 100:
        pet["level"] += 1
        pet["exp"] -= 100
        level_up_msg = f"\n🎉 **探险归来时突然顿悟，晋升为 Lv.{pet['level']} ({get_pet_title(pet['level'])})！**"
        
    save_data(data)
    
    adventures = [
        "在花园里抓了一只蝴蝶，顺便踩了几个梅花脚印",
        "在路边捡到了一颗亮晶晶的小石头，开心地叼了回来",
        "跟邻居家的猫咪友好交流了一番，学到了不少生存小技巧",
        "在草丛里睡了个懒觉，顺便晒了个暖洋洋的太阳"
    ]
    
    await ctx.send(f"🗺️ **{pet['name']}** 背着小书包出去探险啦！它{random.choice(adventures)}。\n✨ 获得探险经验 `+{exp_gain}`，饱食度 `-25`。{level_up_msg}")

@bot.command(name='rename', help='给你的虚拟宠物修改名字。用法：.rename 布丁')
async def pet_rename(ctx, *, new_name: str):
    new_name = new_name.strip()
    if not new_name:
        await ctx.send('❌ 宠物名字不能为空哟！')
        return
        
    data = load_data()
    if "pet" not in data:
        data["pet"] = {"name": "团子", "hunger": 80, "affection": 50, "level": 1, "exp": 0}
    
    old_name = data["pet"]["name"]
    data["pet"]["name"] = new_name
    save_data(data)
    
    await ctx.send(f'✨ 宠物名字修改成功！原本的 **{old_name}** 现在正式改名为 **{new_name}** 啦！ 🎉')

# ==================== 9. 主程序入口 ====================
if __name__ == '__main__':
    keep_alive()
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        raise ValueError('未找到 DISCORD_TOKEN 环境变量！')
    bot.run(TOKEN)
