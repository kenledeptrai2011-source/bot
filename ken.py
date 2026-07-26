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
import random
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

# 1. Khai báo tên file trước
CONFIG_FILE = "config.json"
GIFTCODE_FILE = "giftcodes.json"
LEVEL_FILE = "levels.json"
ECON_FILE = "economy.json"
DAILY_FILE = "daily.json"
BUFF_FILE = "buffs.json"
INVETORY_FILE = "inventory.json"
DATA_FILE = "data.json"

# --- Định nghĩa hàm xử lý JSON (PHẢI NẰM TRÊN CÙNG) ---
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {} # Trả về dict trống nếu file hổng có hoặc lỗi

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- BÂY GIỜ MỚI KHỞI TẠO BIẾN ---
ban_data = load_json(DATA_FILE) # Lúc này nó mới biết load_json là gì nè!

def save_all():
    global levels, economy, last_daily, giftcodes, active_buffs
    try:
        save_json(LEVEL_FILE, levels)
        save_json(ECON_FILE, economy)
        save_json(DAILY_FILE, last_daily)
        save_json(GIFTCODE_FILE, giftcodes)
        save_json(BUFF_FILE, active_buffs)
        save_json(INVETORY_FILE, inventory)
        save_json(DATA_FILE, ban_data)
        print("--- [HỆ THỐNG] Đã lưu dữ liệu thành công! ---")
    except Exception as e:
        print(f"--- [LỖI] Không thể lưu dữ liệu: {e} ---")

# 2. Định nghĩa các hàm xử lý JSON (PHẢI NẰM TRÊN)
def load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# 3. Sau đó mới gọi hàm để nạp dữ liệu (PHẢI NẰM DƯỚI)
levels = load_json(LEVEL_FILE)
economy = load_json(ECON_FILE)
giftcodes = load_json(GIFTCODE_FILE)
config = load_json(CONFIG_FILE)
daily_data = load_json("daily.json")
last_daily = load_json(DAILY_FILE)
active_buffs = load_json(BUFF_FILE)

LUCKY_GIFTS = [
    {"name": "5 Kim Cương 💎", "value": 5, "type": "diamond", "weight": 1},      # 1% (Hiếm nhất)
    
    # Tiền Coins (Tổng 99%)
    {"name": "10,000,000 Coins", "value": 100000000, "type": "coin", "weight": 0.5}, # 0.5%
    {"name": "5,000,000 Coins", "value": 5000000, "type": "coin", "weight": 1.5},   # 1.5%
    {"name": "2,000,000 Coins", "value": 2000000, "type": "coin", "weight": 3},     # 3%
    {"name": "1,000,000 Coins", "value": 1000000, "type": "coin", "weight": 5},     # 5%
    {"name": "500,000 Coins", "value": 500000, "type": "coin", "weight": 9},       # 9%
    {"name": "100,000 Coins", "value": 100000, "type": "coin", "weight": 15},      # 15%
    {"name": "50,000 Coins", "value": 50000, "type": "coin", "weight": 20},        # 20%
    {"name": "10,000 Coins", "value": 10000, "type": "coin", "weight": 25},        # 25%
    {"name": "5,000 Coins", "value": 5000, "type": "coin", "weight": 20}          # 20%
]    



# Công thức EXP lũy tiến: Cấp càng cao càng cần nhiều EXP
def xp_needed(level):
    return int(100 * (level ** 1.5))

# Bảng giá nạp
NAP_PACKAGES = {
    "5k": {"diamonds": 100, "label": "Gói Khởi Đầu (5k = 100KC)"},
    "20k": {"diamonds": 120, "label": "Gói 20k = 120KC"},
    "50k": {"diamonds": 290, "label": "Gói 50k = 300KC"},
    "100k": {"diamonds": 570, "label": "Gói 100k = 680KC"},
    "200k": {"diamonds": 1280, "label": "Gói 200k = 1400KC"},
    "500k": {"diamonds": 2830, "label": "Gói 500k = 2890KC"}
}    


# ================== SETUP BOT ==================

intents = discord.Intents.default()
intents.members = True   # Để xem danh sách thành viên
intents.presences = True # Để xem trạng thái Online/Offline
intents.message_content = True  # Cho phép Bot đọc nội dung tin nhắn
bot = commands.Bot(command_prefix="!", intents=intents)
ADMIN_ID = 1090758840217243688
REPORT_CHANNEL_ID = 1491445396910899290  # <--- Dán ID Kênh vào đây
# Thay ID kênh của bạn vào đây
ID_LOG_NAP_CARD = 1496513685492076704
#Log-ban-thangg-cho-nao-spam
spam_control = {} # Cái giỏ đựng rác nè, thiếu cái này là bot nó xỉu đó!

# 2. SỬA LẠI CÁI EVENT ON_MESSAGE CHO NÓ "GẮT"
@bot.event
async def on_message(message):
    if message.author.bot:
        return # Bot thì tha, hổng có chửi lộn với bot

    user_id = str(message.author.id)
    current_time = time.time()

    # Khởi tạo dữ liệu cho thằng ôn con nào mới vô nhắn tin
    if user_id not in spam_control:
        spam_control[user_id] = {'count': 0, 'last_time': current_time}

    # Kiểm tra xem nó nhắn nhanh hay chậm (dưới 0.8 giây là tao tính spam)
    if current_time - spam_control[user_id]['last_time'] < 0.8:
        spam_control[user_id]['count'] += 1
    else:
        # Nhắn chậm lại thì tao tha, reset cái đếm
        spam_control[user_id]['count'] = 0

    spam_control[user_id]['last_time'] = current_time

# TỚI KHÚC VẢ + GỬI DM TRA TẤN NÈ
    if spam_control[user_id]['count'] > 5:
        try:
            # 1. Chửi dằn mặt ngoài kênh chung trước cái đã
            await message.channel.send(f"Thằng {message.author.mention}! Cái tay mày bị ma nhập hay gì mà bấm dữ vậy? Tao vả cho rụng bộ đồ lòng bây giờ! Biến vô góc nhà mà ngồi sám hối 1 phút cho tao!")[cite: 1]
            
            # 2. GỬI TIN NHẮN RIÊNG (DM) - CHỬI TỚI TẤP, CHỬI KHÔNG KỊP THỞ
            danh_sach_chui = [
                "Mày có tin tao lấy cái chổi lông gà tao quất mày lòi bản họng hông con?",
                "Server người ta đang yên lành, mày vô mày xả rác như cái nhà mày vậy hả?",
                "Mày nhắn nữa đi, tao trù cho cái cục modem nhà mày nó cháy khét lẹt cho mày khỏi lên mạng luôn!",
                "Cái nết gì mà kì cục kẹo vậy? Spam cho cố vô rồi cũng bị tao xách cổ ra ngoài hà!",
                "Lo mà đi học bài hay phụ mẹ nấu cơm đi, ở đó mà bấm bấm cái máy hoài, tao lẹo cái lưỡi mày bây giờ!"
            ]
            
            # Tao cho nó gửi 3 câu chửi vô DM cho nó biết mặt
            for cau_chui in danh_sach_chui[:3]: 
                try:
                    await message.author.send(cau_chui)
                except discord.Forbidden:
                    # Nếu nó khóa DM thì thôi, tao chửi ngoài kia đủ rồi
                    print(f"Thằng {message.author.name} nó nhát gan, nó khóa DM rồi!")[cite: 1]

            # 3. MUTE NÓ CHO NÓ TỊT NGÒI
            duration = datetime.timedelta(minutes=1)
            await message.author.timeout(duration, reason="Spam quá hớp, đã gửi DM cảnh cáo sấp mặt")[cite: 1]
            
            spam_control[user_id]['count'] = 0 # Phạt xong thì reset cho nó "ăn hành" hiệp sau
            
        except discord.Forbidden:
            print("Tao hổng có quyền làm đại ca, coi lại cái Role dùm cái!")[cite: 1]
        except Exception as e:
            print(f"Lỗi gì mà lạ đời vậy nè: {e}")[cite: 1]    
@bot.event
async def on_message(message):
    # 1. Dòng này để mày check xem Bot có đang đọc tin nhắn không
    # Nếu mày nhắn mà CMD không hiện dòng này -> Mày chưa bật "Message Content Intent" trên web Discord
    print(f"DEBUG: Nhận tin từ {message.author.name}: {message.content}")

    # 2. Không check spam cho Bot
    if message.author.bot:
        return

    # 3. GỌI HÀM CHECK SPAM NGAY ĐẦU TIÊN
    # Mày phải chắc chắn hàm check_spam(message) đã được định nghĩa ở TRÊN dòng này
    is_spamming = await check_spam(message)
    
    if is_spamming:
        # Nếu là spam thì dừng luôn, không chạy lệnh bên dưới
        return 

    # 4. CHỈ CHẠY LỆNH KHI KHÔNG PHẢI SPAM
    await bot.process_commands(message)

# --- KẾT THÚC FILE ---

# --- CỬA SỔ NHẬP LIỆU (MODAL) ---


class HelpModal(discord.ui.Modal, title='Phiếu Hỗ Trợ / Báo Cáo'):
    # Ô nhập tiêu đề
    subject = discord.ui.TextInput(
        label='Vấn đề cần hỗ trợ',
        placeholder='Ví dụ: Lỗi nạp tiền, Tố cáo người chơi...',
        required=True,
        max_length=100
    )
    # Ô nhập nội dung chi tiết
    description = discord.ui.TextInput(
        label='Nội dung chi tiết',
        style=discord.TextStyle.long,
        placeholder='Mô tả rõ vấn đề bạn gặp phải...',
        required=True,
        max_length=1000
    )
def get_multiplier(user_id, type="coin"):
    """
    type: "coin" hoặc "exp"
    """
    uid = str(user_id)
    if uid not in active_buffs:
        return 1
    
    current_time = time.time()
    max_multi = 1
    
    # Duyệt qua các buff người dùng đang có
    for item_id, expire_time in list(active_buffs[uid].items()):
        if expire_time > current_time:
            item_info = SHOP_ITEMS.get(item_id)
            # Kiểm tra xem có đúng loại buff (tiền hoặc exp) không
            if item_info and item_info.get('type') == type:
                if item_info['multiplier'] > max_multi:
                    max_multi = item_info['multiplier']
        else:
            # Tiện tay xóa luôn buff hết hạn cho sạch dữ liệu
            del active_buffs[uid][item_id]
            
    return max_multi


async def on_submit(self, interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    try:
        report_channel = interaction.client.get_channel(REPORT_CHANNEL_ID)
        if report_channel is None:
            report_channel = await interaction.client.fetch_channel(REPORT_CHANNEL_ID)

        time_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Tạo Embed gửi cho Admin
        embed = discord.Embed(title="📩 PHIẾU BÁO CÁO MỚI", color=discord.Color.red())
        embed.add_field(name="👤 Người gửi", value=interaction.user.mention, inline=True)
        embed.add_field(name="⏰ Thời gian", value=f"`{time_str}`", inline=True)
        embed.add_field(name="📌 Tiêu đề", value=f"**{self.subject.value}**", inline=False)
        embed.add_field(name="📝 Nội dung", value=self.description.value, inline=False)
        embed.set_footer(text=f"ID Người gửi: {interaction.user.id}")

        # Gửi vào kênh Admin và lấy tin nhắn trả về để lấy ID làm mã phiếu
        msg = await report_channel.send(content="@everyone", embed=embed)
        ticket_id = f"#{msg.id}" # Mã phiếu chính là ID tin nhắn

        # Phản hồi cho người dùng kèm mã phiếu
        await interaction.followup.send(f"✅ Đã gửi báo cáo thành công! Mã phiếu của bạn là: **{ticket_id}**. Admin sẽ xử lý sớm.", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi: Bot thiếu quyền hoặc không tìm thấy kênh.", ephemeral=True)
# ================== HỆ THỐNG LEVEL TỰ ĐỘNG ==================
async def check_level_roles(member, level):
    if level in LEVEL_ROLES:
        role = member.guild.get_role(LEVEL_ROLES[level])
        if role:
            try: await member.add_roles(role)
            except: pass
def xp_needed(level):
    return int(100 * (level ** 1.5))
@bot.event
async def on_message(message):
    # Không tính tin nhắn của Bot
    if message.author.bot: 
        return

    user_id = str(message.author.id)
    
    # Khởi tạo dữ liệu nếu người dùng mới nhắn tin lần đầu
    if user_id not in levels:
        levels[user_id] = {"xp": 0, "level": 1}

# Lấy level hiện tại
    current_lv = levels[user_id]["level"]

    current_time = time.time()
    multiplier = 1 # Mặc định là x1

    if user_id in active_buffs:
        # Kiểm tra X4 trước (ưu tiên cái cao nhất)
        if active_buffs[user_id].get("x16_exp", 0) > current_time:
            multiplier = 16
        elif active_buffs[user_id].get("x8_exp", 0) > current_time:
            multiplier = 8
        elif active_buffs[user_id].get("x4_exp", 0) > current_time:
            multiplier = 4                    
        # Nếu không có X4 thì kiểm tra X2
        elif active_buffs[user_id].get("x2_exp", 0) > current_time:
            multiplier = 2

    # Tính toán EXP nhận được
    bonus_xp = current_lv * 50
    base_xp_gain = random.randint(90, 120) + bonus_xp
    
    # Áp dụng nhân hệ số Buff
    xp_gain = base_xp_gain * multiplier
    
    levels[user_id]["xp"] += xp_gain
    
    # (Tùy chọn) In ra console để bạn theo dõi
    if multiplier > 1:
        print(f"--- {message.author.name} đang dùng Buff x{multiplier}! ---")
    # Vòng lặp WHILE để khấu trừ EXP từng cấp một
    leveled_up = False
    while levels[user_id]["xp"] >= xp_needed(levels[user_id]["level"]):
        # Lấy số EXP đang có trừ đi mốc cần thiết của cấp hiện tại
        levels[user_id]["xp"] -= xp_needed(levels[user_id]["level"])
        
        # Tăng cấp lên 1
        levels[user_id]["level"] += 1
        leveled_up = True

    # Sau khi trừ hết mức có thể, mới thông báo và lưu
    if leveled_up:
        save_all()
        new_lv = levels[user_id]["level"]
        await message.channel.send(f"🎊 Chúc mừng {message.author.mention} đã đạt **Level {new_lv}**!")
 # --- ĐOẠN TRAO ROLE NẰM Ở ĐÂY ---
        roles_to_add = []
        for lv_milestone, role_id in LEVEL_ROLES.items():
            # Nếu level mới của user ĐÚNG BẰNG hoặc VƯỢT QUA mốc milestone
            if new_lv >= lv_milestone:
                role = message.guild.get_role(role_id)
                if role and role not in message.author.roles:
                    roles_to_add.append(role)

        if roles_to_add:
            try:
                await message.author.add_roles(*roles_to_add)
                print(f"✅ Đã trao {len(roles_to_add)} role cho {message.author.name}")
            except Exception as e:
                print(f"❌ Lỗi trao role, vui lòng sử dụng lệnh /help để được hỗ trợ: {e}")

    # Lưu dữ liệu sau mỗi tin nhắn
    save_json(LEVEL_FILE, levels)
    
    # Cho phép bot tiếp tục xử lý các lệnh slash command khác
    await bot.process_commands(message)
    #save all



# ================== 🛡️ NHÓM 1: QUẢN TRỊ & MOD (12 Lệnh) ==================
@bot.tree.command(name="doikc", description="Đổi Kim cương sang Coins (Tỉ lệ: 100 KC = 10,000 Coins)")
@app_commands.describe(amount="Số lượng Kim cương muốn đổi")
async def doikc(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        return await interaction.response.send_message("❌ Số lượng Kim cương phải lớn hơn 0!", ephemeral=True)

    uid = str(interaction.user.id)
    
    # 1. Lấy dữ liệu và chuẩn hóa
    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int): 
        user_econ = {"coins": user_econ, "diamonds": 0}

    # 2. Kiểm tra số dư Kim cương
    if user_econ["diamonds"] < amount:
        return await interaction.response.send_message(
            f"❌ Bạn không đủ Kim cương! Hiện có: `{user_econ['diamonds']:,}` 💎", 
            ephemeral=True
        )

    # 3. Tính toán quy đổi
    # Tỉ lệ: 1 KC = 100 Coins (Vì 100 KC = 10,000 Coins)
    coins_received = amount * 1000

    # 4. Thực hiện giao dịch
    user_econ["diamonds"] -= amount
    user_econ["coins"] += coins_received
    
    economy[uid] = user_econ
    save_all()

    # 5. Phản hồi
    embed = discord.Embed(
        title="🏦 GIAO DỊCH QUY ĐỔI THÀNH CÔNG",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="📉 Kim cương đã đổi", value=f"- `{amount:,}` 💎", inline=True)
    embed.add_field(name="📈 Coins nhận được", value=f"+ `{coins_received:,}` 💰", inline=True)
    embed.add_field(name="💰 Số dư Coins mới", value=f"`{user_econ['coins']:,}` coins", inline=False)
    
    embed.set_footer(text=f"ID: {uid}")
    embed.set_thumbnail(url="https://i.imgur.com/v8S8Anf.png") # Icon kim cương

    await interaction.response.send_message(embed=embed)


# --- LỚP TẠO NÚT BẤM XỬ LÝ NẠP THẺ ---
class NapTheView(discord.ui.View):

  def __init__(self, user_id: int, loai_the: str, menh_gia: str):
    super().__init__(timeout=None)  # Giữ nút bấm luôn hoạt động
    self.user_id = user_id
    self.loai_the = loai_the
    self.menh_gia = menh_gia

  # Nút Chấp nhận
  @discord.ui.button(
      label="Chấp nhận (Thành công)",
      style=discord.ButtonStyle.success,
      emoji="✅",
  )
  async def approve(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    # 1. Khóa tất cả nút bấm lại để không ai bấm lại được nữa
    for child in self.children:
      child.disabled = True

    # 2. Cập nhật Embed trong kênh Log báo đã duyệt
    embed = interaction.message.embeds[0]
    embed.color = discord.Color.blue()
    embed.add_field(
        name="📌 Trạng thái",
        value=f"✅ **Đã duyệt bởi {interaction.user.mention}**",
        inline=False,
    )
    await interaction.response.edit_message(embed=embed, view=self)

    # 3. Gửi DM riêng cho người nạp
    try:
      target_user = await interaction.client.fetch_user(self.user_id)
      if target_user:
        dm_embed = discord.Embed(
            title="🎉 NẠP THẺ THÀNH CÔNG",
            description=(
                f"Yêu cầu nạp thẻ **{self.loai_the}** mệnh giá"
                f" **{self.menh_gia}** của bạn đã được Admin xác nhận thành"
                " công!\nKim cương/Quà đã được cộng vào tài khoản."
            ),
            color=discord.Color.green(),
        )
        await target_user.send(embed=dm_embed)
    except Exception as e:
      print(f"Không thể gửi DM cho user {self.user_id}: {e}")

  # Nút Thất bại
  @discord.ui.button(
      label="Thất bại (Sai thông tin)",
      style=discord.ButtonStyle.danger,
      emoji="❌",
  )
  async def reject(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    # 1. Khóa tất cả nút bấm lại
    for child in self.children:
      child.disabled = True

    # 2. Cập nhật Embed trong kênh Log báo từ chối
    embed = interaction.message.embeds[0]
    embed.color = discord.Color.red()
    embed.add_field(
        name="📌 Trạng thái",
        value=f"❌ **Từ chối bởi {interaction.user.mention}**",
        inline=False,
    )
    await interaction.response.edit_message(embed=embed, view=self)

    # 3. Gửi DM riêng cho người nạp
    try:
      target_user = await interaction.client.fetch_user(self.user_id)
      if target_user:
        dm_embed = discord.Embed(
            title="❌ NẠP THẺ THẤT BẠI",
            description=(
                f"Yêu cầu nạp thẻ **{self.loai_the}** mệnh giá"
                f" **{self.menh_gia}** bị từ chối.\n**Lý do:** Thẻ lỗi hoặc sai"
                " thông tin Seri / Mã thẻ."
            ),
            color=discord.Color.red(),
        )
        await target_user.send(embed=dm_embed)
    except Exception as e:
      print(f"Không thể gửi DM cho user {self.user_id}: {e}")


# --- LỆNH /NAPTIEN CỦA BẠN ---
@bot.tree.command(name="naptien", description="Gửi yêu cầu nạp thẻ cho Admin")
@app_commands.describe(
    loai_the="Chọn nhà mạng (Viettel, Mobi, Vina...)",
    menh_gia="Chọn mệnh giá thẻ nạp",
    seri="Số Seri của thẻ",
    ma_the="Mã số nạp tiền sau lớp cào",
)
@app_commands.choices(
    loai_the=[
        app_commands.Choice(name="Viettel", value="Viettel"),
        app_commands.Choice(name="Mobifone", value="Mobifone"),
        app_commands.Choice(name="Vinaphone", value="Vinaphone"),
        app_commands.Choice(name="Zing (VNG)", value="Zing"),
        app_commands.Choice(name="Gate", value="Gate"),
        app_commands.Choice(name="Garena", value="Garena"),
    ]
)
@app_commands.choices(
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
  # 1. Phản hồi ẩn cho người dùng
  await interaction.response.send_message(
      f"✅ Đã gửi yêu cầu nạp thẻ **{loai_the.name}** mệnh giá **{menh_gia.name}**!"
      " Admin sẽ sớm kiểm tra và duyệt cho bạn.",
      ephemeral=True,
  )

  # 2. Lấy kênh Log
  log_channel = interaction.guild.get_channel(ID_LOG_NAP_CARD)

  if not log_channel:
    print(
        "❌ Cảnh báo: Chưa cài đặt ID kênh Log nạp thẻ (ID hiện tại:"
        f" {ID_LOG_NAP_CARD})"
    )
    return

  # 3. Tạo Embed gửi cho Admin
  embed = discord.Embed(
      title="💳 CÓ YÊU CẦU NẠP THẺ MỚI",
      color=discord.Color.gold(),
      timestamp=discord.utils.utcnow(),
  )

  embed.add_field(
      name="👤 Người gửi",
      value=f"{interaction.user.mention}\nID: `{interaction.user.id}`",
      inline=False,
  )
  embed.add_field(
      name="📶 Nhà mạng", value=f"**{loai_the.name}**", inline=True
  )
  embed.add_field(
      name="💰 Mệnh giá", value=f"**{menh_gia.name}**", inline=True
  )
  embed.add_field(name="🔢 Số Seri", value=f"`{seri}`", inline=False)
  embed.add_field(
      name="🔑 Mã thẻ (Bấm để xem)", value=f"||{ma_the}||", inline=False
  )

  embed.set_thumbnail(url=interaction.user.display_avatar.url)
  embed.set_footer(text="Bấm nút bên dưới để chấp nhận hoặc từ chối đơn này")

  # 4. Gửi vào kênh log kèm 2 Nút Bấm
  view = NapTheView(
      user_id=interaction.user.id,
      loai_the=loai_the.name,
      menh_gia=menh_gia.name,
  )
  await log_channel.send(
      content="🔔 **Thông báo từ hệ thống nạp thẻ:**", embed=embed, view=view
  )

# Ví dụ về hàm lưu dữ liệu của bạn (hãy đảm bảo nó trông như thế này)
def save_all():
    with open("economy.json", "w", encoding="utf-8") as f:
        json.dump(economy, f, indent=4, ensure_ascii=False)

# Cập nhật lệnh add_diamond để lưu đúng cấu trúc
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
    
    # Đảm bảo user có dữ liệu trong dict economy
    if uid not in economy:
        economy[uid] = {"coins": 0, "diamonds": 0}
    
    # Nếu dữ liệu cũ đang là số (chỉ có coins), chuyển sang dict
    if isinstance(economy[uid], int):
        economy[uid] = {"coins": economy[uid], "diamonds": 0}

    # CỘNG VÀO HỆ THỐNG
    economy[uid]["diamonds="] += so_kc
    save_all() # Lệnh này sẽ lưu thẳng vào file economy.json của bạn

    await interaction.response.send_message(f"✅ Đã nạp thành công **{so_kc} 💎** cho {user.mention}!")

@bot.tree.command(name="diamond", description="Xem số dư kim cương và tiền của bạn")
async def diamond(interaction: discord.Interaction, user: discord.Member = None):
    # Nếu không tag ai thì xem của chính mình
    target = user or interaction.user
    uid = str(target.id)
    
    if uid not in economy:
        return await interaction.response.send_message(f"👤 {target.display_name} chưa có tài khoản kinh tế!")

    # Lấy dữ liệu (xử lý cả trường hợp cũ/mới)
    data = economy[uid]
    if isinstance(data, int):
        coins = data
        diamonds = 0
    else:
        coins = data.get("coins", 0)
        diamonds = data.get("diamonds", 0)

    embed = discord.Embed(
        title=f"💰 TÀI KHOẢN CỦA {target.display_name.upper()}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="💵 Tiền xu (Coins)", value=f"`{coins:,}` 💰", inline=False)
    embed.add_field(name="💎 Kim cương", value=f"`{diamonds:,}` 💎", inline=False)
    
    # Thêm dòng nhắc nhở nạp tiền nếu là chính chủ xem
    if target == interaction.user:
        embed.set_footer(text="(Beta Diamond test^^)")

    await interaction.response.send_message(embed=embed)    


import asyncio
import time
import random

# Để lưu cooldown qua các lần restart bot, bạn nên dùng file JSON. 
# Ở đây mình dùng dict tạm thời:
gift_cooldowns = {} 

@bot.tree.command(name="moqua", description="Mở hộp quà may mắn (Free 1 lần/ngày hoặc 500k Coins)")
async def moqua(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    current_time = time.time()
    price = 500000
    
    # Đảm bảo dữ liệu người dùng tồn tại
    if uid not in economy:
        economy[uid] = {"coins": 0, "diamonds": 0}
    if isinstance(economy[uid], int):
        economy[uid] = {"coins": economy[uid], "diamonds": 0}

    # Kiểm tra lượt FREE (24 giờ = 86400 giây)
    last_free = gift_cooldowns.get(uid, 0)
    can_free = (current_time - last_free) >= 86400
    
    is_using_free = False
    
    if can_free:
        is_using_free = True
    else:
        # Nếu hết lượt free, kiểm tra tiền mặt
        if economy[uid]["coins"] < price:
            time_left = 86400 - (current_time - last_free)
            h = int(time_left // 3600)
            m = int((time_left % 3600) // 60)
            return await interaction.response.send_message(
                f"❌ Bạn không đủ {price:,} coins và cũng hết lượt FREE!\n"
                f"⏰ Lượt FREE tiếp theo sau: **{h} giờ {m} phút**.", 
                ephemeral=True
            )
        # Trừ tiền
        economy[uid]["coins"] -= price

    # Phản hồi ban đầu
    await interaction.response.send_message(f"🎁 {interaction.user.mention} đang hồi hộp mở hộp quà may mắn...")
    
    # Hiệu ứng chờ đợi 3 giây cho kịch tính
    await asyncio.sleep(3)

    # Tính toán phần thưởng theo tỉ lệ weights
    weights = [g["weight"] for g in LUCKY_GIFTS]
    reward = random.choices(LUCKY_GIFTS, weights=weights, k=1)[0]

    # Cộng thưởng vào file economy
    if reward["type"] == "coin":
        economy[uid]["coins"] += reward["value"]
        result_text = f"💰 **{reward['value']:,} Coins**"
        color = 0xf1c40f # Màu vàng
    else:
        economy[uid]["diamonds"] += reward["value"]
        result_text = f"💎 **{reward['value']} Kim Cương**"
        color = 0x00ffff # Màu xanh kim cương

    # Nếu dùng lượt free thì cập nhật cooldown
    if is_using_free:
        gift_cooldowns[uid] = current_time
    
    save_all() # Lưu dữ liệu

    # Tạo Embed kết quả
    embed = discord.Embed(title="🎁 KẾT QUẢ MỞ HỘP QUÀ 🎁", color=color)
    embed.set_thumbnail(url="https://www.google.com/imgres?q=%E1%BA%A3nh%20mr%20beast&imgurl=https%3A%2F%2Fphoto.znews.vn%2Fw660%2FUploaded%2Fspluaaa%2F2024_09_23%2F2grnsgnzvb_jpg.jpg&imgrefurl=https%3A%2F%2Fznews.vn%2Fvua-youtube-bi-kien-post1499720.html&docid=Tvn7lLiIN647SM&tbnid=I-3vKB8Sxz8V6M&vet=12ahUKEwi4mqL77KSUAxVfSmwGHZ3YNWwQnPAOegQIShAB..i&w=660&h=371&hcb=2&ved=2ahUKEwi4mqL77KSUAxVfSmwGHZ3YNWwQnPAOegQIShAB")    
    msg_type = "✨ LƯỢT CHƠI MIỄN PHÍ ✨" if is_using_free else f"💸 Chi phí: {price:,} Coins"
    
    embed.add_field(name="Loại lượt chơi", value=msg_type, inline=False)
    embed.add_field(name="Phần thưởng", value=f"🎉 Bạn nhận được: {result_text} 🎉", inline=False)
    
    if reward["type"] == "diamond":
        embed.description = "🔥 **XỊN SÒ! Bạn đã trúng được Kim Cương cực hiếm!** 🔥"
    
    await interaction.edit_original_response(content=None, embed=embed)


@bot.tree.command(name="addexp", description="Thêm kinh nghiệm (EXP) cho người dùng (Admin Only)")
@app_commands.describe(member="Người muốn tặng EXP", amount="Số lượng EXP muốn thêm")
async def addexp(interaction: discord.Interaction, member: discord.Member, amount: int):
    # 1. Kiểm tra quyền Admin
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền Admin để dùng lệnh này!", ephemeral=True)

    if amount <= 0:
        return await interaction.response.send_message("❌ Số lượng EXP phải lớn hơn 0!", ephemeral=True)

    uid = str(member.id)
    
    # 2. Khởi tạo dữ liệu nếu chưa có
    if uid not in levels:
        levels[uid] = {"xp": 0, "level": 1}

    # 3. Thực hiện cộng EXP
    old_lv = levels[uid]["level"]
    levels[uid]["xp"] += amount
    
    # 4. Kiểm tra xem có lên cấp không (Vòng lặp trong trường hợp cộng quá nhiều EXP lên nhiều cấp cùng lúc)
    leveled_up = False
    while levels[uid]["xp"] >= xp_needed(levels[uid]["level"]):
        levels[uid]["xp"] -= xp_needed(levels[uid]["level"])
        levels[uid]["level"] += 1
        leveled_up = True
    
    new_lv = levels[uid]["level"]
    
    # 5. Lưu dữ liệu
    save_json(LEVEL_FILE, levels)

    # 6. Gửi thông báo
    embed = discord.Embed(
        title="✨ CẤP PHÁT KINH NGHIỆM",
        description=f"Admin đã thêm **{amount:,} EXP** cho {member.mention}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Cấp độ hiện tại", value=f"Level `{new_lv}`", inline=True)
    embed.add_field(name="Tiến trình", value=f"`{levels[uid]['xp']}/{xp_needed(new_lv)}` XP", inline=True)
    
    await interaction.response.send_message(embed=embed)

    # 7. Nếu lên cấp, kiểm tra và trao Role tích lũy
    if leveled_up:
        await interaction.channel.send(f"🎉 Chúc mừng {member.mention} đã đạt cấp độ **{new_lv}** nhờ quà tặng từ Admin!")
        
        roles_to_add = []
        for lv_milestone, role_id in LEVEL_ROLES.items():
            if new_lv >= lv_milestone:
                role = interaction.guild.get_role(role_id)
                if role and role not in member.roles:
                    roles_to_add.append(role)
        
        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add)
            except Exception as e:
                print(f"Lỗi trao role khi addexp: {e}")

# --- LỆNH 1: GIVEAWAY NGẪU NHIÊN ---
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

    # --- SỬA LOGIC CỘNG THƯỞNG Ở ĐÂY ---
    if coin > 0:
        user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
        if isinstance(user_econ, int): # Fix data cũ
            user_econ = {"coins": user_econ, "diamonds": 0}
        
        user_econ["coins"] += coin
        economy[uid] = user_econ

    if exp > 0:
        if uid not in levels: levels[uid] = {"xp": 0, "level": 1}
        levels[uid]["xp"] += exp
    # -----------------------------------

    save_all() # Sử dụng hàm lưu tổng của bạn

    embed = discord.Embed(
        title="🎁 GIVEAWAY NGẪU NHIÊN",
        description=f"Chúc mừng bạn may mắn đã nhận được quà từ Admin!",
        color=discord.Color.random(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="👤 Người thắng cuộc", value=winner.mention, inline=False)
    if coin > 0: embed.add_field(name="💰 Tiền thưởng", value=f"`{coin:,}` coins", inline=True)
    if exp > 0: embed.add_field(name="✨ EXP thưởng", value=f"`{exp:,}` exp", inline=True)
    embed.set_thumbnail(url=winner.display_avatar.url)
    embed.set_footer(text=f"Admin: {interaction.user.name}")

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

    # --- SỬA LOGIC CỘNG THƯỞNG Ở ĐÂY ---
    if coin > 0:
        user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
        if isinstance(user_econ, int): # Fix data cũ
            user_econ = {"coins": user_econ, "diamonds": 0}
            
        user_econ["coins"] += coin
        economy[uid] = user_econ

    if exp > 0:
        if uid not in levels: levels[uid] = {"xp": 0, "level": 1}
        levels[uid]["xp"] += exp
    # -----------------------------------

    save_all()

    embed = discord.Embed(
        title="🎁 QUÀ TẶNG TỪ ADMIN",
        description=f"{target.mention} vừa nhận được quà đặc biệt!",
        color=0xFFD700, # Màu vàng Gold
        timestamp=discord.utils.utcnow()
    )
    if coin > 0: embed.add_field(name="💰 Tiền nhận được", value=f"`{coin:,}` coins", inline=True)
    if exp > 0: embed.add_field(name="✨ EXP nhận được", value=f"`{exp:,}` exp", inline=True)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.set_footer(text=f"Admin: {interaction.user.name}")
    
    await interaction.response.send_message(embed=embed)
    
    try:
        await target.send(f"🎉 Bạn đã nhận được quà từ Admin trong server **{interaction.guild.name}**!")
    except:
        pass

@bot.tree.command(name="addmoney", description="Thêm tiền cho người dùng (Admin Only)")
@app_commands.describe(amount="Số tiền muốn cộng", member="Người nhận (để trống nếu tự cộng cho mình)")
@app_commands.checks.has_permissions(administrator=True)
async def addmoney(interaction: discord.Interaction, amount: int, member: discord.Member = None):
    target = member or interaction.user
    uid = str(target.id)

    # 1. Lấy dữ liệu hiện tại (Sử dụng cấu trúc mới)
    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    
    # 2. Kiểm tra và chuyển đổi nếu là dữ liệu cũ (con số)
    if isinstance(user_econ, int):
        user_econ = {"coins": user_econ, "diamonds": 0}

    # 3. Thực hiện cộng tiền vào key "coins"
    user_econ["coins"] += amount
    
    # 4. Cập nhật lại vào database và lưu
    economy[uid] = user_econ
    save_all()

    # Tạo Embed thông báo cho chuyên nghiệp
    embed = discord.Embed(
        title="💰 THÔNG BÁO CỘNG TIỀN",
        description=f"Admin {interaction.user.mention} đã cộng tiền thành công!",
        color=discord.Color.green()
    )
    embed.add_field(name="👤 Người nhận", value=target.mention, inline=True)
    embed.add_field(name="💵 Số tiền", value=f"`+{amount:,}` coins", inline=True)
    embed.add_field(name="💳 Số dư mới", value=f"`{user_econ['coins']:,}` coins", inline=False)
    embed.set_footer(text=f"ID: {uid}")
    embed.timestamp = discord.utils.utcnow()

    await interaction.response.send_message(embed=embed)

# Hàm này để đọc file, hông có file thì tạo mới cái list trống
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
    global ban_data # Liên kết với biến toàn cục để save_all() nhận diện
    
    # 1. ĐẶT GẠCH (Tránh lỗi 404 Unknown Interaction)
    await interaction.response.defer()

    if not interaction.user.guild_permissions.ban_members:
        return await interaction.followup.send("❌ Bạn không có quyền Ban người dùng!", ephemeral=True)

    if member.top_role >= interaction.user.top_role:
        return await interaction.followup.send("❌ Không thể ban người có vai trò cao hơn hoặc bằng mình!", ephemeral=True)

    guild = interaction.guild
    seconds = 0
    thoi_han_str = f"{thoi_han} {don_vi.name}"

    # Tính toán giây để Unban
    if don_vi.value != "permanent":
        if don_vi.value == "minutes": seconds = thoi_han * 60
        elif don_vi.value == "hours": seconds = thoi_han * 3600
        elif don_vi.value == "days": seconds = thoi_han * 86400
    
    # Tạo link invite tự động
    invite_link = "Liên hệ Admin"
    if don_vi.value != "permanent":
        try:
            invite = await interaction.channel.create_invite(max_uses=1, unique=True)
            invite_link = invite.url
        except: pass

    # 2. GỬI THÔNG BÁO DM (Giao diện giống image_b1b141.png)
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
    except:
        print(f"Không thể gửi DM cho {member.name}")

    # 3. THỰC HIỆN BAN VÀ LƯU FILE
    try:
        await member.ban(reason=ly_do, delete_message_days=0)
        
        # Nếu ban có thời hạn thì lưu vào Dictionary
        if don_vi.value != "permanent":
            ban_data[str(member.id)] = {
                "user_name": member.name,
                "guild_id": guild.id,
                "unban_at": time.time() + seconds
            }
            save_all() # Gọi hàm lưu tổng mà mày đã sửa ở dòng 49

        await interaction.followup.send(f"🚨 Đã đuổi **{member.name}** khỏi server. Thời hạn: `{thoi_han_str if don_vi.value != 'permanent' else 'Vĩnh viễn'}`")

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi thực hiện: {e}", ephemeral=True)

@bot.tree.command(name="unban", description="Gỡ cấm ngay lập tức và cập nhật dữ liệu")
@app_commands.describe(user_id="ID Discord của người cần gỡ ban")
async def unban(interaction: discord.Interaction, user_id: str):
    global ban_data
    await interaction.response.defer() # Luôn defer cho chắc ăn

    if not interaction.user.guild_permissions.ban_members:
        return await interaction.followup.send("❌ Bạn không có quyền gỡ cấm!", ephemeral=True)

    guild = interaction.guild
    
    try:
        uid = int(user_id)
        user = await bot.fetch_user(uid)
        
        # Gỡ ban trên Discord
        await guild.unban(user, reason=f"Gỡ ban bởi {interaction.user.name}")
        
        # Xóa khỏi biến ban_data và lưu file
        uid_str = str(uid)
        if uid_str in ban_data:
            del ban_data[uid_str]
            save_all() # Cập nhật lại data.json ngay lập tức
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

@bot.tree.command(name="clear")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 Đã xóa {amount} tin nhắn.", ephemeral=True)

# Lệnh ẩn bổ sung cho Admin: /lock, /unlock, /warn, /unwarn, /slowmode, /nuke
@bot.tree.command(name="setlevel", description="Đặt cấp độ cho người dùng (Admin)")
async def setlevel(interaction: discord.Interaction, level: int, member: discord.Member = None):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền Admin!", ephemeral=True)
    
    target = member or interaction.user
    uid = str(target.id)
    
    levels.setdefault(uid, {"xp": 0, "level": 1})
    levels[uid]["level"] = level
    levels[uid]["xp"] = 0 # Reset XP về 0 khi set level mới
    
    save_json(LEVEL_FILE, levels)
    
    # Kiểm tra trao Role ngay lập tức
    if level in LEVEL_ROLES:
        role = interaction.guild.get_role(LEVEL_ROLES[level])
        if role:
            try: await target.add_roles(role)
            except: pass
            
    await interaction.response.send_message(f"✅ Đã đặt cấp độ của {target.mention} thành **Level {level}**.")
@bot.tree.command(name="setmoney", description="Đặt số tiền cho người dùng (Chỉ dành cho Admin)")
@app_commands.describe(amount="Số tiền muốn đặt", member="Người dùng cần đặt lại tiền")
async def setmoney(interaction: discord.Interaction, amount: int, member: discord.Member = None):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền Admin!", ephemeral=True)
    
    target = member or interaction.user
    uid = str(target.id)
    
    # 1. Lấy dữ liệu hiện tại
    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    
    # 2. Kiểm tra/Chuyển đổi nếu là dữ liệu cũ
    if isinstance(user_econ, int):
        user_econ = {"coins": user_econ, "diamonds": 0}
    
    # 3. THAY ĐỔI: Chỉ đặt lại giá trị coins, giữ nguyên diamonds
    user_econ["coins"] = amount
    
    # 4. Lưu lại
    economy[uid] = user_econ
    save_all() # Hoặc save_json(ECON_FILE, economy) tùy hàm bạn dùng

    embed = discord.Embed(
        title="🔧 ĐẶT LẠI SỐ DƯ",
        description=f"Admin {interaction.user.mention} đã thiết lập lại tài khoản của {target.mention}",
        color=discord.Color.orange(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="💰 Tiền xu mới", value=f"`{amount:,}` coins", inline=True)
    embed.add_field(name="💎 Kim cương", value=f"`{user_econ['diamonds']:,}` diamonds", inline=True)
    embed.set_footer(text=f"ID: {uid}")

    await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name="setdiamond", description="Đặt lại số lượng kim cương cho người dùng (Admin Only)")
@app_commands.describe(amount="Số kim cương muốn đặt", member="Người dùng cần đặt lại")
@app_commands.checks.has_permissions(administrator=True)
async def setdiamond(interaction: discord.Interaction, amount: int, member: discord.Member = None):
    target = member or interaction.user
    uid = str(target.id)
    
    # Lấy dữ liệu và fix data cũ nếu cần
    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int):
        user_econ = {"coins": user_econ, "diamonds": 0}
    
    # ĐẶT LẠI giá trị (không phải cộng dồn)
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
    
    # Lấy dữ liệu và fix data cũ nếu cần
    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int):
        user_econ = {"coins": user_econ, "diamonds": 0}
    
    # CỘNG THÊM giá trị
    user_econ["diamonds"] += amount
    economy[uid] = user_econ
    save_all()

    await interaction.response.send_message(f"💎 Đã cộng thêm `{amount:,}` Kim cương cho {target.mention}!")


@bot.tree.command(name="reset", description="Reset dữ liệu (Tiền,  Level) cho 1 người hoặc tất cả")
@app_commands.describe(scope="Chọn phạm vi: Cá nhân hoặc Tất cả", member="Chọn người cần reset (nếu chọn cá nhân)")
@app_commands.choices(scope=[
    app_commands.Choice(name="Cá nhân (Chỉ 1 người)", value="individual"),
    app_commands.Choice(name="Tất cả (Toàn bộ Server)", value="all")
])
async def reset(interaction: discord.Interaction, scope: app_commands.Choice[str], member: discord.Member = None):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền Admin!", ephemeral=True)

    # File names
    L_FILE = "levels.json"
    E_FILE = "economy.json"

    if scope.value == "individual":
        if not member:
            return await interaction.response.send_message("❌ Bạn chưa chọn người cần reset!", ephemeral=True)
        
        uid = str(member.id)
        
        # Reset Level & EXP
        levels[uid] = {"xp": 0, "level": 1}
        
        # SỬA LẠI: Reset Economy về cấu trúc mới thay vì số 0
        economy[uid] = {"coins": 0}
        
        save_json(L_FILE, levels)
        save_json(E_FILE, economy)
        await interaction.response.send_message(f"✅ Đã reset toàn bộ dữ liệu (Tiền, Kim cương, Level) của {member.mention} về mặc định.")

    elif scope.value == "all":
        view = discord.ui.View()
        confirm_btn = discord.ui.Button(label="XÁC NHẬN RESET TẤT CẢ", style=discord.ButtonStyle.danger)
        
        async def confirm_callback(itn: discord.Interaction):
            # Xóa sạch dữ liệu
            levels.clear()
            economy.clear()
            
            # Lưu file trắng
            save_json(L_FILE, levels)
            save_json(E_FILE, economy)
            
            await itn.response.edit_message(content="🚨 **ĐÃ RESET TOÀN BỘ DỮ LIỆU SERVER!** (Tất cả xu và cấp độ đã về 0)", view=None)

        confirm_btn.callback = confirm_callback
        view.add_item(confirm_btn)
        await interaction.response.send_message("⚠️ **CẢNH BÁO:** Bạn có chắc chắn muốn xóa sạch dữ liệu của **TẤT CẢ** mọi người? Hành động này không thể hoàn tác!", view=view)
@bot.tree.command(name="lock", description="Khóa kênh hiện tại (Chặn thành viên nhắn tin)")
@app_commands.describe(ly_do="Lý do khóa kênh")
async def lock(interaction: discord.Interaction, ly_do: str = "Bảo trì hoặc ổn định trật tự"):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ Bạn không có quyền quản lý kênh!", ephemeral=True)

    channel = interaction.channel
    overwrite = channel.overwrites_for(interaction.guild.default_role)
    
    if overwrite.send_messages == False:
        return await interaction.response.send_message("🔒 Kênh này đã bị khóa từ trước rồi!", ephemeral=True)

    # Chặn quyền gửi tin nhắn của @everyone
    overwrite.send_messages = False
    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

    embed = discord.Embed(
        title="🔒 KÊNH ĐÃ BỊ KHÓA",
        description=f"Thành viên không thể gửi tin nhắn trong kênh này.\n**Lý do:** {ly_do}",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Thực hiện bởi {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unlock", description="Mở khóa kênh hiện tại")
async def unlock(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ Bạn không có quyền quản lý kênh!", ephemeral=True)

    channel = interaction.channel
    overwrite = channel.overwrites_for(interaction.guild.default_role)

    if overwrite.send_messages == True or overwrite.send_messages == None:
        return await interaction.response.send_message("🔓 Kênh này đang ở trạng thái mở!", ephemeral=True)

    # Trả lại quyền gửi tin nhắn (hoặc để mặc định)
    overwrite.send_messages = None 
    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

    embed = discord.Embed(
        title="🔓 KÊNH ĐÃ ĐƯỢC MỞ KHÓA",
        description="Thành viên hiện đã có thể nhắn tin bình thường.",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Thực hiện bởi {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="help", description="Gửi yêu cầu hỗ trợ trực tiếp cho Admin")
@app_commands.describe(tieude="Tiêu đề ngắn gọn", noidung="Mô tả chi tiết vấn đề")
async def help_command(interaction: discord.Interaction, tieude: str, noidung: str):
    # 1. Báo cho Discord là đang xử lý để tránh timeout
    await interaction.response.defer(ephemeral=True)
    
    try:
        # 2. Lấy kênh báo cáo
        channel = bot.get_channel(REPORT_CHANNEL_ID)
        
        # Nếu không lấy được bằng get_channel, thử dùng fetch_channel
        if channel is None:
            try:
                channel = await bot.fetch_channel(REPORT_CHANNEL_ID)
            except:
                return await interaction.followup.send("❌ Bot không tìm thấy kênh báo cáo. Admin hãy kiểm tra lại ID Kênh!", ephemeral=True)

        # 3. Lấy giờ Việt Nam
        time_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # 4. Tạo Embed chuyên nghiệp
        embed = discord.Embed(title="📩 PHIẾU HỖ TRỢ MỚI", color=discord.Color.red())
        embed.add_field(name="👤 Người gửi", value=interaction.user.mention, inline=True)
        embed.add_field(name="⏰ Thời gian", value=f"`{time_now}`", inline=True)
        embed.add_field(name="📌 Tiêu đề", value=f"**{tieude}**", inline=False)
        embed.add_field(name="📝 Nội dung", value=noidung, inline=False)
        embed.set_footer(text=f"ID Người gửi: {interaction.user.id}")
        embed.timestamp = discord.utils.utcnow()

       # Gửi và lấy ID làm mã phiếu
        msg = await channel.send(content="@everyone", embed=embed)
        ticket_id = f"#{msg.id}"

        await interaction.followup.send(f"✅ Báo cáo đã được gửi! Mã phiếu: **{ticket_id}**. Thời gian: `{time_now}`", ephemeral=True)
    except Exception as e:


        print(f"Lỗi lệnh help: {e}")
        # Dùng followup.send vì đã gọi defer ở trên
        try:
            await interaction.followup.send(f"❌ Có lỗi xảy ra: {e}", ephemeral=True)
        except:
            pass

@bot.tree.command(name="addrole", description="Thêm một Role cụ thể cho thành viên")
@app_commands.describe(member="Người cần nhận Role", role="Role muốn thêm")
async def addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    # 1. Kiểm tra quyền của người thực hiện lệnh
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Bạn không có quyền `Quản lý vai trò` để dùng lệnh này!", ephemeral=True)

    # 2. Kiểm tra vị trí của Role Bot so với Role muốn thêm
    # Bot không thể thêm Role cao hơn Role cao nhất của chính nó
    bot_member = interaction.guild.me
    if role >= bot_member.top_role:
        return await interaction.response.send_message("❌ Bot không thể thêm Role này vì nó cao hơn hoặc bằng vai trò của Bot!", ephemeral=True)

    # 3. Kiểm tra xem người đó đã có Role này chưa
    if role in member.roles:
        return await interaction.response.send_message(f"⚠️ Người dùng {member.mention} đã có vai trò {role.mention} rồi.", ephemeral=True)

    try:
        # 4. Thực hiện thêm Role
        await member.add_roles(role)
        
        embed = discord.Embed(
            title="✅ CẤP VAI TRÒ THÀNH CÔNG",
            description=f"Đã thêm vai trò {role.mention} cho {member.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Người thực hiện: {interaction.user.name}")
        embed.set_timestamp()
        
        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"❌ Đã xảy ra lỗi: {e}", ephemeral=True)
@bot.tree.command(name="removerole", description="Gỡ một Role khỏi thành viên")
@app_commands.describe(member="Người cần gỡ Role", role="Role muốn gỡ")
async def removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Bạn không có quyền gỡ vai trò!", ephemeral=True)

    if role not in member.roles:
        return await interaction.response.send_message(f"⚠️ Người dùng {member.mention} vốn không có vai trò {role.mention}.", ephemeral=True)

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

    # 1. Kiểm tra ngày hết hạn
    expiry_date = datetime.datetime.strptime(data["expiry"], "%d/%m/%Y %H:%M")
    if now > expiry_date:
        return await interaction.response.send_message("⏰ Mã code này đã hết hạn sử dụng!", ephemeral=True)

    # 2. Kiểm tra số lượt nhập
    if data["max_uses"] != -1:
        if data["current_uses"] >= data["max_uses"]:
            return await interaction.response.send_message("📉 Mã code này đã đạt giới hạn lượt nhập!", ephemeral=True)

    # 3. Kiểm tra xem người dùng đã nhận mã này chưa
    if uid in data["users_claimed"]:
        return await interaction.response.send_message("⚠️ Bạn đã nhận quà từ mã code này rồi!", ephemeral=True)

    # 4. Trao thưởng (SỬA LOGIC Ở ĐÂY)
    reward_coin = data["rewards"].get("coins", 0)
    reward_exp = data["rewards"].get("exp", 0)
    reward_diamond = data["rewards"].get("diamonds", 0) # Thêm kim cương
    
    # Xử lý cộng xu/kim cương an toàn
    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int): # Fix data cũ
        user_econ = {"coins": user_econ, "diamonds": 0}
    
    user_econ["coins"] += reward_coin
    user_econ["diamonds"] += reward_diamond
    economy[uid] = user_econ

    # Xử lý EXP
    if uid not in levels: levels[uid] = {"xp": 0, "level": 1}
    levels[uid]["xp"] += reward_exp
    
    # 5. Cập nhật dữ liệu code
    data["current_uses"] += 1
    data["users_claimed"].append(uid)
    
    save_all() # Lưu toàn bộ

    embed = discord.Embed(title="🎁 NHẬN QUÀ THÀNH CÔNG", color=discord.Color.green())
    embed.description = f"Chúc mừng {interaction.user.mention} đã nhập thành công mã `{code}`"
    if reward_coin > 0: embed.add_field(name="💰 Tiền mặt", value=f"`{reward_coin:,}` coins", inline=True)
    if reward_diamond > 0: embed.add_field(name="💎 Kim cương", value=f"`{reward_diamond:,}` KC", inline=True)
    if reward_exp > 0: embed.add_field(name="✨ Kinh nghiệm", value=f"`{reward_exp:,}` EXP", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="createcode", description="Tạo mã Giftcode mới (Admin Only)")
@app_commands.describe(
    code="Tên mã ", 
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
        # Kiểm tra định dạng ngày tháng
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
        
        gifts = []
        if coins > 0: gifts.append(f"💰 {coins:,} Coins")
        if diamonds > 0: gifts.append(f"💎 {diamonds:,} Kim cương")
        if exp > 0: gifts.append(f"✨ {exp:,} EXP")
        
        embed.add_field(name="🎁 Phần thưởng", value="\n".join(gifts) if gifts else "Không có", inline=False)
        
        await interaction.response.send_message(embed=embed)
    except ValueError:
        await interaction.response.send_message("❌ Sai định dạng thời gian! Kiểu mẫu: `Ngày/Tháng/Năm Giờ:Phút`", ephemeral=True)


@bot.tree.command(name="checkbots", description="Kiểm tra trạng thái hoạt động của tất cả Bot trong server")
async def checkbots(interaction: discord.Interaction):
    bot_list = []
    
    # Duyệt qua tất cả thành viên trong server
    for member in interaction.guild.members:
        if member.bot: # Chỉ lấy những thành viên là Bot
            # Kiểm tra trạng thái
            if member.status == discord.Status.online:
                status_icon = "🟢 **Online**"
            elif member.status == discord.Status.idle:
                status_icon = "🌙 **Chờ**"
            elif member.status == discord.Status.dnd:
                status_icon = "⛔ **Đừng làm phiền**"
            else:
                status_icon = "🔴 **Offline**"
                
            # Tránh liệt kê chính bản thân nó vào danh sách (nếu muốn)
            if member.id == bot.user.id:
                bot_list.append(f"🤖 {member.mention} (Là mình nè!) - {status_icon}")
            else:
                bot_list.append(f"🤖 {member.mention} - {status_icon}")

    # Tạo Embed để hiển thị cho đẹp
    embed = discord.Embed(
        title=f"📊 Trạng thái Bot tại {interaction.guild.name}",
        description="\n".join(bot_list) if bot_list else "Không tìm thấy Bot nào khác.",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Tổng cộng: {len(bot_list)} Bots")
    
    await interaction.response.send_message(embed=embed)

# ================== 💰 NHÓM 2: KINH TẾ & MEMBER (10 Lệnh) ==================
BOT_VERSION = "2.6.1"
UPDATE_LOG = """
**Phiên bản 2.8.5**
** Sự kiện tổng kết và sự kiện thanh xuân **
**Bot tổ chức sự kiên @1505946724756099082**
**Fix các lỗi của sự kiện**
**VUI LÒNG KHÔNG SỬ DỤNG LỆNH ĐANG ĐƯỢC BẢO TRÌ ĐỂ TRÁNH MẤT TIỀN!!**
|| Sử dụng lệnh `/help` để nhận được sự hỗ trợ từ phía admin ||
"""

@bot.tree.command(name="updlog", description="Xem nhật ký cập nhật của Bot.")
async def uptlog(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"🆙 Cập nhật Bot - v{BOT_VERSION}",
        description=UPDATE_LOG,
        color=discord.Color.green()
    )
    embed.set_footer(text="Cảm ơn bạn đã sử dụng!")
    await interaction.response.send_message(embed=embed)


# --- LỆNH SLASH COMMAND ---
# Lệnh loại 2: Xóa số lượng tin nhắn theo yêu cầu
@bot.tree.command(name="xoa", description="Xóa số lượng tin nhắn nhất định trong kênh")
@app_commands.checks.has_permissions(manage_messages=True) # Yêu cầu quyền quản lý tin nhắn
async def clear(interaction: discord.Interaction, amount: int):
    if amount < 1:
        await interaction.response.send_message("❌ Số lượng tin nhắn xóa phải ít nhất là 1!", ephemeral=True)
        return

    # Gửi phản hồi tạm thời vì quá trình xóa có thể mất vài giây
    await interaction.response.defer(ephemeral=True)
    
    # Thực hiện xóa (limit + 1 để xóa cả lệnh vừa gọi nếu là lệnh prefix, 
    # nhưng với Slash command thì chỉ cần xóa đúng amount)
    deleted = await interaction.channel.purge(limit=amount)
    
    await interaction.followup.send(f"✅ Đã xóa thành công **{len(deleted)}** tin nhắn!")

# Lệnh loại 1: Xóa tin nhắn của 1 người cụ thể trong 1 kênh
@bot.tree.command(name="clear_user", description="Xóa tin nhắn của một người cụ thể trong kênh này")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_user(interaction: discord.Interaction, user: discord.Member, amount: int):
    if amount < 1:
        await interaction.response.send_message("❌ Số lượng tin nhắn xóa phải ít nhất là 1!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    # Hàm lọc: chỉ xóa tin nhắn nếu author là người được chọn
    def is_user(m):
        return m.author.id == user.id

    deleted = await interaction.channel.purge(limit=amount, check=is_user)
    
    await interaction.followup.send(f"✅ Đã dọn dẹp **{len(deleted)}** tin nhắn của {user.mention}!")

# ================== 💸 HỆ THỐNG GIAO DỊCH & ĐIỂM DANH ==================

# --- VIEW CHỨA NÚT BẤM ĐIỂM DANH ---
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

        # --- PHẦN THƯỞNG CHỈ CÓ COINS VÀ EXP ---
        coin_reward = min(1000 + (day - 1) * 200, 5000)
        exp_reward = min(100 + (day - 1) * 20, 500)

        # --- CẬP NHẬT AN TOÀN (BÓC TÁCH DICT) ---
        user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
        if isinstance(user_econ, int): # Chuyển đổi data cũ nếu có
            user_econ = {"coins": user_econ, "diamonds": 0}
        
        user_econ["coins"] += coin_reward
        # Tuyệt đối không cộng Diamonds ở đây để giữ giá trị
        economy[uid] = user_econ

        if uid not in levels: levels[uid] = {"xp": 0, "level": 1}
        levels[uid]["xp"] += exp_reward
        
        daily_data[uid]["last_claim"] = now.isoformat()
        save_all()

        # --- PHẢN HỒI ---
        self.clear_items()
        await interaction.response.edit_message(content=f"✅ **{interaction.user.name}** đã điểm danh ngày {day} thành công!", view=self)
        
        await interaction.followup.send(
            f"💰 Bạn nhận được: `{coin_reward:,}` coins\n✨ Bạn nhận được: `{exp_reward:,}` EXP\n"
            f"*Hãy dùng Coins để săn trong `/moqua` nhé!*", 
            ephemeral=True
        )
# --- LỆNH SLASH COMMAND ---
@bot.tree.command(name="daily", description="Mở bảng điểm danh nhận quà hàng ngày")
async def daily(interaction: discord.Interaction):
    now = datetime.datetime.now()
    year, month, today = now.year, now.month, now.day
    
    # Tạo danh sách các ngày trong tháng để hiển thị vào Embed
    cal = calendar.monthcalendar(year, month)
    month_name = f"Tháng {month} / {year}"
    
    calendar_text = f"```\nThứ 2  Thứ 3  Thứ 4  Thứ 5  Thứ 6  Thứ 7  CN\n"
    for week in cal:
        week_str = ""
        for day in week:
            if day == 0:
                week_str += "    " # Ngày trống
            elif day == today:
                week_str += f" [{day:2}]" # Khoanh vùng ngày hiện tại
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
    embed.set_footer(text="Lưu ý: Quà tặng sẽ tăng dần theo ngày trong tháng!")
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    view = DailyView()
    await interaction.response.send_message(embed=embed, view=view)


        
# ==========================================
# 1. VIEW XÁC NHẬN (ConfirmPay)
# ==========================================
class ConfirmPay(discord.ui.View):
    def __init__(self, s, r, a):
        super().__init__(timeout=60)
        self.s, self.r, self.a = s, r, a

    @discord.ui.button(label="Xác nhận chuyển", style=discord.ButtonStyle.green, emoji="✅")
    async def ok(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.s.id: return
        
        sid, rid = str(self.s.id), str(self.r.id)

        # --- LẤY DỮ LIỆU VÀ FIX CẤU TRÚC ---
        s_data = economy.get(sid, {"coins": 0, "diamonds": 0})
        if isinstance(s_data, int): s_data = {"coins": s_data, "diamonds": 0}
        
        r_data = economy.get(rid, {"coins": 0, "diamonds": 0})
        if isinstance(r_data, int): r_data = {"coins": r_data, "diamonds": 0}

        # Kiểm tra lại số dư xu
        if s_data["coins"] < self.a:
            return await interaction.response.edit_message(content="❌ Số dư của bạn không đủ để thực hiện giao dịch!", view=None)

        # --- THỰC HIỆN CHUYỂN (Chỉ trừ/cộng coins) ---
        s_data["coins"] -= self.a
        r_data["coins"] += self.a
        
        # Cập nhật lại vào global economy
        economy[sid] = s_data
        economy[rid] = r_data
        
        save_all()

        await interaction.response.edit_message(content=f"✅ Chuyển thành công `{self.a:,}` coins cho **{self.r.name}**!", view=None)
        try:
            await self.r.send(f"💰 Bạn nhận được `{self.a:,}` coins từ **{self.s.name}**!")
        except: pass
        self.stop()

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.s.id: return
        await interaction.response.edit_message(content="❌ Đã hủy giao dịch.", view=None)
        self.stop()

@bot.tree.command(name="chuyentien", description="Chuyển tiền ví cho người khác")
async def chuyentien(interaction: discord.Interaction, user: discord.Member, amount: int):
    if user.id == interaction.user.id or amount <= 0:
        return await interaction.response.send_message("❌ Lỗi: Người nhận hoặc số tiền không hợp lệ!", ephemeral=True)

    if user.bot:
        return await interaction.response.send_message("❌ Không thể chuyển tiền cho Bot!", ephemeral=True)

    uid_s = str(interaction.user.id)
    
    # Lấy dữ liệu người gửi để kiểm tra tiền
    s_data = economy.get(uid_s, {"coins": 0, "diamonds": 0})
    if isinstance(s_data, int): s_data = {"coins": s_data, "diamonds": 0}

    if s_data["coins"] < amount:
        return await interaction.response.send_message(f"❌ Bạn không đủ tiền! Ví hiện tại: `{s_data['coins']:,}` coins", ephemeral=True)

    view = ConfirmPay(interaction.user, user, amount)
    try:
        # Gửi DM để xác nhận cho bảo mật
        await interaction.user.send(f"🔔 Bạn có chắc chắn muốn chuyển `{amount:,}` coins cho **{user.name}** không?", view=view)
        await interaction.response.send_message("📩 Một yêu cầu xác nhận đã được gửi vào Tin nhắn riêng (DM) của bạn!", ephemeral=True)
    except:
        await interaction.response.send_message("❌ Lỗi: Bạn cần mở DM để Bot có thể gửi nút xác nhận!", ephemeral=True)


@bot.tree.command(name="rank", description="Xem bảng xếp hạng những người giàu nhất server")
async def rank(interaction: discord.Interaction):
    # 1. Chuẩn hóa dữ liệu để sắp xếp (Chống lỗi Dictionary)
    processed_list = []
    for uid, data in economy.items():
        if isinstance(data, int):
            coins = data
            diamonds = 0
        else:
            coins = data.get("coins", 0)
            diamonds = data.get("diamonds", 0)
        
        processed_list.append({
            "uid": uid,
            "coins": coins,
            "diamonds": diamonds
        })

    # 2. Sắp xếp theo Coins giảm dần
    sorted_econ = sorted(processed_list, key=lambda x: x["coins"], reverse=True)
    top_10 = sorted_econ[:10]
    
    embed = discord.Embed(
        title="🏆 BẢNG XẾP HẠNG ĐẠI GIA SERVER",
        description="Ai là người đang nắm giữ nền kinh tế của server này?",
        color=0xffd700, # Màu Vàng Gold
        timestamp=discord.utils.utcnow()
    )

    leaderboard_text = ""
    
    for i, user_info in enumerate(top_10, start=1):
        uid = user_info["uid"]
        money = user_info["coins"]
        dias = user_info["diamonds"]
        
        # Lấy thông tin Member từ Server
        member = interaction.guild.get_member(int(uid))
        name = member.name if member else f"Người dùng cũ ({uid})"
        
        # --- PHẦN HIỂN THỊ ROLE ---
        top_role = "Không có"
        if member:
            # Lấy role cao nhất (bỏ qua @everyone)
            roles = [r for r in member.roles if r != interaction.guild.default_role]
            if roles:
                top_role = member.top_role.mention # Dùng mention để hiện màu và tên role
        
        # Lấy Level
        user_lv_data = levels.get(uid, {"level": 1, "xp": 0})
        lv = user_lv_data.get("level", 1)
        
        # Huy chương cho Top 3
        medal = "👤"
        if i == 1: medal = "🥇"
        elif i == 2: medal = "🥈"
        elif i == 3: medal = "🥉"

        leaderboard_text += f"{medal} **Top {i}: {name}**\n"
        leaderboard_text += f"> 💰 Coins: `{money:,}` | 💎 `{dias:,}` KC\n"
        leaderboard_text += f"> ⭐ Level: `{lv}` | 🎭 {top_role}\n\n"

    if not leaderboard_text:
        leaderboard_text = "Chưa có dữ liệu xếp hạng."

    embed.description = leaderboard_text
    embed.set_footer(text=f"Yêu cầu bởi {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="info", description="Xem thông tin chi tiết của bản thân hoặc người khác")
@app_commands.describe(member="Chọn người cần xem thông tin (để trống nếu muốn xem bản thân)")
async def info(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    uid = str(target.id)

    # 1. Lấy dữ liệu Level & EXP
    user_lvl = levels.get(uid, {"level": 1, "xp": 0})
    lvl = user_lvl.get("level", 1)
    xp = user_lvl.get("xp", 0)
    needed = xp_needed(lvl) 

    # 2. LẤY DỮ LIỆU KINH TẾ (Sửa lỗi NameError ở đây)
    # Lấy dữ liệu từ economy, nếu không có thì mặc định là dict mới
    user_econ_data = economy.get(uid, {"coins": 0, "diamonds": 0})
    
    # Kiểm tra nếu là dữ liệu cũ (chỉ là 1 con số int)
    if isinstance(user_econ_data, int):
        coins = user_econ_data
        diamonds = 0
    else:
        # Nếu là dict thì bóc tách riêng từng món
        coins = user_econ_data.get("coins", 0)
        diamonds = user_econ_data.get("diamonds", 0)

    # 3. Thông tin Role & Thời gian
    roles = [role.mention for role in target.roles if role != interaction.guild.default_role]
    roles_str = " ".join(roles) if roles else "Không có"
    created_at = target.created_at.strftime("%d/%m/%Y")
    joined_at = target.joined_at.strftime("%d/%m/%Y")

    # 4. TẠO EMBED MỚI
    embed = discord.Embed(
        title=f"👤 Thông tin người dùng: {target.name}",
        color=target.color,
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    
    # Nhóm 1: Tài chính (Dùng :, để phân cách hàng nghìn cho đẹp)
    embed.add_field(name="💰 Tài chính", value=f"`{coins:,}` coins", inline=True)
    embed.add_field(name="💎 Kim cương", value=f"`{diamonds:,}` diamonds", inline=True)
    embed.add_field(name="⭐ Cấp độ", value=f"Level `{lvl}`", inline=True)
    
    # Nhóm 2: EXP & Thời gian
    embed.add_field(name="✨ Kinh nghiệm", value=f"`{xp:,}/{needed:,}` XP", inline=True)
    embed.add_field(name="🗓️ Ngày tạo", value=f"`{created_at}`", inline=True)
    embed.add_field(name="📥 Ngày tham gia", value=f"`{joined_at}`", inline=True)


    # Nhóm 3: Vai trò
    embed.add_field(name=f"🎭 Vai trò ({len(roles)})", value=roles_str, inline=False)

    embed.set_footer(text=f"ID: {uid}")
    
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="money", description="Xem số tiền")
async def money(interaction: discord.Interaction):
    bal = economy.get(str(interaction.user.id), 0)
    await interaction.response.send_message(f"💰 Bạn có: `{bal:,}` coins.")

@bot.tree.command(name="level", description="Xem cấp độ")
async def level_cmd(interaction: discord.Interaction):
    data = levels.get(str(interaction.user.id), {"xp": 0, "level": 1})
    await interaction.response.send_message(f"⭐ Cấp: {data['level']} | XP: {data['xp']}/{data['level']*100}")

@bot.tree.command(name="doiexp", description="Dùng tiền để mua cấp độ")
@app_commands.describe(levels_count="Số cấp độ muốn mua")
async def doiexp(interaction: discord.Interaction, levels_count: int):
    uid = str(interaction.user.id)
    cost_per_level = 5000 # 5000 coins cho 1 level
    total_cost = levels_count * cost_per_level

    if levels_count <= 0:
        return await interaction.response.send_message("Số cấp độ phải lớn hơn 0!", ephemeral=True)

    # --- CHỈNH SỬA TẠI ĐÂY ĐỂ HẾT LỖI TYPEERROR ---
    # Lấy dữ liệu kinh tế và chuẩn hóa
    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int): 
        user_econ = {"coins": user_econ, "diamonds": 0}

    # Lấy ra số coins để so sánh (Lỗi cũ nằm ở đây vì so sánh dict < int)
    user_money = user_econ["coins"]

    if user_money < total_cost:
        return await interaction.response.send_message(f"Bạn không đủ tiền! Cần `{total_cost:,}` coins để mua `{levels_count}` level.", ephemeral=True)

    # Khởi tạo dữ liệu level nếu chưa có
    if uid not in levels:
        levels[uid] = {"xp": 0, "level": 1}

    # THỰC HIỆN TRỪ TIỀN VÀ CỘNG LEVEL
    user_econ["coins"] -= total_cost # Trừ vào coins trong dict
    economy[uid] = user_econ         # Cập nhật lại vào bộ nhớ
    
    levels[uid]["level"] += levels_count
    
    # Lưu dữ liệu vào file
    save_all()

    # Tự động kiểm tra và trao Role
    roles_to_add = []
    for lv_milestone, role_id in LEVEL_ROLES.items():
        if levels[uid]["level"] >= lv_milestone:
            role = interaction.guild.get_role(role_id)
            if role and role not in interaction.user.roles:
                roles_to_add.append(role)
    
    if roles_to_add:
        try:
            await interaction.user.add_roles(*roles_to_add)
        except:
            pass

    await interaction.response.send_message(f"✅ Thành công! Bạn đã chi `{total_cost:,}` coins để lên thẳng cấp **{levels[uid]['level']}**.")
# --- VIEW XÁC NHẬN CHUYỂN TIỀN ---
# ================== 💸 HỆ THỐNG GIAO DỊCH VÀ XẾP HẠNG ==================

# ================== 💸 HỆ THỐNG GIAO DỊCH VÀ XẾP HẠNG ==================



# ================== 🎲 NHÓM 3: TRÒ CHƠI (10 Lệnh) ==================
@bot.tree.command(name="taixiu", description="Cá cược Tài Xỉu (Thuế 10%)")
@app_commands.choices(lua_chon=[
    app_commands.Choice(name="Tài", value="tài"),
    app_commands.Choice(name="Xỉu", value="xỉu"),
])
async def taixiu(interaction: discord.Interaction, lua_chon: app_commands.Choice[str], tien_cuoc: int):
    uid = str(interaction.user.id)
    val = lua_chon.value

    # Lấy và chuẩn hóa dữ liệu
    user_econ = economy.get(uid, {"coins": 0, "diamonds": 0})
    if isinstance(user_econ, int): user_econ = {"coins": user_econ, "diamonds": 0}

    if tien_cuoc <= 0 or user_econ["coins"] < tien_cuoc:
        return await interaction.response.send_message("❌ Tiền cược không hợp lệ hoặc bạn không đủ coins!", ephemeral=True)

    # Trừ tiền cược
    user_econ["coins"] -= tien_cuoc
    
    import random
    dices = [random.randint(1, 6) for _ in range(3)]
    total = sum(dices)
    result = "tài" if total >= 11 else "xỉu"
    
    if val == result:
        # Thắng: Trả lại vốn + 90% lãi (10% thuế)
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
    
    import random
    num = random.randint(1, 100)
    win = (num % 2 == choices[lc])
    
    emb = discord.Embed(title="🔢 KẾT QUẢ CHẴN LẺ", color=0x9b59b6)
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
    
    import random
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

    # Định nghĩa giá vật phẩm
SHOP_ITEMS = {
    "x2_exp": {"name": "Buff X2 EXP (1 phút)", "price": 3000000, "multiplier": 2, "type": "exp"},
    "x4_exp": {"name": "Buff X4 EXP (1 phút)", "price": 6000000, "multiplier": 4, "type": "exp"},
    "x8_exp": {"name": "Buff X8 EXP (1 phút)", "price": 100000000, "multiplier": 8, "type": "exp"},
    "x16_exp": {"name": "Buff X16 EXP (1 phút)", "price": 16000000000000, "multiplier": 16, "type": "exp"},
    "x2_coin": {"name": "Buff X2 Tiền (1 phút)", "price": 5000000, "multiplier": 2, "type": "coin"},
    "x4_coin": {"name": "Buff X4 Tiền (1 phút)", "price": 10000000, "multiplier": 4, "type": "coin"},
    "x8_coin": {"name": "Buff X8 Tiền (1 phút)", "price": 200000000, "multiplier": 8, "type": "coin"},
    "x16_coin": {"name": "Buff X16 Tiền (1 phút)", "price": 25000000000000, "multiplier": 16, "type": "coin"}
}
SHOP_ITEMS.update({
    "role_vip1": {
        "name": "Role VIP 1",
        "price": 1000,
        "type": "role",
        "currency": "diamond",
        "role_id": 1496152438548336781
    },
    "role_vip2": {
        "name": "Role VIP 2",
        "price": 6000,
        "type": "role",
        "currency": "diamond",
        "role_id": 1496154307521941688
    },
    "role_vip3": {
        "name": "Role VIP 3",
        "price": 12000,
        "type": "role",
        "currency": "diamond",
        "role_id": 1496154436332945559
    },
    "role_vip4": {
        "name": "Role VIP 4",
        "price": 24000,
        "type": "role",
        "currency": "diamond",
        "role_id": 1496154550955020459
    }
})
# Trong phần data của Shop
shop_items = {
    "ruong_luu_tru": {
        "name": "🎁 Rương lưu trữ",
        "price": 10000000,
        "limit": 10,
        "description": "Chứa tối đa 1,000,000 Coins. Giúp bảo vệ tài sản qua mùa mới!"
    }
}
class QuantitySelect(discord.ui.Select):
    def __init__(self, item_id, item_info):
        self.item_id = item_id
        self.item_info = item_info
        options = [discord.SelectOption(label=f"Số lượng: {i}", value=str(i)) for i in range(1, 25)]
        super().__init__(placeholder="Chọn số lượng muốn mua...", options=options)

    async def callback(self, interaction: discord.Interaction):
        quantity = int(self.values[0])
        total_price = self.item_info['price'] * quantity
        
        view = ConfirmPurchase(self.item_id, quantity, total_price, self.item_info['name'])
        embed = discord.Embed(title="🛒 XÁC NHẬN THANH TOÁN", color=0xf1c40f)
        embed.description = f"Vật phẩm: **{self.item_info['name']}**\nSố lượng: **{quantity}**\nTổng tiền: **{total_price:,} coins**"
        
        await interaction.response.edit_message(embed=embed, view=view)

class ConfirmPurchase(discord.ui.View):
    def __init__(self, item_id, qty, price, name):
        super().__init__(timeout=30)
        self.item_id, self.qty, self.price, self.name = item_id, qty, price, name

    @discord.ui.button(label="Xác nhận mua", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        global economy, active_buffs
        uid = str(interaction.user.id)
        
        if economy.get(uid, 0) < self.price:
            return await interaction.response.edit_message(content="❌ Bạn không đủ tiền!", embed=None, view=None)

        # Trừ tiền
        economy[uid] -= self.price
        
        # Tính thời gian buff (số phút mua * 60 giây)
        duration = self.qty * 60
        current_time = time.time()
        
        if uid not in active_buffs: active_buffs[uid] = {}
        
        # Nếu đang có buff cũ thì cộng dồn thời gian, nếu không thì tính từ hiện tại
        old_expire = active_buffs[uid].get(self.item_id, 0)
        start_from = max(old_expire, current_time)
        active_buffs[uid][self.item_id] = start_from + duration
        
        save_all()
        await interaction.response.edit_message(content=f"✅ Mua thành công **{self.qty}** phút **{self.name}**!", embed=None, view=None)
       
    @discord.ui.button(label="Xác nhận mua", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        global economy
        uid = str(interaction.user.id)
        item_info = SHOP_ITEMS.get(self.item_id)
        
        # 1. Kiểm tra ví Kim cương (Vì Role VIP bán bằng Kim cương)
        user_diamonds = economy.get(uid, {}).get("diamonds", 0)
        if user_diamonds < self.price:
            return await interaction.response.edit_message(content="❌ Bạn không đủ Kim cương để làm VIP!", embed=None, view=None)

        # 2. Xử lý cấp Role nếu vật phẩm là loại 'role'
        if item_info.get("type") == "role":
            role_id = item_info.get("role_id")
            role = interaction.guild.get_role(role_id)
            
            if role in interaction.user.roles:
                return await interaction.response.edit_message(content="✨ Bạn đã sở hữu Role này rồi!", embed=None, view=None)
            
            try:
                await interaction.user.add_roles(role)
            except discord.Forbidden:
                return await interaction.response.edit_message(content="❌ Bot không đủ quyền để cấp Role (Hãy kiểm tra thứ tự Role của Bot)!", embed=None, view=None)

        # 3. Trừ tiền và lưu dữ liệu
        economy[uid]["diamonds"] -= self.price
        save_all()
        
        await interaction.response.edit_message(content=f"👑 Chúc mừng! Bạn đã trở thành **{self.name}**!", embed=None, view=None)

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    async def open_quantity_select(self, interaction, item_id):
        view = discord.ui.View()
        view.add_item(QuantitySelect(item_id, SHOP_ITEMS[item_id]))
        await interaction.response.edit_message(view=view)

    # --- HÀNG 0: BUFF EXP ---
    @discord.ui.button(label="X2 EXP", style=discord.ButtonStyle.primary, row=0)
    async def buy_x2_exp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_quantity_select(interaction, "x2_exp")

    @discord.ui.button(label="X4 EXP", style=discord.ButtonStyle.primary, row=0)
    async def buy_x4_exp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_quantity_select(interaction, "x4_exp")

    @discord.ui.button(label="X8 EXP", style=discord.ButtonStyle.primary, row=0)
    async def buy_x8_exp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_quantity_select(interaction, "x8_exp")

    @discord.ui.button(label="X16 EXP", style=discord.ButtonStyle.primary, row=0)
    async def buy_x16_exp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_quantity_select(interaction, "x16_exp")

    # --- HÀNG 1: BUFF TIỀN ---
    @discord.ui.button(label="X2 Tiền(Bảo trì)", style=discord.ButtonStyle.success, row=1)
    async def buy_x2_coin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_quantity_select(interaction, "x2_coin")

    @discord.ui.button(label="X4 Tiền(Bảo trì)", style=discord.ButtonStyle.success, row=1)
    async def buy_x4_coin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_quantity_select(interaction, "x4_coin")

    @discord.ui.button(label="X8 Tiền(Bảo trì)", style=discord.ButtonStyle.success, row=1)
    async def buy_x8_coin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_quantity_select(interaction, "x8_coin")

    @discord.ui.button(label="X16 Tiền(Bảo trì)", style=discord.ButtonStyle.success, row=1)
    async def buy_x16_coin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_quantity_select(interaction, "x16_coin")
    
    async def open_vip_confirm(self, interaction, item_id):
        item_info = SHOP_ITEMS[item_id]
        # Role mua 1 lần nên mặc định số lượng là 1
        view = ConfirmPurchase(item_id, 1, item_info['price'], item_info['name'])
        
        embed = discord.Embed(title="👑 XÁC NHẬN MUA ROLE VIP", color=0xffd700)
        embed.description = (
            f"Bạn có chắc muốn mua **{item_info['name']}** không?\n\n"
            f"💰 Giá: **{item_info['price']:,} Kim cương**\n"
            f"✨ Quyền lợi: Nhận role vĩnh viễn trong server."
        )
        await interaction.response.edit_message(embed=embed, view=view)

    # --- CÁC NÚT MUA ROLE VIP (Hàng 2) ---
    @discord.ui.button(label="VIP 1", style=discord.ButtonStyle.danger, row=2)
    async def buy_vip1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_vip_confirm(interaction, "role_vip1")

    @discord.ui.button(label="VIP 2", style=discord.ButtonStyle.danger, row=2)
    async def buy_vip2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_vip_confirm(interaction, "role_vip2")

    @discord.ui.button(label="VIP 3", style=discord.ButtonStyle.danger, row=2)
    async def buy_vip3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_vip_confirm(interaction, "role_vip3")

    @discord.ui.button(label="VIP 4", style=discord.ButtonStyle.danger, row=2)
    async def buy_vip4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_vip_confirm(interaction, "role_vip4")

    @discord.ui.button(label="Mua Toàn Bộ Rương (10M/cái)", style=discord.ButtonStyle.danger, row=3)
    async def buy_ruong_luu_tru(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        gia_moi_ruong = 10000000 

        # 1. Load data
        with open('economy.json', 'r', encoding='utf-8') as f: eco = json.load(f)
        with open('inventory.json', 'r', encoding='utf-8') as f: inv = json.load(f)

        # 2. Tính toán số lượng có thể mua
        inv_user = inv.get(user_id, {})
        sl_trong = inv_user.get("ruong_luu_tru", 0)
        sl_da_nap = len(inv_user.get("ruong_da_nap", []))
        tong_hien_tai = sl_trong + sl_da_nap
        
        so_luong_can_mua_de_full = 10 - tong_hien_tai

        if so_luong_can_mua_de_full <= 0:
            return await interaction.response.send_message("⚠️ Bạn đã sở hữu tối đa 10 rương rồi!", ephemeral=True)

        user_coins = eco.get(user_id, {}).get("coins", 0)
        
        # Tính xem với số tiền hiện có mua được tối đa bao nhiêu cái
        so_luong_mua_duoc_theo_tien = user_coins // gia_moi_ruong
        so_luong_thuc_te = min(so_luong_can_mua_de_full, so_luong_mua_duoc_theo_tien)

        if so_luong_thuc_te <= 0:
            return await interaction.response.send_message(f"❌ Bạn không đủ tiền để mua thêm rương nào (Cần {gia_moi_ruong:,} Coins)!", ephemeral=True)

        # 3. Thực hiện trừ tiền và cộng rương
        tong_bill = so_luong_thuc_te * gia_moi_ruong
        eco[user_id]["coins"] -= tong_bill
        inv[user_id]["ruong_luu_tru"] = sl_trong + so_luong_thuc_te

        # 4. GHI CẢ 2 FILE (Fix lỗi không mất tiền)
        with open('economy.json', 'w', encoding='utf-8') as f:
            json.dump(eco, f, indent=4)
        with open('inventory.json', 'w', encoding='utf-8') as f:
            json.dump(inv, f, indent=4)

        await interaction.response.send_message(
            f"✅ **Giao dịch thành công!**\n"
            f"- Đã mua: **{so_luong_thuc_te}** rương\n"
            f"- Tổng chi: **{tong_bill:,}** Coins\n"
            f"- Hiện có: **{inv[user_id]['ruong_luu_tru']}** rương trống.", 
            ephemeral=True
        )

@bot.tree.command(name="shop", description="Cửa hàng vật phẩm bổ trợ")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🏪 CỬA HÀNG VẬT PHẨM", color=0xe91e63)
    embed.add_field(name="⚡ Buff X2 EXP", value="Giá: `3,000,000 / phút`", inline=False)
    embed.add_field(name="🔥 Buff X4 EXP", value="Giá: `6,000,000 / phút`", inline=False)
    embed.add_field(name="🔥 Buff X8 EXP", value="Giá: `100,000,000 / phút`", inline=False)
    embed.add_field(name="🔥 Buff X16 EXP", value="Giá: `16,000,000,000,000 / phút`", inline=False)
    embed.add_field(name="Role Vip 1!", value="Giá: `500💎`", inline=False)
    embed.add_field(name="Role Vip 2!", value="Giá: `1500💎`", inline=False)
    embed.add_field(name="Role Vip 3!", value="Giá: `5000💎`", inline=False)
    embed.add_field(name="Role Vip 4!", value="Giá: `12000💎`", inline=False)
    embed.set_footer(text="Bấm nút bên dưới để chọn vật phẩm")
    embed.set_footer(text="**Hiện tại chức năng mua buff money vẫn đang test, chưa có giá chính thức , bạn cố tình ấn vào sẽ bị trừ tiền, bên phía admin sẽ ko giải quyết. Cảm ơn!**")
    await interaction.response.send_message(embed=embed, view=ShopView())

@bot.tree.command(name="buff", description="Xem các vật phẩm đang có hiệu lực.")
async def buff(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    if uid not in active_buffs or not active_buffs[uid]:
        return await interaction.response.send_message("Bạn hiện không có buff nào đang hoạt động.")

    embed = discord.Embed(title="✨ THÔNG TIN BUFF HIỆN TẠI", color=0x00ff00)
    current_time = time.time()
    has_active = False

    for item_id, expire_time in list(active_buffs[uid].items()):
        if expire_time > current_time:
            has_active = True
            remaining = int(expire_time - current_time)
            mins, secs = divmod(remaining, 60)
            name = SHOP_ITEMS[item_id]['name']
            embed.add_field(name=name, value=f"⏳ Còn lại: `{mins}m {secs}s`", inline=False)
        else:
            # Xóa buff đã hết hạn
            del active_buffs[uid][item_id]

    if not has_active:
        return await interaction.response.send_message("Các vật phẩm của bạn đã hết hạn.")
    
    save_all()
    await interaction.response.send_message(embed=embed)


# Giả sử đây là class bot của bạn
@bot.tree.command(name="phanhoi", description="Gửi phản hồi trực tiếp vào DM người dùng")
@app_commands.describe(ma_phieu="Dán mã ID tin nhắn báo cáo vào đây", ghi_chu="Nội dung bạn muốn nhắn cho người dùng")
async def phanhoi(interaction: discord.Interaction, ma_phieu: str, ghi_chu: str):
    await interaction.response.defer(ephemeral=True)
    
    try:
        # 1. Lấy ID tin nhắn (xử lý nếu bạn có nhập dấu #)
        clean_id = int(ma_phieu.replace("#", ""))
        
        # 2. Tìm tin nhắn đó trong kênh Admin
        channel = bot.get_channel(REPORT_CHANNEL_ID)
        msg = await channel.fetch_message(clean_id)
        
        # 3. Lấy thông tin người gửi từ Embed cũ
        # Mình lấy ID người dùng đã lưu ở Footer của tin nhắn báo cáo
        user_id = int(msg.embeds[0].footer.text.split(": ")[1])
        user = await bot.fetch_user(user_id)
        
        # Lấy ngày gửi từ Embed cũ (nếu có)
        ngay_gui = msg.embeds[0].fields[1].value.replace("`", "") 

        # 4. Tạo Embed phản hồi cực đẹp gửi cho NGƯỜI DÙNG
        from datetime import datetime
        embed_gui_user = discord.Embed(
            title="📝 ĐƠN BÁO CÁO / HỖ TRỢ",
            color=discord.Color.from_rgb(46, 204, 113) # Màu xanh lá chuyên nghiệp
        )
        embed_gui_user.add_field(name="📅 Ngày gửi đơn", value=ngay_gui, inline=True)
        embed_gui_user.add_field(name="⏱️ Thời gian xử lý", value=datetime.now().strftime("%d/%m/%Y %H:%M"), inline=True)
        embed_gui_user.add_field(name="🟢 Trạng thái", value="Đã phản hồi", inline=False)
        
        # Nội dung gốc (lấy từ Embed báo cáo)
        noi_dung_goc = msg.embeds[0].fields[3].value 
        embed_gui_user.add_field(name="📄 Nội dung báo cáo", value=f"```{noi_dung_goc}```", inline=False)
        
        # Nội dung Admin ghi chú
        embed_gui_user.add_field(name="💬 Nội dung phản hồi", value=f"```{ghi_chu}```", inline=False)
        
        embed_gui_user.set_footer(text=f"Người phản hồi: {interaction.user.name}")

        # 5. GỬI DM CHO NGƯỜI DÙNG
        await user.send(embed=embed_gui_user)
        
        # 6. Thông báo cho Admin biết đã gửi thành công
        await interaction.followup.send(f"✅ Đã gửi phản hồi thành công đến <@{user_id}>", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi: {e}. Hãy chắc chắn mã phiếu đúng và người dùng không khóa DM.", ephemeral=True)

@bot.tree.command(name="avatar")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    await interaction.response.send_message(target.display_avatar.url)

@bot.tree.command(name="ping", description="Check ping server")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Tôi là quản lí sever. Version 1.23.53 `{round(bot.latency * 1000)}ms`")
    
class ChonRuongNapView(discord.ui.View):
    def __init__(self, user_id, inventory_data, economy_data):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.inv = inventory_data
        self.eco = economy_data
        self.sl_trong = self.inv.get(user_id, {}).get("ruong_luu_tru", 0)

        # 1. Tạo các nút nạp từng rương (Hàng 1, 2)
        for i in range(self.sl_trong):
            btn = discord.ui.Button(
                label=f"Nạp Rương {i+1}", 
                style=discord.ButtonStyle.primary,
                custom_id=f"nap_don_{i}"
            )
            btn.callback = self.create_nap_callback(i)
            self.add_item(btn)

        # 2. Tạo nút "NẠP TẤT CẢ" (Màu xanh lá - Success)
        if self.sl_trong > 1:
            btn_all = discord.ui.Button(
                label="🚀 NẠP TẤT CẢ RƯƠNG TRỐNG", 
                style=discord.ButtonStyle.success,
                row=4 # Đặt ở hàng cuối cùng cho nổi bật
            )
            btn_all.callback = self.nap_tat_ca_callback
            self.add_item(btn_all)

    def create_nap_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if self.eco[self.user_id]["coins"] < 1000000:
                return await interaction.response.send_message("❌ Bạn không đủ 1,000,000 Coins!", ephemeral=True)

            self.eco[self.user_id]["coins"] -= 1000000
            self.inv[self.user_id]["ruong_luu_tru"] -= 1
            self.inv[self.user_id].setdefault("ruong_da_nap", []).append(1000000)

            self.save_data()
            await interaction.response.send_message(f"✅ Đã nạp 1M Coins vào 1 rương!", ephemeral=True)
            self.stop()
        return callback

    async def nap_tat_ca_callback(self, interaction: discord.Interaction):
        user_coins = self.eco[self.user_id].get("coins", 0)
        
        # Tính số rương có thể nạp (dựa trên số tiền đang có và số rương trống)
        so_ruong_co_the_nap_theo_tien = user_coins // 1000000
        so_ruong_thuc_te_nap = min(self.sl_trong, so_ruong_co_the_nap_theo_tien)

        if so_ruong_thuc_te_nap <= 0:
            return await interaction.response.send_message("❌ Bạn không đủ tiền để nạp bất kỳ rương nào!", ephemeral=True)

        tong_tien_nap = so_ruong_thuc_te_nap * 1000000
        
        # Thực hiện trừ tiền và chuyển trạng thái rương
        self.eco[self.user_id]["coins"] -= tong_tien_nap
        self.inv[self.user_id]["ruong_luu_tru"] -= so_ruong_thuc_te_nap
        
        for _ in range(so_ruong_thuc_te_nap):
            self.inv[self.user_id].setdefault("ruong_da_nap", []).append(1000000)

        self.save_data()
        await interaction.response.send_message(
            f"🚀 **Nạp tất cả thành công!**\n"
            f"- Đã nạp: **{so_ruong_thuc_te_nap}** rương\n"
            f"- Tổng tiền khấu trừ: **{tong_tien_nap:,}** Coins", 
            ephemeral=True
        )
        self.stop()

    def save_data(self):
        with open('economy.json', 'w', encoding='utf-8') as f:
            json.dump(self.eco, f, indent=4)
        with open('inventory.json', 'w', encoding='utf-8') as f:
            json.dump(self.inv, f, indent=4)

@bot.tree.command(name="themtien", description="Nạp tiền vào rương lưu trữ")
async def themtien(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    with open('economy.json', 'r', encoding='utf-8') as f: eco = json.load(f)
    with open('inventory.json', 'r', encoding='utf-8') as f: inv = json.load(f)

    inv_user = inv.get(user_id, {})
    sl_trong = inv_user.get("ruong_luu_tru", 0)

    if sl_trong <= 0:
        return await interaction.response.send_message("⚠️ Bạn không còn rương trống nào! Hãy mua tại `/shop`.", ephemeral=True)

    embed = discord.Embed(
        title="📥 HỆ THỐNG NẠP TIỀN RƯƠNG",
        description=f"Bạn đang có **{sl_trong}** rương trống.\nBạn muốn nạp lẻ từng rương hay nạp tất cả?",
        color=discord.Color.blue()
    )
    
    view = ChonRuongNapView(user_id, inv, eco)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class MoRuongView(discord.ui.View):
    def __init__(self, user_id, inv, eco):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.inv = inv
        self.eco = eco
        self.ruong_da_nap = self.inv.get(user_id, {}).get("ruong_da_nap", [])

    @discord.ui.button(label="🔓 MỞ TẤT CẢ RƯƠNG", style=discord.ButtonStyle.danger, emoji="💰")
    async def open_all_ruong(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = self.user_id
        
        # 1. Kiểm tra xem có rương nào để mở không
        if not self.ruong_da_nap:
            return await interaction.response.send_message("⚠️ Bạn không có tiền trong rương để rút!", ephemeral=True)

        # 2. Tính tổng tiền trong tất cả các rương
        tong_tien_rut = sum(self.ruong_da_nap)
        so_luong_ruong_vừa_mo = len(self.ruong_da_nap)

        # 3. Cập nhật dữ liệu
        # Cộng tiền vào ví
        self.eco[user_id]["coins"] += tong_tien_rut
        
        # Chuyển số rương đã mở về lại rương trống (ruong_luu_tru)
        self.inv[user_id]["ruong_luu_tru"] = self.inv[user_id].get("ruong_luu_tru", 0) + so_luong_ruong_vừa_mo
        
        # Xóa danh sách rương đã nạp
        self.inv[user_id]["ruong_da_nap"] = []

        # 4. GHI FILE (Cực kỳ quan trọng để fix lỗi)
        with open('economy.json', 'w', encoding='utf-8') as f:
            json.dump(self.eco, f, indent=4)
        with open('inventory.json', 'w', encoding='utf-8') as f:
            json.dump(self.inv, f, indent=4)

        # 5. Phản hồi
        embed = discord.Embed(
            title="✅ RÚT TIỀN THÀNH CÔNG",
            description=f"Bạn đã mở **{so_luong_ruong_vừa_mo}** rương và nhận lại **{tong_tien_rut:,}** Coins!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()

# Lệnh Slash
@bot.tree.command(name="moruong", description="Xem và quản lý tiền trong rương")
async def moruong(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    # --- Load Data (Giống cách mình làm ở trên) ---
    with open('economy.json', 'r') as f: eco = json.load(f)
    with open('inventory.json', 'r') as f: inv = json.load(f)
    
    ruong_list = inv.get(user_id, {}).get("ruong_da_nap", [])
    
    if not ruong_list:
        return await interaction.response.send_message("📭 Bạn không có rương nào đã nạp tiền!", ephemeral=True)

    total_money = sum(ruong_list)
    
    embed = discord.Embed(title="🎁 KÉT SẮT CÁ NHÂN", color=discord.Color.gold())
    embed.add_field(name="💰 Tổng tiền trong rương:", value=f"**{total_money:,} Coins**", inline=False)
    
    desc = ""
    for i, m in enumerate(ruong_list):
        desc += f"📦 **Rương {i+1}:** `{m:,}` Coins\n"
    embed.description = desc
    
    view = MoRuongView(user_id, inv, eco)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)    

import discord
from discord import app_commands

# LỆNH: /lock_channel
@bot.tree.command(name="lock_channel", description="🔒 Ẩn kênh hoàn toàn với @everyone và chỉ cho phép role Member trở lên nhìn thấy")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock_channel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    channel = interaction.channel
    
    everyone_role = guild.default_role
    member_role = discord.utils.get(guild.roles, name="Member") # Sửa lại tên role của mày ở đây nếu cần
    
    if not member_role:
        return await interaction.followup.send("❌ Không tìm thấy role nào tên là `Member` trong Server!", ephemeral=True)
    
    try:
        # Cấu hình quyền đè lên kênh (Overwrite permissions)
        # 1. @everyone: Không được phép xem kênh (view_channel=False) -> Kênh sẽ biến mất khỏi màn hình của họ
        await channel.set_permissions(everyone_role, 
            view_channel=False
        )
        
        # 2. Member: Được phép xem kênh và gửi tin nhắn bình thường
        await channel.set_permissions(member_role, 
            view_channel=True, 
            send_messages=True
        )
        
        # Gửi thông báo công khai trong kênh cho những người còn ở lại (Member trở lên) nhìn thấy
        embed = discord.Embed(
            title="🔒 KÊNH ĐÃ ẨN KHỎI @EVERYONE",
            description=f"Kênh {channel.mention} đã được ẩn hoàn toàn đối với thành viên mới/@everyone.\n\n👁️ Hiện tại chỉ có những ai sở hữu role **{member_role.mention}** trở lên mới có thể nhìn thấy và chat ở đây.",
            color=discord.Color.red()
        )
        await channel.send(embed=embed)
        await interaction.followup.send("✅ Đã ẩn kênh thành công với @everyone và giữ lại cho Member!", ephemeral=True)

    except discord.Forbidden:
        await interaction.followup.send("❌ Bot thiếu quyền `Manage Channels` hoặc role của Bot đang bị xếp dưới role Member!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi: {str(e)}", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} đã online với đầy đủ 60+ lệnh!")
@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    # Kiểm tra xem có sự thay đổi về Role hay không
    if len(before.roles) != len(after.roles):
        # Lấy các role vừa được thêm vào
        role_moi_nhan = set(after.roles) - set(before.roles)
        
        if role_moi_nhan:
            # Lấy role vừa nhận (ưu tiên role cao nhất nếu nhận nhiều role)
            role_vua_them = list(role_moi_nhan)[-1]
            
            # Bỏ qua role mặc định @everyone
            if role_vua_them.is_default():
                return
                
            ten_goc = after.global_name or after.name
            biet_danh_moi = f"{role_vua_them.name} | {ten_goc}"
            
            if len(biet_danh_moi) > 32:
                biet_danh_moi = biet_danh_moi[:32]
                
            try:
                await after.edit(nick=biet_danh_moi)
            except discord.Forbidden:
                pass # Bot không đủ quyền can thiệp vào user này
import discord
from discord import app_commands

@bot.tree.command(name="rename_role_members", description="🛠️ Đổi biệt danh tất cả thành viên có role theo cú pháp: [Tên Role | Tên]")
@app_commands.checks.has_permissions(manage_nicknames=True) # Yêu cầu quyền Quản lý biệt danh
@app_commands.describe(role="Chọn role cần đổi biệt danh cho các thành viên sở hữu")
async def rename_role_members(interaction: discord.Interaction, role: discord.Role):
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    thanh_cong = 0
    that_bai = 0
    
    # Lặp qua tất cả thành viên đang có Role này
    for member in role.members:
        # Lấy tên hiển thị gốc (bỏ phần biệt danh cũ nếu có)
        ten_goc = member.global_name or member.name
        
        # Tạo biệt danh mới theo cú pháp yêu cầu
        biet_danh_moi = f"{role.name} | {ten_goc}"
        
        # Giới hạn độ dài biệt danh của Discord tối đa là 32 ký tự
        if len(biet_danh_moi) > 32:
            biet_danh_moi = biet_danh_moi[:32]
            
        try:
            # Đổi biệt danh
            await member.edit(nick=biet_danh_moi)
            thanh_cong += 1
        except discord.Forbidden:
            # Lỗi không đổi được (thường là do mem đó là Chủ Server hoặc có Role cao hơn Bot)
            that_bai += 1
        except Exception:
            that_bai += 1

    await interaction.followup.send(
        f"✅ **Hoàn tất đổi biệt danh cho Role {role.mention}!**\n"
        f"• Đã đổi thành công: **{thanh_cong}** thành viên.\n"
        f"• Thất bại: **{that_bai}** (Thường do Chủ Server hoặc người có quyền cao hơn Bot).",
        ephemeral=True
    )

@rename_role_members.error
async def rename_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Mày thiếu quyền `Manage Nicknames` (Quản lý biệt danh) để xài lệnh này!", ephemeral=True)


# LỆNH: /invite
@bot.tree.command(name="link", description="🔗 Lấy link mời bot tham gia vào server khác")
async def invite(interaction: discord.Interaction):
    # Lấy ID của bot từ client
    bot_id = bot.user.id
    
    # Tạo link invite với quyền Administrator (permissions=8)
    # Đây là quyền chuẩn nhất giúp bot không bị lỗi thiếu quyền khi chạy lệnh
    invite_link = f"https://discord.com/api/oauth2/authorize?client_id={bot_id}&permissions=8&scope=bot%20applications.commands"
    
    embed = discord.Embed(
        title="🤖 MỜI BOT VÀO SERVER CỦA BẠN",
        description=(
            f"Cảm ơn mày đã tin tưởng và muốn đưa tôi về nhà mới! 💖\n\n"
            f"👉 **[Nhấp vào đây để thêm Bot]({invite_link})**\n\n"
            f"*Lưu ý: Bạn cần có quyền `Quản lý Server` (Manage Server) ở server đích để thêm được bot.*"
        ),
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text=f"Yêu cầu bởi {interaction.user.name}")
    
    # Gửi ẩn (ephemeral=True) để tránh spam kênh chat, hoặc bỏ True nếu muốn ai cũng thấy
    await interaction.response.send_message(embed=embed, ephemeral=True)



# ==========================================
# 🟢 HÀM KÍCH HOẠT DUY NHẤT
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} đã online thành công!")


import os

# Lấy token từ biến môi trường
TOKEN = os.getenv("DISCORD_TOKEN")

bot.run(TOKEN)