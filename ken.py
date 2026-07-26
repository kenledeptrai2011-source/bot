import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import re
import random
import asyncio
from datetime import datetime, timedelta
import datetime
import calendar
import time

# ================== CẤU HÌNH ROLE & DATA ==================
LEVEL_ROLES = {
    10: 1487811181522452570,
    15: 1487811362926231723,
    20: 1487811612806086666,
    36: 1487811855261892690,
    40: 1487812040197148773,
    67: 1491787298826748115,
    100: 1495778647871590591,
    150: 1495779829717536950,
    200: 1495779996046852297
}

CONFIG_FILE = "config.json"
GIFTCODE_FILE = "giftcodes.json"
LEVEL_FILE = "levels.json"
ECON_FILE = "economy.json"
DAILY_FILE = "daily.json"
BUFF_FILE = "buffs.json"
INVETORY_FILE = "inventory.json"
DATA_FILE = "data.json"

# --- Định nghĩa hàm xử lý JSON (Nằm ở trên cùng) ---
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Nạp dữ liệu vào bộ nhớ
ban_data = load_json(DATA_FILE)
levels = load_json(LEVEL_FILE)
economy = load_json(ECON_FILE)
giftcodes = load_json(GIFTCODE_FILE)
config = load_json(CONFIG_FILE)
daily_data = load_json(DAILY_FILE)
active_buffs = load_json(BUFF_FILE)
inventory = load_json(INVETORY_FILE)
gift_cooldowns = {}

def save_all():
    global levels, economy, daily_data, giftcodes, active_buffs, inventory, ban_data
    try:
        save_json(LEVEL_FILE, levels)
        save_json(ECON_FILE, economy)
        save_json(DAILY_FILE, daily_data)
        save_json(GIFTCODE_FILE, giftcodes)
        save_json(BUFF_FILE, active_buffs)
        save_json(INVETORY_FILE, inventory)
        save_json(DATA_FILE, ban_data)
        print("--- [HỆ THỐNG] Đã lưu dữ liệu thành công! ---")
    except Exception as e:
        print(f"--- [LỖI] Không thể lưu dữ liệu: {e} ---")

LUCKY_GIFTS = [
    {"name": "5 Kim Cương 💎", "value": 5, "type": "diamond", "weight": 1},
    {"name": "100,000,000 Coins", "value": 100000000, "type": "coin", "weight": 0.5},
    {"name": "5,000,000 Coins", "value": 5000000, "type": "coin", "weight": 1.5},
    {"name": "2,000,000 Coins", "value": 2000000, "type": "coin", "weight": 3},
    {"name": "1,000,000 Coins", "value": 1000000, "type": "coin", "weight": 5},
    {"name": "500,000 Coins", "value": 500000, "type": "coin", "weight": 9},
    {"name": "100,000 Coins", "value": 100000, "type": "coin", "weight": 15},
    {"name": "50,000 Coins", "value": 50000, "type": "coin", "weight": 20},
    {"name": "10,000 Coins", "value": 10000, "type": "coin", "weight": 25},
    {"name": "5,000 Coins", "value": 5000, "type": "coin", "weight": 20}
]

def xp_needed(level):
    return int(100 * (level ** 1.5))

NAP_PACKAGES = {
    "5k": {"diamonds": 100, "label": "Gói Khởi Đầu (5k = 100KC)"},
    "20k": {"diamonds": 120, "label": "Gói 20k = 120KC"},
    "50k": {"diamonds": 290, "label": "Gói 50k = 300KC"},
    "100k": {"diamonds": 570, "label": "Gói 100k = 680KC"},
    "200k": {"diamonds": 1280, "label": "Gói 200k = 1400KC"},
    "500k": {"diamonds": 2830, "label": "Gói 500k = 2890KC"}
}

SHOP_ITEMS = {
    "x2_exp": {"name": "Buff X2 EXP (1 phút)", "price": 3000000, "multiplier": 2, "type": "exp"},
    "x4_exp": {"name": "Buff X4 EXP (1 phút)", "price": 6000000, "multiplier": 4, "type": "exp"},
    "x8_exp": {"name": "Buff X8 EXP (1 phút)", "price": 100000000, "multiplier": 8, "type": "exp"},
    "x16_exp": {"name": "Buff X16 EXP (1 phút)", "price": 16000000000000, "multiplier": 16, "type": "exp"},
    "x2_coin": {"name": "Buff X2 Tiền (1 phút)", "price": 5000000, "multiplier": 2, "type": "coin"},
    "x4_coin": {"name": "Buff X4 Tiền (1 phút)", "price": 10000000, "multiplier": 4, "type": "coin"},
    "x8_coin": {"name": "Buff X8 Tiền (1 phút)", "price": 200000000, "multiplier": 8, "type": "coin"},
    "x16_coin": {"name": "Buff X16 Tiền (1 phút)", "price": 25000000000000, "multiplier": 16, "type": "coin"},
    "role_vip1": {"name": "Role VIP 1", "price": 1000, "type": "role", "currency": "diamond", "role_id": 1496152438548336781},
    "role_vip2": {"name": "Role VIP 2", "price": 6000, "type": "role", "currency": "diamond", "role_id": 1496154307521941688},
    "role_vip3": {"name": "Role VIP 3", "price": 12000, "type": "role", "currency": "diamond", "role_id": 1496154436332945559},
    "role_vip4": {"name": "Role VIP 4", "price": 24000, "type": "role", "currency": "diamond", "role_id": 1496154550955020459},
    "ruong_luu_tru": {"name": "🎁 Rương lưu trữ", "price": 10000000, "limit": 10, "description": "Chứa tối đa 1,000,000 Coins."}
}

# ================== SETUP BOT ==================
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ADMIN_ID = 1090758840217243688
REPORT_CHANNEL_ID = 1491445396910899290
ID_LOG_NAP_CARD = 1496513685492076704

spam_control = {}

def get_multiplier(user_id, type_buff="coin"):
    uid = str(user_id)
    if uid not in active_buffs:
        return 1
    current_time = time.time()
    max_multi = 1
    for item_id, expire_time in list(active_buffs[uid].items()):
        if expire_time > current_time:
            item_info = SHOP_ITEMS.get(item_id)
            if item_info and item_info.get('type') == type_buff:
                if item_info['multiplier'] > max_multi:
                    max_multi = item_info['multiplier']
        else:
            del active_buffs[uid][item_id]
    return max_multi

async def check_spam(message):
    if message.author.bot:
        return False
    user_id = str(message.author.id)
    current_time = time.time()

    if user_id not in spam_control:
        spam_control[user_id] = {'count': 0, 'last_time': current_time}

    if current_time - spam_control[user_id]['last_time'] < 0.8:
        spam_control[user_id]['count'] += 1
    else:
        spam_control[user_id]['count'] = 0

    spam_control[user_id]['last_time'] = current_time

    if spam_control[user_id]['count'] > 5:
        try:
            await message.channel.send(f"Thằng {message.author.mention}! Cái tay mày bị ma nhập hay gì mà bấm dữ vậy? Biến vô góc nhà mà ngồi sám hối 1 phút cho tao!")
            danh_sach_chui = [
                "Mày có tin tao lấy cái chổi lông gà tao quất mày lòi bản họng hông con?",
                "Server người ta đang yên lành, mày vô mày xả rác như cái nhà mày vậy hả?",
                "Mày nhắn nữa đi, tao trù cho cái cục modem nhà mày nó cháy khét lẹt cho mày khỏi lên mạng luôn!",
                "Cái nết gì mà kì cục kẹo vậy? Spam cho cố vô rồi cũng bị tao xách cổ ra ngoài hà!",
                "Lo mà đi học bài hay phụ mẹ nấu cơm đi, ở đó mà bấm bấm cái máy hoài, tao lẹo cái lưỡi mày bây giờ!"
            ]
            for cau_chui in danh_sach_chui[:3]:
                try:
                    await message.author.send(cau_chui)
                except discord.Forbidden:
                    print(f"Thằng {message.author.name} nó nhát gan, nó khóa DM rồi!")

            duration = datetime.timedelta(minutes=1)
            await message.author.timeout(duration, reason="Spam quá hớp, đã gửi DM cảnh cáo sấp mặt")
            spam_control[user_id]['count'] = 0
            return True
        except discord.Forbidden:
            print("Tao hổng có quyền làm đại ca, coi lại cái Role dùm cái!")
        except Exception as e:
            print(f"Lỗi check_spam: {e}")
        return True
    return False

# --- HÀM XỬ LÝ SỰ KIỆN NHAU (GỘP CHUNG TRÁNH ĐÈ LÊN NHAU) ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Kiểm tra Spam
    if await check_spam(message):
        return

    # 2. Xử lý cộng EXP tự động
    user_id = str(message.author.id)
    if user_id not in levels:
        levels[user_id] = {"xp": 0, "level": 1}

    current_lv = levels[user_id]["level"]
    current_time = time.time()
    multiplier = 1

    if user_id in active_buffs:
        if active_buffs[user_id].get("x16_exp", 0) > current_time:
            multiplier = 16
        elif active_buffs[user_id].get("x8_exp", 0) > current_time:
            multiplier = 8
        elif active_buffs[user_id].get("x4_exp", 0) > current_time:
            multiplier = 4
        elif active_buffs[user_id].get("x2_exp", 0) > current_time:
            multiplier = 2

    bonus_xp = current_lv * 50
    base_xp_gain = random.randint(90, 120) + bonus_xp
    xp_gain = base_xp_gain * multiplier

    levels[user_id]["xp"] += xp_gain

    leveled_up = False
    while levels[user_id]["xp"] >= xp_needed(levels[user_id]["level"]):
        levels[user_id]["xp"] -= xp_needed(levels[user_id]["level"])
        levels[user_id]["level"] += 1
        leveled_up = True

    if leveled_up:
        save_all()
        new_lv = levels[user_id]["level"]
        await message.channel.send(f"🎊 Chúc mừng {message.author.mention} đã đạt **Level {new_lv}**!")
        
        roles_to_add = []
        for lv_milestone, role_id in LEVEL_ROLES.items():
            if new_lv >= lv_milestone:
                role = message.guild.get_role(role_id)
                if role and role not in message.author.roles:
                    roles_to_add.append(role)

        if roles_to_add:
            try:
                await message.author.add_roles(*roles_to_add)
            except Exception as e:
                print(f"❌ Lỗi trao role: {e}")

    save_json(LEVEL_FILE, levels)

    # 3. Tiến hành xử lý Lệnh Bot
    await bot.process_commands(message)

# ================== MODALS & UI COMPONENTS ==================
class HelpModal(discord.ui.Modal, title='Phiếu Hỗ Trợ / Báo Cáo'):
    subject = discord.ui.TextInput(
        label='Vấn đề cần hỗ trợ',
        placeholder='Ví dụ: Lỗi nạp tiền, Tố cáo người chơi...',
        required=True,
        max_length=100
    )
    description = discord.ui.TextInput(
        label='Nội dung chi tiết',
        style=discord.TextStyle.long,
        placeholder='Mô tả rõ vấn đề bạn gặp phải...',
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            report_channel = interaction.client.get_channel(REPORT_CHANNEL_ID)
            if report_channel is None:
                report_channel = await interaction.client.fetch_channel(REPORT_CHANNEL_ID)

            time_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            embed = discord.Embed(title="📩 PHIẾU BÁO CÁO MỚI", color=discord.Color.red())
            embed.add_field(name="👤 Người gửi", value=interaction.user.mention, inline=True)
            embed.add_field(name="⏰ Thời gian", value=f"`{time_str}`", inline=True)
            embed.add_field(name="📌 Tiêu đề", value=f"**{self.subject.value}**", inline=False)
            embed.add_field(name="📝 Nội dung", value=self.description.value, inline=False)
            embed.set_footer(text=f"ID Người gửi: {interaction.user.id}")

            msg = await report_channel.send(content="@everyone", embed=embed)
            ticket_id = f"#{msg.id}"

            await interaction.followup.send(f"✅ Đã gửi báo cáo thành công! Mã phiếu của bạn là: **{ticket_id}**. Admin sẽ xử lý sớm.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi: Bot thiếu quyền hoặc không tìm thấy kênh.", ephemeral=True)

class NapTheView(discord.ui.View):
    def __init__(self, user_id: int, loai_the: str, menh_gia: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.loai_the = loai_the
        self.menh_gia = menh_gia

    @discord.ui.button(label="Chấp nhận (Thành công)", style=discord.ButtonStyle.success, emoji="✅")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.blue()
        embed.add_field(name="📌 Trạng thái", value=f"✅ **Đã duyệt bởi {interaction.user.mention}**", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

        try:
            target_user = await interaction.client.fetch_user(self.user_id)
            if target_user:
                dm_embed = discord.Embed(
                    title="🎉 NẠP THẺ THÀNH CÔNG",
                    description=f"Yêu cầu nạp thẻ **{self.loai_the}** mệnh giá **{self.menh_gia}** của bạn đã được Admin xác nhận thành công!\nKim cương/Quà đã được cộng vào tài khoản.",
                    color=discord.Color.green(),
                )
                await target_user.send(embed=dm_embed)
        except Exception as e:
            print(f"Không thể gửi DM cho user {self.user_id}: {e}")

    @discord.ui.button(label="Thất bại (Sai thông tin)", style=discord.ButtonStyle.danger, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="📌 Trạng thái", value=f"❌ **Từ chối bởi {interaction.user.mention}**", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

        try:
            target_user = await interaction.client.fetch_user(self.user_id)
            if target_user:
                dm_embed = discord.Embed(
                    title="❌ NẠP THẺ THẤT BẠI",
                    description=f"Yêu cầu nạp thẻ **{self.loai_the}** mệnh giá **{self.menh_gia}** bị từ chối.\n**Lý do:** Thẻ lỗi hoặc sai thông tin Seri / Mã thẻ.",
                    color=discord.Color.red(),
                )
                await target_user.send(embed=dm_embed)
        except Exception as e:
            print(f"Không thể gửi DM cho user {self.user_id}: {e}")

class DailyView(discord.ui.View):
    def __init__(self, timeout=60):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Nhận Quà Hôm Nay", style=discord.ButtonStyle.success, emoji="🎁")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = str(interaction.user.id)
        now = datetime.datetime.now()
        day = now.day

        if uid not in daily_data:
            daily_data[uid] = {"last_claim": "", "streak": 0}

        last_claim_str = daily_data[uid]["last_claim"]
        if last_claim_str:
            last_claim = datetime.datetime.fromisoformat(last_claim_str)
            if last_claim.date() == now.date():
                return await interaction.response.send_message("⌛ Bạn đã nhận quà hôm nay rồi!", ephemeral=True)

        coin_reward = min(1000 + (day - 1) * 200, 5000)
        exp_reward = min(100 + (day - 1) * 20, 500)

        user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
        if isinstance(user_econ, int):
            user_econ = {"coins": user_econ, "diamonds": 0}

        user_econ["coins"] += coin_reward
        economy[uid] = user_econ

        if uid not in levels:
            levels[uid] = {"xp": 0, "level": 1}
        levels[uid]["xp"] += exp_reward

        daily_data[uid]["last_claim"] = now.isoformat()
        save_all()

        self.clear_items()
        await interaction.response.edit_message(content=f"✅ **{interaction.user.name}** đã điểm danh ngày {day} thành công!", view=self)
        await interaction.followup.send(
            f"💰 Bạn nhận được: `{coin_reward:,}` coins\n✨ Bạn nhận được: `{exp_reward:,}` EXP\n*Hãy dùng Coins để săn trong `/moqua` nhé!*",
            ephemeral=True
        )

class ConfirmPay(discord.ui.View):
    def __init__(self, s, r, a):
        super().__init__(timeout=60)
        self.s, self.r, self.a = s, r, a

    @discord.ui.button(label="Xác nhận chuyển", style=discord.ButtonStyle.green, emoji="✅")
    async def ok(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.s.id:
            return

        sid, rid = str(self.s.id), str(self.r.id)

        s_data = economy.get(sid, {"coins": 0, "diamonds": 0})
        if isinstance(s_data, int): s_data = {"coins": s_data, "diamonds": 0}

        r_data = economy.get(rid, {"coins": 0, "diamonds": 0})
        if isinstance(r_data, int): r_data = {"coins": r_data, "diamonds": 0}

        if s_data["coins"] < self.a:
            return await interaction.response.edit_message(content="❌ Số dư của bạn không đủ để thực hiện giao dịch!", view=None)

        s_data["coins"] -= self.a
        r_data["coins"] += self.a

        economy[sid] = s_data
        economy[rid] = r_data

        save_all()

        await interaction.response.edit_message(content=f"✅ Chuyển thành công `{self.a:,}` coins cho **{self.r.name}**!", view=None)
        try:
            await self.r.send(f"💰 Bạn nhận được `{self.a:,}` coins từ **{self.s.name}**!")
        except Exception:
            pass
        self.stop()

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.s.id:
            return
        await interaction.response.edit_message(content="❌ Đã hủy giao dịch.", view=None)
        self.stop()

class ConfirmPurchase(discord.ui.View):
    def __init__(self, item_id, qty, price, name):
        super().__init__(timeout=30)
        self.item_id, self.qty, self.price, self.name = item_id, qty, price, name

    @discord.ui.button(label="Xác nhận mua", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = str(interaction.user.id)
        user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
        if isinstance(user_econ, int):
            user_econ = {"coins": user_econ, "diamonds": 0}

        if user_econ["coins"] < self.price:
            return await interaction.response.send_message("❌ Bạn không đủ Coins để thanh toán!", ephemeral=True)

        user_econ["coins"] -= self.price
        economy[uid] = user_econ

        if uid not in inventory:
            inventory[uid] = {}
        inventory[uid][self.item_id] = inventory[uid].get(self.item_id, 0) + self.qty

        save_all()
        await interaction.response.edit_message(content=f"✅ Bạn đã mua thành công **{self.qty}x {self.name}** với giá `{self.price:,}` coins!", view=None)

# ================== 🛡️ NHÓM 1: QUẢN TRỊ & MOD ==================
@bot.tree.command(name="doikc", description="Đổi Kim cương sang Coins (Tỉ lệ: 1 KC = 1,000 Coins)")
@app_commands.describe(amount="Số lượng Kim cương muốn đổi")
async def doikc(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        return await interaction.response.send_message("❌ Số lượng Kim cương phải lớn hơn 0!", ephemeral=True)

    uid = str(interaction.user.id)
    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int):
        user_econ = {"coins": user_econ, "diamonds": 0}

    if user_econ["diamonds"] < amount:
        return await interaction.response.send_message(
            f"❌ Bạn không đủ Kim cương! Hiện có: `{user_econ['diamonds']:,}` 💎", 
            ephemeral=True
        )

    coins_received = amount * 1000
    user_econ["diamonds"] -= amount
    user_econ["coins"] += coins_received

    economy[uid] = user_econ
    save_all()

    embed = discord.Embed(title="🏦 GIAO DỊCH QUY ĐỔI THÀNH CÔNG", color=discord.Color.blue(), timestamp=discord.utils.utcnow())
    embed.add_field(name="📉 Kim cương đã đổi", value=f"- `{amount:,}` 💎", inline=True)
    embed.add_field(name="📈 Coins nhận được", value=f"+ `{coins_received:,}` 💰", inline=True)
    embed.add_field(name="💰 Số dư Coins mới", value=f"`{user_econ['coins']:,}` coins", inline=False)
    embed.set_footer(text=f"ID: {uid}")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="naptien", description="Gửi yêu cầu nạp thẻ cho Admin")
@app_commands.describe(loai_the="Chọn nhà mạng", menh_gia="Chọn mệnh giá thẻ nạp", seri="Số Seri", ma_the="Mã thẻ")
@app_commands.choices(
    loai_the=[
        app_commands.Choice(name="Viettel", value="Viettel"),
        app_commands.Choice(name="Mobifone", value="Mobifone"),
        app_commands.Choice(name="Vinaphone", value="Vinaphone"),
        app_commands.Choice(name="Zing (VNG)", value="Zing"),
        app_commands.Choice(name="Gate", value="Gate"),
        app_commands.Choice(name="Garena", value="Garena"),
    ],
    menh_gia=[
        app_commands.Choice(name="20,000 VND", value="20k"),
        app_commands.Choice(name="50,000 VND", value="50k"),
        app_commands.Choice(name="100,000 VND", value="100k"),
        app_commands.Choice(name="200,000 VND", value="200k"),
        app_commands.Choice(name="500,000 VND", value="500k"),
    ]
)
async def naptien(
    interaction: discord.Interaction,
    loai_the: app_commands.Choice[str],
    menh_gia: app_commands.Choice[str],
    seri: str,
    ma_the: str,
):
    await interaction.response.send_message(
        f"✅ Đã gửi yêu cầu nạp thẻ **{loai_the.name}** mệnh giá **{menh_gia.name}**! Admin sẽ sớm kiểm tra.",
        ephemeral=True,
    )

    log_channel = interaction.guild.get_channel(ID_LOG_NAP_CARD)
    if not log_channel:
        return

    embed = discord.Embed(title="💳 CÓ YÊU CẦU NẠP THẺ MỚI", color=discord.Color.gold(), timestamp=discord.utils.utcnow())
    embed.add_field(name="👤 Người gửi", value=f"{interaction.user.mention}\nID: `{interaction.user.id}`", inline=False)
    embed.add_field(name="📶 Nhà mạng", value=f"**{loai_the.name}**", inline=True)
    embed.add_field(name="💰 Mệnh giá", value=f"**{menh_gia.name}**", inline=True)
    embed.add_field(name="🔢 Số Seri", value=f"`{seri}`", inline=False)
    embed.add_field(name="🔑 Mã thẻ", value=f"||{ma_the}||", inline=False)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    view = NapTheView(user_id=interaction.user.id, loai_the=loai_the.name, menh_gia=menh_gia.name)
    await log_channel.send(content="🔔 **Thông báo từ hệ thống nạp thẻ:**", embed=embed, view=view)

@bot.tree.command(name="add_diamond", description="Nạp kim cương cho người dùng")
@app_commands.choices(goi_nap=[
    app_commands.Choice(name="5k - Gói Khởi Đầu (+100 KC)", value="5k"),
    app_commands.Choice(name="20k (+120 KC)", value="20k"),
    app_commands.Choice(name="50k (+290 KC)", value="50k"),
    app_commands.Choice(name="100k (+570 KC)", value="100k"),
    app_commands.Choice(name="200k (+1280 KC)", value="200k"),
    app_commands.Choice(name="500k (+2830 KC)", value="500k"),
])
@app_commands.checks.has_permissions(administrator=True)
async def add_diamond(interaction: discord.Interaction, user: discord.Member, goi_nap: app_commands.Choice[str]):
    uid = str(user.id)
    so_kc = NAP_PACKAGES[goi_nap.value]["diamonds"]

    if uid not in economy:
        economy[uid] = {"coins": 0, "diamonds": 0}
    if isinstance(economy[uid], int):
        economy[uid] = {"coins": economy[uid], "diamonds": 0}

    economy[uid]["diamonds"] += so_kc
    save_all()

    await interaction.response.send_message(f"✅ Đã nạp thành công **{so_kc} 💎** cho {user.mention}!")

@bot.tree.command(name="diamond", description="Xem số dư kim cương và tiền của bạn")
async def diamond(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    uid = str(target.id)

    if uid not in economy:
        return await interaction.response.send_message(f"👤 {target.display_name} chưa có tài khoản kinh tế!")

    data = economy[uid]
    if isinstance(data, int):
        coins = data
        diamonds = 0
    else:
        coins = data.get("coins", 0)
        diamonds = data.get("diamonds", 0)

    embed = discord.Embed(title=f"💰 TÀI KHOẢN CỦA {target.display_name.upper()}", color=discord.Color.blue())
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="💵 Tiền xu (Coins)", value=f"`{coins:,}` 💰", inline=False)
    embed.add_field(name="💎 Kim cương", value=f"`{diamonds:,}` 💎", inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="moqua", description="Mở hộp quà may mắn (Free 1 lần/ngày hoặc 500k Coins)")
async def moqua(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    current_time = time.time()
    price = 500000

    if uid not in economy:
        economy[uid] = {"coins": 0, "diamonds": 0}
    if isinstance(economy[uid], int):
        economy[uid] = {"coins": economy[uid], "diamonds": 0}

    last_free = gift_cooldowns.get(uid, 0)
    can_free = (current_time - last_free) >= 86400
    is_using_free = False

    if can_free:
        is_using_free = True
    else:
        if economy[uid]["coins"] < price:
            time_left = 86400 - (current_time - last_free)
            h = int(time_left // 3600)
            m = int((time_left % 3600) // 60)
            return await interaction.response.send_message(
                f"❌ Bạn không đủ {price:,} coins và cũng hết lượt FREE!\n⏰ Lượt FREE tiếp theo sau: **{h} giờ {m} phút**.",
                ephemeral=True
            )
        economy[uid]["coins"] -= price

    await interaction.response.send_message(f"🎁 {interaction.user.mention} đang hồi hộp mở hộp quà may mắn...")
    await asyncio.sleep(3)

    weights = [g["weight"] for g in LUCKY_GIFTS]
    reward = random.choices(LUCKY_GIFTS, weights=weights, k=1)[0]

    if reward["type"] == "coin":
        economy[uid]["coins"] += reward["value"]
        result_text = f"💰 **{reward['value']:,} Coins**"
        color = 0xf1c40f
    else:
        economy[uid]["diamonds"] += reward["value"]
        result_text = f"💎 **{reward['value']} Kim Cương**"
        color = 0x00ffff

    if is_using_free:
        gift_cooldowns[uid] = current_time

    save_all()

    embed = discord.Embed(title="🎁 KẾT QUẢ MỞ HỘP QUÀ 🎁", color=color)
    msg_type = "✨ LƯỢT CHƠI MIỄN PHÍ ✨" if is_using_free else f"💸 Chi phí: {price:,} Coins"
    embed.add_field(name="Loại lượt chơi", value=msg_type, inline=False)
    embed.add_field(name="Phần thưởng", value=f"🎉 Bạn nhận được: {result_text} 🎉", inline=False)

    await interaction.edit_original_response(content=None, embed=embed)

@bot.tree.command(name="addexp", description="Thêm kinh nghiệm (EXP) cho người dùng (Admin Only)")
@app_commands.describe(member="Người muốn tặng EXP", amount="Số lượng EXP muốn thêm")
async def addexp(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền Admin để dùng lệnh này!", ephemeral=True)

    if amount <= 0:
        return await interaction.response.send_message("❌ Số lượng EXP phải lớn hơn 0!", ephemeral=True)

    uid = str(member.id)
    if uid not in levels:
        levels[uid] = {"xp": 0, "level": 1}

    levels[uid]["xp"] += amount
    leveled_up = False
    while levels[uid]["xp"] >= xp_needed(levels[uid]["level"]):
        levels[uid]["xp"] -= xp_needed(levels[uid]["level"])
        levels[uid]["level"] += 1
        leveled_up = True

    new_lv = levels[uid]["level"]
    save_json(LEVEL_FILE, levels)

    embed = discord.Embed(
        title="✨ CẤP PHÁT KINH NGHIỆM",
        description=f"Admin đã thêm **{amount:,} EXP** cho {member.mention}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Cấp độ hiện tại", value=f"Level `{new_lv}`", inline=True)
    embed.add_field(name="Tiến trình", value=f"`{levels[uid]['xp']}/{xp_needed(new_lv)}` XP", inline=True)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="giveaway_random", description="Tặng quà cho một người ngẫu nhiên (Admin Only)")
@app_commands.describe(coin="Số tiền muốn tặng", exp="Số EXP muốn tặng")
async def giveaway_random(interaction: discord.Interaction, coin: int = 0, exp: int = 0):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền Admin!", ephemeral=True)

    if coin <= 0 and exp <= 0:
        return await interaction.response.send_message("❌ Bạn phải nhập số tiền hoặc EXP lớn hơn 0!", ephemeral=True)

    members = [m for m in interaction.guild.members if not m.bot]
    if not members:
        return await interaction.response.send_message("Không tìm thấy thành viên hợp lệ.")

    winner = random.choice(members)
    uid = str(winner.id)

    if coin > 0:
        user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
        if isinstance(user_econ, int):
            user_econ = {"coins": user_econ, "diamonds": 0}
        user_econ["coins"] += coin
        economy[uid] = user_econ

    if exp > 0:
        if uid not in levels:
            levels[uid] = {"xp": 0, "level": 1}
        levels[uid]["xp"] += exp

    save_all()

    embed = discord.Embed(
        title="🎁 GIVEAWAY NGẪU NHIÊN",
        description=f"Chúc mừng bạn may mắn đã nhận được quà từ Admin!",
        color=discord.Color.random(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="👤 Người thắng cuộc", value=winner.mention, inline=False)
    if coin > 0: embed.add_field(name="💰 Tiền thưởng", value=f"`{coin:,}` coins", inline=True)
    if exp > 0: embed.add_field(name="✨ EXP thưởng", value=f"`{exp:,}` exp", inline=True)

    await interaction.response.send_message(content=f"🎉 Chúc mừng {winner.mention}!", embed=embed)

@bot.tree.command(name="giveaway_target", description="Tặng quà cho một người cụ thể (Admin Only)")
@app_commands.describe(target="Người nhận quà", coin="Số tiền muốn tặng", exp="Số EXP muốn tặng")
async def giveaway_target(interaction: discord.Interaction, target: discord.Member, coin: int = 0, exp: int = 0):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền Admin!", ephemeral=True)

    if target.bot:
        return await interaction.response.send_message("❌ Bạn không thể tặng quà cho Bot!", ephemeral=True)

    if coin <= 0 and exp <= 0:
        return await interaction.response.send_message("❌ Vui lòng nhập số lượng Tiền hoặc EXP!", ephemeral=True)

    uid = str(target.id)

    if coin > 0:
        user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
        if isinstance(user_econ, int):
            user_econ = {"coins": user_econ, "diamonds": 0}
        user_econ["coins"] += coin
        economy[uid] = user_econ

    if exp > 0:
        if uid not in levels:
            levels[uid] = {"xp": 0, "level": 1}
        levels[uid]["xp"] += exp

    save_all()

    embed = discord.Embed(title="🎁 QUÀ TẶNG TỪ ADMIN", description=f"{target.mention} vừa nhận được quà đặc biệt!", color=0xFFD700)
    if coin > 0: embed.add_field(name="💰 Tiền nhận được", value=f"`{coin:,}` coins", inline=True)
    if exp > 0: embed.add_field(name="✨ EXP nhận được", value=f"`{exp:,}` exp", inline=True)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="addmoney", description="Thêm tiền cho người dùng (Admin Only)")
@app_commands.describe(amount="Số tiền muốn cộng", member="Người nhận")
@app_commands.checks.has_permissions(administrator=True)
async def addmoney(interaction: discord.Interaction, amount: int, member: discord.Member = None):
    target = member or interaction.user
    uid = str(target.id)

    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int):
        user_econ = {"coins": user_econ, "diamonds": 0}

    user_econ["coins"] += amount
    economy[uid] = user_econ
    save_all()

    embed = discord.Embed(title="💰 THÔNG BÁO CỘNG TIỀN", color=discord.Color.green())
    embed.add_field(name="👤 Người nhận", value=target.mention, inline=True)
    embed.add_field(name="💵 Số tiền", value=f"`+{amount:,}` coins", inline=True)
    embed.add_field(name="💳 Số dư mới", value=f"`{user_econ['coins']:,}` coins", inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ban", description="Ban người dùng và lưu dữ liệu đồng bộ")
@app_commands.describe(member="Người cần ban", thoi_han="Số lượng thời gian", don_vi="Đơn vị thời gian", ly_do="Lý do xử phạt")
@app_commands.choices(don_vi=[
    app_commands.Choice(name="Phút", value="minutes"),
    app_commands.Choice(name="Giờ", value="hours"),
    app_commands.Choice(name="Ngày", value="days"),
    app_commands.Choice(name="Vĩnh viễn", value="permanent")
])
async def ban(
    interaction: discord.Interaction, 
    member: discord.Member, 
    thoi_han: int, 
    don_vi: app_commands.Choice[str], 
    ly_do: str = "Không có lý do cụ thể"
):
    global ban_data
    await interaction.response.defer()

    if not interaction.user.guild_permissions.ban_members:
        return await interaction.followup.send("❌ Bạn không có quyền Ban người dùng!", ephemeral=True)

    if member.top_role >= interaction.user.top_role:
        return await interaction.followup.send("❌ Không thể ban người có vai trò cao hơn hoặc bằng mình!", ephemeral=True)

    guild = interaction.guild
    seconds = 0
    thoi_han_str = f"{thoi_han} {don_vi.name}"

    if don_vi.value != "permanent":
        if don_vi.value == "minutes": seconds = thoi_han * 60
        elif don_vi.value == "hours": seconds = thoi_han * 3600
        elif don_vi.value == "days": seconds = thoi_han * 86400

    invite_link = "Liên hệ Admin"
    if don_vi.value != "permanent":
        try:
            invite = await interaction.channel.create_invite(max_uses=1, unique=True)
            invite_link = invite.url
        except Exception:
            pass

    try:
        embed = discord.Embed(title="🚫 THÔNG BÁO BAN", color=discord.Color.red())
        embed.add_field(name="**Server**", value=guild.name, inline=False)
        embed.add_field(name="**Lý do**", value=ly_do, inline=False)
        embed.add_field(name="**Thời hạn**", value=thoi_han_str if don_vi.value != "permanent" else "Vĩnh viễn", inline=False)

        if don_vi.value != "permanent":
            embed.set_footer(text="Ghi chú: Sau khi hết hạn, bạn có thể dùng link dưới để vào lại.")
            await member.send(embed=embed)
            await member.send(f"🔗 **Link vào lại server:** {invite_link}")
        else:
            await member.send(embed=embed)
    except Exception:
        print(f"Không thể gửi DM cho {member.name}")

    try:
        await member.ban(reason=ly_do, delete_message_days=0)
        if don_vi.value != "permanent":
            ban_data[str(member.id)] = {
                "user_name": member.name,
                "guild_id": guild.id,
                "unban_at": time.time() + seconds
            }
            save_all()

        await interaction.followup.send(f"🚨 Đã đuổi **{member.name}** khỏi server. Thời hạn: `{thoi_han_str if don_vi.value != 'permanent' else 'Vĩnh viễn'}`")
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi thực hiện: {e}", ephemeral=True)

@bot.tree.command(name="unban", description="Gỡ cấm ngay lập tức và cập nhật dữ liệu")
@app_commands.describe(user_id="ID Discord của người cần gỡ ban")
async def unban(interaction: discord.Interaction, user_id: str):
    global ban_data
    await interaction.response.defer()

    if not interaction.user.guild_permissions.ban_members:
        return await interaction.followup.send("❌ Bạn không có quyền gỡ cấm!", ephemeral=True)

    guild = interaction.guild
    try:
        uid = int(user_id)
        user = await bot.fetch_user(uid)
        await guild.unban(user, reason=f"Gỡ ban bởi {interaction.user.name}")

        uid_str = str(uid)
        if uid_str in ban_data:
            del ban_data[uid_str]
            save_all()
            status = "Đã xóa khỏi danh sách hẹn giờ."
        else:
            status = "Người này không có trong danh sách hẹn giờ."

        await interaction.followup.send(f"✅ Đã gỡ cấm thành công cho **{user.name}**. {status}")
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi: {e}", ephemeral=True)

@bot.tree.command(name="duoi", description="Kick người dùng")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member):
    await member.kick()
    await interaction.response.send_message(f"👢 Đã kick {member.name}")

@bot.tree.command(name="mute", description="Cấm chat người dùng (phút)")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):
    await member.timeout(timedelta(minutes=minutes))
    await interaction.response.send_message(f"🔇 Đã mute {member.mention} trong {minutes} phút.")

@bot.tree.command(name="unmute")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"🔊 Đã gỡ mute cho {member.mention}")

@bot.tree.command(name="setlevel", description="Đặt cấp độ cho người dùng (Admin)")
async def setlevel(interaction: discord.Interaction, level: int, member: discord.Member = None):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền Admin!", ephemeral=True)

    target = member or interaction.user
    uid = str(target.id)

    levels.setdefault(uid, {"xp": 0, "level": 1})
    levels[uid]["level"] = level
    levels[uid]["xp"] = 0

    save_json(LEVEL_FILE, levels)

    if level in LEVEL_ROLES:
        role = interaction.guild.get_role(LEVEL_ROLES[level])
        if role:
            try:
                await target.add_roles(role)
            except Exception:
                pass

    await interaction.response.send_message(f"✅ Đã đặt cấp độ của {target.mention} thành **Level {level}**.")

@bot.tree.command(name="setmoney", description="Đặt số tiền cho người dùng (Chỉ dành cho Admin)")
@app_commands.describe(amount="Số tiền muốn đặt", member="Người dùng cần đặt lại tiền")
async def setmoney(interaction: discord.Interaction, amount: int, member: discord.Member = None):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền Admin!", ephemeral=True)

    target = member or interaction.user
    uid = str(target.id)

    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int):
        user_econ = {"coins": user_econ, "diamonds": 0}

    user_econ["coins"] = amount
    economy[uid] = user_econ
    save_all()

    embed = discord.Embed(title="🔧 ĐẶT LẠI SỐ DƯ", color=discord.Color.orange())
    embed.add_field(name="💰 Tiền xu mới", value=f"`{amount:,}` coins", inline=True)
    embed.add_field(name="💎 Kim cương", value=f"`{user_econ['diamonds']:,}` diamonds", inline=True)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setdiamond", description="Đặt lại số lượng kim cương cho người dùng (Admin Only)")
@app_commands.describe(amount="Số kim cương muốn đặt", member="Người dùng cần đặt lại")
@app_commands.checks.has_permissions(administrator=True)
async def setdiamond(interaction: discord.Interaction, amount: int, member: discord.Member = None):
    target = member or interaction.user
    uid = str(target.id)

    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int):
        user_econ = {"coins": user_econ, "diamonds": 0}

    user_econ["diamonds"] = amount
    economy[uid] = user_econ
    save_all()

    await interaction.response.send_message(f"💎 Đã thiết lập số dư Kim cương của {target.mention} thành `{amount:,}` 💎")

@bot.tree.command(name="addkimcuong", description="Cộng thêm kim cương cho người dùng (Admin Only)")
@app_commands.describe(amount="Số kim cương muốn cộng thêm", member="Người dùng nhận kim cương")
@app_commands.checks.has_permissions(administrator=True)
async def addkimcuong(interaction: discord.Interaction, amount: int, member: discord.Member = None):
    target = member or interaction.user
    uid = str(target.id)

    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int):
        user_econ = {"coins": user_econ, "diamonds": 0}

    user_econ["diamonds"] += amount
    economy[uid] = user_econ
    save_all()

    await interaction.response.send_message(f"💎 Đã cộng thêm `{amount:,}` Kim cương cho {target.mention}!")

@bot.tree.command(name="reset", description="Reset dữ liệu (Tiền, Level) cho 1 người hoặc tất cả")
@app_commands.describe(scope="Chọn phạm vi: Cá nhân hoặc Tất cả", member="Chọn người cần reset")
@app_commands.choices(scope=[
    app_commands.Choice(name="Cá nhân (Chỉ 1 người)", value="individual"),
    app_commands.Choice(name="Tất cả (Toàn bộ Server)", value="all")
])
async def reset(interaction: discord.Interaction, scope: app_commands.Choice[str], member: discord.Member = None):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền Admin!", ephemeral=True)

    if scope.value == "individual":
        if not member:
            return await interaction.response.send_message("❌ Bạn chưa chọn người cần reset!", ephemeral=True)

        uid = str(member.id)
        levels[uid] = {"xp": 0, "level": 1}
        economy[uid] = {"coins": 0, "diamonds": 0}

        save_all()
        await interaction.response.send_message(f"✅ Đã reset toàn bộ dữ liệu của {member.mention} về mặc định.")

    elif scope.value == "all":
        view = discord.ui.View()
        confirm_btn = discord.ui.Button(label="XÁC NHẬN RESET TẤT CẢ", style=discord.ButtonStyle.danger)

        async def confirm_callback(itn: discord.Interaction):
            levels.clear()
            economy.clear()
            save_all()
            await itn.response.edit_message(content="🚨 **ĐÃ RESET TOÀN BỘ DỮ LIỆU SERVER!**", view=None)

        confirm_btn.callback = confirm_callback
        view.add_item(confirm_btn)
        await interaction.response.send_message("⚠️ **CẢNH BÁO:** Bạn có chắc chắn muốn xóa sạch dữ liệu của **TẤT CẢ** mọi người?", view=view)

@bot.tree.command(name="lock", description="Khóa kênh hiện tại")
@app_commands.describe(ly_do="Lý do khóa kênh")
async def lock(interaction: discord.Interaction, ly_do: str = "Bảo trì hoặc ổn định trật tự"):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ Bạn không có quyền quản lý kênh!", ephemeral=True)

    channel = interaction.channel
    overwrite = channel.overwrites_for(interaction.guild.default_role)

    if overwrite.send_messages == False:
        return await interaction.response.send_message("🔒 Kênh này đã bị khóa từ trước rồi!", ephemeral=True)

    overwrite.send_messages = False
    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

    embed = discord.Embed(title="🔒 KÊNH ĐÃ BỊ KHÓA", description=f"**Lý do:** {ly_do}", color=discord.Color.red())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unlock", description="Mở khóa kênh hiện tại")
async def unlock(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ Bạn không có quyền quản lý kênh!", ephemeral=True)

    channel = interaction.channel
    overwrite = channel.overwrites_for(interaction.guild.default_role)

    overwrite.send_messages = None
    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

    embed = discord.Embed(title="🔓 KÊNH ĐÃ ĐƯỢC MỞ KHÓA", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Gửi yêu cầu hỗ trợ trực tiếp cho Admin")
@app_commands.describe(tieude="Tiêu đề ngắn gọn", noidung="Mô tả chi tiết vấn đề")
async def help_command(interaction: discord.Interaction, tieude: str, noidung: str):
    await interaction.response.defer(ephemeral=True)
    try:
        channel = bot.get_channel(REPORT_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(REPORT_CHANNEL_ID)

        time_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        embed = discord.Embed(title="📩 PHIẾU HỖ TRỢ MỚI", color=discord.Color.red())
        embed.add_field(name="👤 Người gửi", value=interaction.user.mention, inline=True)
        embed.add_field(name="⏰ Thời gian", value=f"`{time_now}`", inline=True)
        embed.add_field(name="📌 Tiêu đề", value=f"**{tieude}**", inline=False)
        embed.add_field(name="📝 Nội dung", value=noidung, inline=False)

        msg = await channel.send(content="@everyone", embed=embed)
        ticket_id = f"#{msg.id}"

        await interaction.followup.send(f"✅ Báo cáo đã được gửi! Mã phiếu: **{ticket_id}**.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Có lỗi xảy ra: {e}", ephemeral=True)

@bot.tree.command(name="addrole", description="Thêm một Role cụ thể cho thành viên")
@app_commands.describe(member="Người cần nhận Role", role="Role muốn thêm")
async def addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Bạn không có quyền Quản lý vai trò!", ephemeral=True)

    if role >= interaction.guild.me.top_role:
        return await interaction.response.send_message("❌ Bot không thể thêm Role này vì nó cao hơn vai trò của Bot!", ephemeral=True)

    if role in member.roles:
        return await interaction.response.send_message(f"⚠️ Người dùng {member.mention} đã có vai trò này rồi.", ephemeral=True)

    try:
        await member.add_roles(role)
        embed = discord.Embed(title="✅ CẤP VAI TRÒ THÀNH CÔNG", description=f"Đã thêm {role.mention} cho {member.mention}", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)

@bot.tree.command(name="removerole", description="Gỡ một Role khỏi thành viên")
@app_commands.describe(member="Người cần gỡ Role", role="Role muốn gỡ")
async def removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Bạn không có quyền gỡ vai trò!", ephemeral=True)

    if role not in member.roles:
        return await interaction.response.send_message(f"⚠️ Người dùng {member.mention} vốn không có vai trò này.", ephemeral=True)

    try:
        await member.remove_roles(role)
        await interaction.response.send_message(f"✅ Đã gỡ vai trò {role.mention} khỏi {member.mention}.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)

@bot.tree.command(name="giftcode", description="Nhập mã quà tặng để nhận thưởng")
@app_commands.describe(code="Nhập mã code của bạn")
async def use_giftcode(interaction: discord.Interaction, code: str):
    uid = str(interaction.user.id)
    now = datetime.datetime.now()

    if code not in giftcodes:
        return await interaction.response.send_message("❌ Mã code này không tồn tại!", ephemeral=True)

    data = giftcodes[code]
    expiry_date = datetime.datetime.strptime(data["expiry"], "%d/%m/%Y %H:%M")
    if now > expiry_date:
        return await interaction.response.send_message("⏰ Mã code này đã hết hạn sử dụng!", ephemeral=True)

    if data["max_uses"] != -1 and data["current_uses"] >= data["max_uses"]:
        return await interaction.response.send_message("📉 Mã code này đã đạt giới hạn lượt nhập!", ephemeral=True)

    if uid in data["users_claimed"]:
        return await interaction.response.send_message("⚠️ Bạn đã nhận quà từ mã code này rồi!", ephemeral=True)

    reward_coin = data["rewards"].get("coins", 0)
    reward_exp = data["rewards"].get("exp", 0)
    reward_diamond = data["rewards"].get("diamonds", 0)

    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int):
        user_econ = {"coins": user_econ, "diamonds": 0}

    user_econ["coins"] += reward_coin
    user_econ["diamonds"] += reward_diamond
    economy[uid] = user_econ

    if uid not in levels:
        levels[uid] = {"xp": 0, "level": 1}
    levels[uid]["xp"] += reward_exp

    data["current_uses"] += 1
    data["users_claimed"].append(uid)

    save_all()

    embed = discord.Embed(title="🎁 NHẬN QUÀ THÀNH CÔNG", color=discord.Color.green())
    embed.description = f"Chúc mừng {interaction.user.mention} đã nhập thành công mã `{code}`"
    if reward_coin > 0: embed.add_field(name="💰 Tiền mặt", value=f"`{reward_coin:,}` coins", inline=True)
    if reward_diamond > 0: embed.add_field(name="💎 Kim cương", value=f"`{reward_diamond:,}` KC", inline=True)
    if reward_exp > 0: embed.add_field(name="✨ Kinh nghiệm", value=f"`{reward_exp:,}` EXP", inline=True)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="createcode", description="Tạo mã Giftcode mới (Admin Only)")
@app_commands.describe(
    code="Tên mã", 
    coins="Số tiền thưởng", 
    diamonds="Số Kim cương thưởng",
    exp="Số EXP thưởng", 
    max_uses="Số lượt nhập (-1 = vô hạn)",
    expiry="Hạn dùng (Ví dụ: 30/12/2026 23:59)"
)
async def create_code(interaction: discord.Interaction, code: str, coins: int = 0, diamonds: int = 0, exp: int = 0, max_uses: int = -1, expiry: str = "31/12/2099 23:59"):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền tạo code!", ephemeral=True)

    try:
        datetime.datetime.strptime(expiry, "%d/%m/%Y %H:%M")
        giftcodes[code] = {
            "rewards": {"coins": coins, "diamonds": diamonds, "exp": exp},
            "max_uses": max_uses,
            "current_uses": 0,
            "expiry": expiry,
            "users_claimed": []
        }
        save_json(GIFTCODE_FILE, giftcodes)

        embed = discord.Embed(title="✅ ĐÃ TẠO GIFTCODE", color=discord.Color.blue())
        embed.add_field(name="🎫 Mã", value=f"`{code}`")
        embed.add_field(name="⏰ Hạn dùng", value=f"`{expiry}`")
        embed.add_field(name="🎟️ Giới hạn", value=f"{max_uses if max_uses != -1 else 'Vô hạn'} lượt")

        await interaction.response.send_message(embed=embed)
    except ValueError:
        await interaction.response.send_message("❌ Sai định dạng thời gian! Kiểu mẫu: `Ngày/Tháng/Năm Giờ:Phút`", ephemeral=True)

@bot.tree.command(name="checkbots", description="Kiểm tra trạng thái hoạt động của tất cả Bot trong server")
async def checkbots(interaction: discord.Interaction):
    bot_list = []
    for member in interaction.guild.members:
        if member.bot:
            if member.status == discord.Status.online:
                status_icon = "🟢 **Online**"
            elif member.status == discord.Status.idle:
                status_icon = "🌙 **Chờ**"
            elif member.status == discord.Status.dnd:
                status_icon = "⛔ **Đừng làm phiền**"
            else:
                status_icon = "🔴 **Offline**"

            bot_list.append(f"🤖 {member.mention} - {status_icon}")

    embed = discord.Embed(
        title=f"📊 Trạng thái Bot tại {interaction.guild.name}",
        description="\n".join(bot_list) if bot_list else "Không tìm thấy Bot nào khác.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

# ================== 💰 NHÓM 2: KINH TẾ & MEMBER ==================
BOT_VERSION = "2.6.1"
UPDATE_LOG = """
**Phiên bản 2.8.5**
** Sự kiện tổng kết và sự kiện thanh xuân **
**Fix các lỗi hệ thống & Đồng bộ hóa toàn bộ CSDL**
|| Sử dụng lệnh `/help` để nhận được sự hỗ trợ từ phía admin ||
"""

@bot.tree.command(name="updlog", description="Xem nhật ký cập nhật của Bot.")
async def uptlog(interaction: discord.Interaction):
    embed = discord.Embed(title=f"🆙 Cập nhật Bot - v{BOT_VERSION}", description=UPDATE_LOG, color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="xoa", description="Xóa số lượng tin nhắn nhất định trong kênh")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    if amount < 1:
        return await interaction.response.send_message("❌ Số lượng tin nhắn xóa phải ít nhất là 1!", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ Đã xóa thành công **{len(deleted)}** tin nhắn!")

@bot.tree.command(name="clear_user", description="Xóa tin nhắn của một người cụ thể trong kênh này")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_user(interaction: discord.Interaction, user: discord.Member, amount: int):
    if amount < 1:
        return await interaction.response.send_message("❌ Số lượng tin nhắn xóa phải ít nhất là 1!", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    def is_user(m):
        return m.author.id == user.id

    deleted = await interaction.channel.purge(limit=amount, check=is_user)
    await interaction.followup.send(f"✅ Đã dọn dẹp **{len(deleted)}** tin nhắn của {user.mention}!")

@bot.tree.command(name="daily", description="Mở bảng điểm danh nhận quà hàng ngày")
async def daily(interaction: discord.Interaction):
    now = datetime.datetime.now()
    year, month, today = now.year, now.month, now.day

    cal = calendar.monthcalendar(year, month)
    month_name = f"Tháng {month} / {year}"

    calendar_text = "```\nThứ 2  Thứ 3  Thứ 4  Thứ 5  Thứ 6  Thứ 7  CN\n"
    for week in cal:
        week_str = ""
        for day in week:
            if day == 0:
                week_str += "    "
            elif day == today:
                week_str += f" [{day:2}]"
            else:
                week_str += f"  {day:2} "
        calendar_text += week_str + "\n"
    calendar_text += "```"

    embed = discord.Embed(
        title=f"📅 BẢNG ĐIỂM DANH - {month_name}",
        description=f"Hôm nay là ngày **{today}**\n\n{calendar_text}\nNhấn nút dưới đây để nhận phần thưởng của ngày hôm nay!",
        color=discord.Color.blue()
    )
    embed.add_field(name="🎁 Phần thưởng tối đa", value="• 💰 **5,000** Coins\n• ✨ **500** EXP", inline=False)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    view = DailyView()
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="chuyentien", description="Chuyển tiền ví cho người khác")
async def chuyentien(interaction: discord.Interaction, user: discord.Member, amount: int):
    if user.id == interaction.user.id or amount <= 0:
        return await interaction.response.send_message("❌ Lỗi: Người nhận hoặc số tiền không hợp lệ!", ephemeral=True)

    if user.bot:
        return await interaction.response.send_message("❌ Không thể chuyển tiền cho Bot!", ephemeral=True)

    uid_s = str(interaction.user.id)
    s_data = economy.get(uid_s, {"coins": 0, "diamonds": 0})
    if isinstance(s_data, int): s_data = {"coins": s_data, "diamonds": 0}

    if s_data["coins"] < amount:
        return await interaction.response.send_message(f"❌ Bạn không đủ tiền! Ví hiện tại: `{s_data['coins']:,}` coins", ephemeral=True)

    view = ConfirmPay(interaction.user, user, amount)
    try:
        await interaction.user.send(f"🔔 Bạn có chắc chắn muốn chuyển `{amount:,}` coins cho **{user.name}** không?", view=view)
        await interaction.response.send_message("📩 Một yêu cầu xác nhận đã được gửi vào DM của bạn!", ephemeral=True)
    except Exception:
        await interaction.response.send_message("❌ Lỗi: Bạn cần mở DM để Bot có thể gửi nút xác nhận!", ephemeral=True)

@bot.tree.command(name="rank", description="Xem bảng xếp hạng những người giàu nhất server")
async def rank(interaction: discord.Interaction):
    processed_list = []
    for uid, data in economy.items():
        if isinstance(data, int):
            coins, diamonds = data, 0
        else:
            coins = data.get("coins", 0)
            diamonds = data.get("diamonds", 0)

        processed_list.append({"uid": uid, "coins": coins, "diamonds": diamonds})

    sorted_econ = sorted(processed_list, key=lambda x: x["coins"], reverse=True)
    top_10 = sorted_econ[:10]

    embed = discord.Embed(title="🏆 BẢNG XẾP HẠNG ĐẠI GIA SERVER", color=0xffd700, timestamp=discord.utils.utcnow())
    leaderboard_text = ""

    for i, user_info in enumerate(top_10, start=1):
        uid = user_info["uid"]
        money = user_info["coins"]
        dias = user_info["diamonds"]

        member = interaction.guild.get_member(int(uid))
        name = member.name if member else f"Người dùng cũ ({uid})"

        top_role = "Không có"
        if member:
            roles = [r for r in member.roles if r != interaction.guild.default_role]
            if roles:
                top_role = member.top_role.mention

        user_lv_data = levels.get(uid, {"level": 1, "xp": 0})
        lv = user_lv_data.get("level", 1)

        medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else "👤"))
        leaderboard_text += f"{medal} **Top {i}: {name}**\n> 💰 Coins: `{money:,}` | 💎 `{dias:,}` KC\n> ⭐ Level: `{lv}` | 🎭 {top_role}\n\n"

    embed.description = leaderboard_text or "Chưa có dữ liệu xếp hạng."
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="info", description="Xem thông tin chi tiết của bản thân hoặc người khác")
@app_commands.describe(member="Chọn người cần xem thông tin")
async def info(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    uid = str(target.id)

    user_lvl = levels.get(uid, {"level": 1, "xp": 0})
    lvl = user_lvl.get("level", 1)
    xp = user_lvl.get("xp", 0)
    needed = xp_needed(lvl)

    user_econ_data = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ_data, int):
        coins, diamonds = user_econ_data, 0
    else:
        coins = user_econ_data.get("coins", 0)
        diamonds = user_econ_data.get("diamonds", 0)

    roles = [role.mention for role in target.roles if role != interaction.guild.default_role]
    roles_str = " ".join(roles) if roles else "Không có"

    embed = discord.Embed(title=f"👤 Thông tin người dùng: {target.name}", color=target.color, timestamp=discord.utils.utcnow())
    embed.set_thumbnail(url=target.display_avatar.url)

    embed.add_field(name="💰 Tài chính", value=f"`{coins:,}` coins", inline=True)
    embed.add_field(name="💎 Kim cương", value=f"`{diamonds:,}` diamonds", inline=True)
    embed.add_field(name="⭐ Cấp độ", value=f"Level `{lvl}`", inline=True)
    embed.add_field(name="✨ Kinh nghiệm", value=f"`{xp:,}/{needed:,}` XP", inline=True)
    embed.add_field(name=f"🎭 Vai trò ({len(roles)})", value=roles_str, inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="money", description="Xem số tiền")
async def money(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    bal = economy.get(uid, 0)
    if isinstance(bal, dict):
        bal = bal.get("coins", 0)
    await interaction.response.send_message(f"💰 Bạn có: `{bal:,}` coins.")

@bot.tree.command(name="level", description="Xem cấp độ")
async def level_cmd(interaction: discord.Interaction):
    data = levels.get(str(interaction.user.id), {"xp": 0, "level": 1})
    await interaction.response.send_message(f"⭐ Cấp: {data['level']} | XP: {data['xp']}/{xp_needed(data['level'])}")

@bot.tree.command(name="doiexp", description="Dùng tiền để mua cấp độ")
@app_commands.describe(levels_count="Số cấp độ muốn mua")
async def doiexp(interaction: discord.Interaction, levels_count: int):
    uid = str(interaction.user.id)
    cost_per_level = 5000
    total_cost = levels_count * cost_per_level

    if levels_count <= 0:
        return await interaction.response.send_message("Số cấp độ phải lớn hơn 0!", ephemeral=True)

    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int):
        user_econ = {"coins": user_econ, "diamonds": 0}

    if user_econ["coins"] < total_cost:
        return await interaction.response.send_message(f"Bạn không đủ tiền! Cần `{total_cost:,}` coins.", ephemeral=True)

    if uid not in levels:
        levels[uid] = {"xp": 0, "level": 1}

    user_econ["coins"] -= total_cost
    economy[uid] = user_econ
    levels[uid]["level"] += levels_count

    save_all()
    await interaction.response.send_message(f"✅ Thành công! Bạn đã chi `{total_cost:,}` coins để lên thẳng cấp **{levels[uid]['level']}**.")

# ================== 🎲 NHÓM 3: TRÒ CHƠI ==================
@bot.tree.command(name="taixiu", description="Cá cược Tài Xỉu (Thuế 10%)")
@app_commands.choices(lua_chon=[
    app_commands.Choice(name="Tài", value="tài"),
    app_commands.Choice(name="Xỉu", value="xỉu"),
])
async def taixiu(interaction: discord.Interaction, lua_chon: app_commands.Choice[str], tien_cuoc: int):
    uid = str(interaction.user.id)
    val = lua_chon.value

    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int): user_econ = {"coins": user_econ, "diamonds": 0}

    if tien_cuoc <= 0 or user_econ["coins"] < tien_cuoc:
        return await interaction.response.send_message("❌ Tiền cược không hợp lệ hoặc bạn không đủ coins!", ephemeral=True)

    user_econ["coins"] -= tien_cuoc

    dices = [random.randint(1, 6) for _ in range(3)]
    total = sum(dices)
    result = "tài" if total >= 11 else "xỉu"

    if val == result:
        tong_nhan = tien_cuoc + int(tien_cuoc * 0.9)
        user_econ["coins"] += tong_nhan
        msg = f"🎲 Xúc xắc: `{dices[0]}+{dices[1]}+{dices[2]}` = **{total}** ({result.upper()}).\n✅ Bạn thắng nhận `{tong_nhan:,}` coins!"
    else:
        msg = f"🎲 Xúc xắc: `{dices[0]}+{dices[1]}+{dices[2]}` = **{total}** ({result.upper()}).\n❌ Bạn thua mất `{tien_cuoc:,}` coins!"

    economy[uid] = user_econ
    save_all()
    await interaction.response.send_message(msg)

@bot.tree.command(name="chanle", description="Cá cược Chẵn Lẻ (Thuế 10%)")
async def chanle(interaction: discord.Interaction, lua_chon: str, tien_cuoc: int):
    uid = str(interaction.user.id)
    choices = {"chẵn": 0, "chan": 0, "lẻ": 1, "le": 1}
    lc = lua_chon.lower()

    if lc not in choices:
        return await interaction.response.send_message("❌ Vui lòng chọn 'Chẵn' hoặc 'Lẻ'!", ephemeral=True)

    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int): user_econ = {"coins": user_econ, "diamonds": 0}

    if tien_cuoc <= 0 or user_econ["coins"] < tien_cuoc:
        return await interaction.response.send_message("❌ Lỗi tiền cược hoặc bạn không đủ tiền!", ephemeral=True)

    user_econ["coins"] -= tien_cuoc

    num = random.randint(1, 100)
    win = (num % 2 == choices[lc])

    emb = discord.Embed(title="🔢 KẾT QUẢ CHẴN LẺ")
    if win:
        tong_nhan = tien_cuoc + int(tien_cuoc * 0.9)
        user_econ["coins"] += tong_nhan
        emb.description = f"Số ra: **{num}**. Bạn thắng nhận `{tong_nhan:,}` coins!"
        emb.color = 0x2ecc71
    else:
        emb.description = f"Số ra: **{num}**. Bạn đã thua `{tien_cuoc:,}` coins!"
        emb.color = 0xe74c3c

    economy[uid] = user_econ
    save_all()
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="duangua", description="Đua ngựa (Thắng x3 - Thuế 10%)")
async def duangua(interaction: discord.Interaction, con_ngua: int, tien_cuoc: int):
    uid = str(interaction.user.id)

    if con_ngua not in [1, 2, 3, 4] or tien_cuoc <= 0:
        return await interaction.response.send_message("❌ Chọn ngựa từ 1-4 và số tiền hợp lệ!", ephemeral=True)

    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int): user_econ = {"coins": user_econ, "diamonds": 0}

    if user_econ["coins"] < tien_cuoc:
        return await interaction.response.send_message("❌ Bạn không đủ coins!", ephemeral=True)

    user_econ["coins"] -= tien_cuoc

    winner = random.randint(1, 4)
    emb = discord.Embed(title="🏇 KẾT QUẢ ĐUA NGỰA", timestamp=discord.utils.utcnow())

    if con_ngua == winner:
        tong_thang = tien_cuoc * 3
        thue = int(tong_thang * 0.1)
        thuc_nhan = tong_thang - thue
        user_econ["coins"] += thuc_nhan
        emb.description = f"🏆 Ngựa số **{winner}** thắng! Bạn nhận `{thuc_nhan:,}` coins (Đã trừ thuế `{thue:,}`)."
        emb.color = 0x2ecc71
    else:
        emb.description = f"❌ Ngựa số **{winner}** về nhất. Bạn đã mất `{tien_cuoc:,}` coins."
        emb.color = 0xe74c3c

    economy[uid] = user_econ
    save_all()
    await interaction.response.send_message(embed=emb)

# ================== BẮT ĐẦU BOT ==================
@bot.event
async def on_ready():
    print(f"🤖 Bot đã đăng nhập thành công với tên: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"⚡ Đã đồng bộ {len(synced)} lệnh Slash Commands.")
    except Exception as e:
        print(f"❌ Lỗi đồng bộ lệnh: {e}")

# Đặt Token của bot vào đây khi khởi chạy
# bot.run("YOUR_BOT_TOKEN")


import os

# Lấy token từ biến môi trường
TOKEN = os.getenv("DISCORD_TOKEN")

bot.run(TOKEN)